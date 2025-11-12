import re
import traceback
from itertools import combinations
from stdnum.us import ssn
from dateutil.parser import ParserError, parse
from classifier.log import get_logger
from luhnchecker.luhn import Luhn
from stdnum.us import itin

logger = get_logger(__name__)

# Define entity labels globally
ENTITY_LABELS = {
    "iban": "iban",
    "ssn": "ssn",
    "passport_number": "passport_number",
    "passport": "passport_number",
    "driver_license_number": "driver_license_number",
    "credit_card_number": "credit_card_number",
    "name": "name",
    "company_name": "company",
    "street_address": "street_address",
    "email": "email",
    "phone_number": "phone_number",
    "date_of_birth": "date_of_birth",
    "bank_routing_number": "bank_routing_number",
    "bank_account_number": "bank_account_number",
    "swift_bic_code": "swift_bic_code",
    "api_key": "api_key",
    "private_keys": "private_keys",
    "bank_name": "company",
    "hospital_name": "company",
    "company_address": "street_address",
    "us-itin": "itin",
    "itin": "itin",
    "ip_address": "ip_address",
    "bban": "bban",
    "address": "street_address",
    "treating_physician": "name",
    "surgeon": "name",
    "contact_number": "phone_number",
    "ipv6": "ip_address",
    "ipv4": "ip_address",
    "provider_email": "email",
    "reference_contact_number": "phone_number",
    "residential_address": "street_address",
    "reference_name": "name",
    "contact_telephone_number": "phone_number",
    "contact_name": "name",
    "contact_ipv6_address": "ip_address",
    "person": "name",
    "us_ssn": "ssn",
    "us_passport": "passport_number",
    "us_driver_license": "driver_license_number",
    "email_address": "email",
    "llm_person": "name",
    "llm_organization": "company",
    "credit_card": "credit_card_number",
    "us_bank_number": "bank_account_number",
    "iban_code": "iban",
    "us_itin": "itin",
    "routing_number": "bank_routing_number",
    "swift_code": "swift_bic_code",
    "bban_code": "bban",
    "medical_record_number": "medical_record_number",
    "health_insurance_number": "health_insurance_number",
    "vehicle_vin": "vehicle_vin",
    "license_plate_number": "license_plate_number",
}


# Helper Functions

dob_regex = re.compile(
    r"(Birth|DOB|Birthdate|Born|D\.O\.B\.|DOB|"
    r"Geburtsdatum|Geburtstag|geboren\s+am|Geb\.\s*Datum|"
    r"Date\s+de\s+naissance|DDN|Né\(e\)\s+le|Date\s+de\s+n\.|"
    r"Fecha\s+de\s+nacimiento|F\.N\.|Nacimiento|Nacido\s+el|Fecha\s+nacimiento|Fecha\s+de\s+n\.|"
    r"Syntymäaika|Syntymäpäivä|Syntymä|Syntynyt|"
    r"Geboortedatum|Geboren\s+op|Geboorte|Geb\.\s*datum|"
    r"Födelsedatum|Född\s+den|Födelsedag|Född|F\.d\.)",
    re.IGNORECASE|re.MULTILINE
)

def is_overlapping(start, end, label, used_spans):
    """
    Check if the current match overlaps with any previously matched spans for a given label.

    Args:
    - start (int): The start position of the current match.
    - end (int): The end position of the current match.
    - label (str): The entity label of the current match.
    - used_spans (dict): Dictionary of used spans by label.

    Returns:
    - bool: True if the current match overlaps with any existing spans, False otherwise.
    """
    for s, e in used_spans[label]:
        if max(start, s) < min(end, e):
            return True
    return False


def generate_permutations(phrase):
    """
    Generate subsequences that preserve the word order from a given phrase.

    Args:
    - phrase (str): The input phrase to generate subsequences from.

    Returns:
    - list: List of subsequences in descending order of length.
    """
    words = phrase.split()
    subsequences = [
        " ".join(combo)
        for length in range(1, len(words) + 1)
        for combo in combinations(words, length)
    ]
    subsequences.sort(key=len, reverse=True)
    return subsequences


def is_valid_email(email):
    """
    Validate if the input is a proper email address.

    Args:
    - email (str): The email to validate.

    Returns:
    - bool: True if it's a valid email, False otherwise.
    """
    return "@" in email and "." in email


def is_valid_name(name):
    """
    Validate if the name has a length greater than 2.

    Args:
    - name (str): The name to validate.

    Returns:
    - bool: True if the name is valid, False otherwise.
    """
    return len(name) > 5 and sum(c.isdigit() for c in name) < 3


def is_valid_numeric_field(field_value):
    """
    Check if the input field contains any alphabetic characters.

    Args:
    - field_value (str): The value to check.

    Returns:
    - bool: True if it contains any alphabetic characters, False otherwise.
    """
    return bool(re.search(r"[A-Za-z]+", field_value))
    


def is_valid_length_for_entity(key_label, field_value):
    """
    Validate the length of numeric fields based on entity type (e.g., SSN, phone number).

    Args:
    - key_label (str): The label of the entity being checked.
    - field_value (str): The value to validate for length.

    Returns:
    - bool: True if the value has the correct length for the entity, False otherwise.
    """
    digit_value = re.sub(r"\D", "", field_value)
    if key_label.lower() == "ssn" :
        return len(digit_value) == 9 and  ssn.is_valid(field_value)
    elif key_label.lower() == "itin" :
        return len(digit_value) == 9 and itin.is_valid(field_value)
    elif key_label.lower() == "credit_card_number":
        return 12 <= len(digit_value) <= 19
    elif key_label.lower() == "phone_number":
        return 7 <= len(digit_value) <= 30
    elif key_label.lower() == "bank_account_number":
        return 6 <= len(digit_value) <= 15

    return True


def is_valid_date(date, text):
    """
    Validate if the input string is a valid date format.

    Args:
    - date (str): The date string to validate.

    Returns:
    - bool: True if the date is valid, False otherwise.
    """
    try:
        if len(date) < 8:
            return False
        if not bool(dob_regex.search(text)):
            return False

        parse(date)
        return True
    except ParserError:
        return False


def is_valid_ip(ip):
    """
    Validate if the input string is a valid IPv4 or IPv6 address.

    Args:
    - ip (str): The IP address string to validate.

    Returns:
    - bool: True if the IP is valid, False otherwise.
    """
    ipv4_pattern = re.compile(
        r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    ipv6_pattern = re.compile(
        r"^(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}$|^::(?:[a-fA-F0-9]{1,4}:){0,5}[a-fA-F0-9]{1,4}$|^(?:[a-fA-F0-9]{1,4}:){1,6}:$"
    )
    return bool(ipv4_pattern.match(ip) or ipv6_pattern.match(ip))


def count_alphabets(s):
    """
    Count the number of alphabetic characters in a string.

    Args:
    - s (str): The string to count alphabets in.

    Returns:
    - int: The number of alphabetic characters.
    """
    return sum(c.isalpha() for c in s)


def has_consecutive_decreasing_numbers(s: str, min_consecutive: int = 5) -> bool:
    """
    Check if the input string contains a sequence of at least `min_consecutive` digits
    where each digit is exactly one less than the previous (e.g., '98765').

    Args:
        s (str): The string to check.
        min_consecutive (int): The minimum length of consecutive decreasing digits. Default is 5.

    Returns:
        bool: True if such a sequence exists, False otherwise.
    """
    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) < min_consecutive:
        return False
    if len(digits) != len(s):
        return False

    count = 1
    for i in range(1, len(digits)):
        if digits[i] == digits[i - 1] - 1:
            count += 1
            if count >= min_consecutive:
                return True
        else:
            count = 1
    return False

def has_consecutive_repetitive_numbers(s: str, min_consecutive: int = 5) -> bool:
    """
    Check if the input string contains a sequence of at least `min_consecutive` identical digits.

    Args:
        s (str): The string to check.
        min_consecutive (int): The minimum length of consecutive identical digits. Default is 5.

    Returns:
        bool: True if such a sequence exists, False otherwise.
    """
    digits = [c for c in s if c.isdigit()]
    if len(digits) < min_consecutive:
        return False
    if len(digits) != len(s):
        return False

    count = 1
    for i in range(1, len(digits)):
        if digits[i] == digits[i - 1]:
            count += 1
            if count >= min_consecutive:
                return True
        else:
            count = 1
    return False


def has_consecutive_increasing_numbers(s: str, min_consecutive: int = 5) -> bool:
    """
    Check if the input string contains a sequence of at least `min_consecutive` digits
    where each digit is exactly one greater than the previous (e.g., '123456').

    Args:
        s (str): The string to check.
        min_consecutive (int): The minimum length of consecutive increasing digits. Default is 5.

    Returns:
        bool: True if such a sequence exists, False otherwise.
    """

    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) < min_consecutive:
        return False
    if len(digits) != len(s):
        return False

    count = 1
    for i in range(1, len(digits)):
        if digits[i] == digits[i - 1] + 1:
            count += 1
            if count >= min_consecutive:
                return True
        else:
            count = 1
    return False


# Validation Functions


def validate_extracted_data(label, extracted_text, text):
    """
    Validate extracted data based on its label.

    Args:
    - label (str): The entity label for the extracted data.
    - extracted_text (str): The text to validate.

    Returns:
    - bool: True if the extracted data is valid, False otherwise.
    """
    if label in ["IP_ADDRESS", "ip-address"]:
        return len(extracted_text) > 6
    if label == "email" and not is_valid_email(extracted_text):
        return False
    if label in ["name", "PERSON", "LLM_PERSON"] and not is_valid_name(extracted_text):
        return False
    if label == "date_of_birth" and not is_valid_date(extracted_text, text):
        return False
    if label.lower() in [
        "ssn",
        "credit_card_number",
        "itin",
        "phone_number",
        "bank_account_number",
        "us_bank_number",
        "us_bank_account_number",
        "credit_card",
        "us_ssn",
        "us_itin",

    ] and (
        is_valid_numeric_field(extracted_text)
        or not is_valid_length_for_entity(label, extracted_text) 
        or has_consecutive_increasing_numbers(extracted_text) 
        or has_consecutive_decreasing_numbers(extracted_text)
        or has_consecutive_repetitive_numbers(extracted_text)

    ):
        return False
    if label.lower() in [
        "iban",
        "bban",
        "driver_license_number",
        "passport_number",
        "us_driver_license",
        "us_passport",
        "iban_code",
    ] and (
        len(extracted_text) < 8
        or not re.search(r"\d", extracted_text)
        or (
            label in ["passport_number", "driver_license_number"]
            and count_alphabets(extracted_text) > 4
        )
    ):
        return False
    if label.lower() == "ip_address" and not is_valid_ip(extracted_text):
        return False
    if label.lower() == "api_key" and (
        len(extracted_text) < 8 or not re.search(r"\d", extracted_text)
    ):
        return False
    if label.lower() in ["iban_code", "bban_code", "passport_number", "us_passport", "driver_license_number", "us_driver_license", "routing_number"] and (has_consecutive_increasing_numbers(extracted_text) or has_consecutive_decreasing_numbers(extracted_text) or has_consecutive_repetitive_numbers(extracted_text)):   
        return False
    if label.lower() in ["itin", "us_itin"] :
        return itin.is_valid(extracted_text)
    if label.lower() in ["health_insurance_number", "medical_record_number", "license_plate_number"] :
        if not any(char.isdigit() for char in extracted_text):
            return False
    return True

def is_not_part_of_decimal(label, text, start_index, end_index):
    """
    Check if the number in the text (defined by start_index and end_index) 
    is not part of a larger decimal number.

    Args:
        text (str): The input text.
        start_index (int): The start index of the number.
        end_index (int): The end index of the number.

    Returns:
        bool: True if the number is not part of a decimal number, False otherwise.
    """
    
    try:
        if label.lower() in [
            "ssn",
            "credit_card",
            "itin",
            "phone_number",
            "us_bank_number",
            "us_driver_license",
            "us_ssn",
            "us_itin",
        ]:
            # Check character before the start index
            if start_index > 0:
                char_before = text[start_index - 1]
                if char_before.isdigit() or (char_before == '.' and text[start_index-2].isdigit()):
                    return False
            
            # Check character after the end index
            if end_index < len(text):
                char_after = text[end_index]
                if char_after.isdigit() or (char_after == '.' and text[end_index+1].isdigit()):
                    return False
        
        # If both conditions are satisfied, it's not part of a decimal
        return True
    except Exception as ex:
        return True
# Result Preparation Functions


def prepare_results(entity_patterns, text):
    """
    Match entity patterns to text and prepare the results.

    Args:
    - entity_patterns (dict): A dictionary of entity patterns.
    - text (str): The text in which to search for entity patterns.

    Returns:
    - list: A list of matched entities with start, end, and extracted text.
    """
    used_spans = {label: [] for label in ENTITY_LABELS.values()}
    results = []
    for key, patterns in entity_patterns.items():
        for pattern in patterns:
            combined_pattern = (
                "|".join(map(re.escape, generate_permutations(pattern)))
                if key == "name"
                else re.escape(str(pattern))
            )
            
            for match in re.finditer(
                combined_pattern, text, re.IGNORECASE | re.MULTILINE
            ):
                start, end = match.span()
                extracted_text = text[start:end]
                label = ENTITY_LABELS.get(key.lower(), "")

                if label and not is_overlapping(start, end, label, used_spans) and len(extracted_text) > 2:
                    if validate_extracted_data(label, extracted_text, text):
                        res_dict = {
                            "start": start,
                            "end": end,
                            "label": label,
                            "extracted_text": extracted_text.strip(),
                        }
                        results.append(res_dict)
                        used_spans[label].append((start, end))
    return results


# Main Function to Extract Entity Information


def extract_entity_info(entity_list, text):
    """
    Extract entity information by comparing entities from the list with the text.

    Args:
    - entity_list (list): List of entities (dictionaries) to match.
    - text (str): The input text to search for entities.

    Returns:
    - list: A list of matched entity information with start, end, label, and extracted text.
    """
    try:
        # Create patterns from entity list
        entity_patterns = {}
        labels = {key.lower(): value for key, value in ENTITY_LABELS.items()}

        for entity in entity_list:
            if isinstance(entity, dict):
                for key, value in entity.items():
                    key = key.lower()
                    if key in labels.keys():
                        if value and isinstance(value, str):
                            entity_patterns.setdefault(key, []).append(value)
                        elif value and isinstance(value, list):
                            for val in value:
                                entity_patterns.setdefault(key, []).append(
                                    val if isinstance(val, str) else list(val.values())
                                )

        # Prepare the results by matching patterns
        results = prepare_results(entity_patterns, text)
        return results

    except Exception:
        logger.error(traceback.format_exc())
        return []
