import re


def normalize_token(value: str, pattern: str | re.Pattern | None = None) -> str:
    """Normalize an identifier-like token by removing separators/whitespace and uppercasing.

    Args:
        value: Raw token value
        pattern: Optional regex or pattern string specifying characters to strip.
                 Defaults to a cross-country-safe set: whitespace, dash, dot, underscore,
                 slash and backslash, comma.

    Returns:
        Normalized token string
    """
    compiled = re.compile(pattern) if isinstance(pattern, str) else (
        pattern if pattern is not None else re.compile(r"[ \t\r\n\-._/,\\]")
    )
    return compiled.sub("", value).upper()


def mrz_check_digit(data: str) -> int:
    """Compute MRZ check digit per ICAO 9303 (weights 7-3-1). Returns -1 on invalid char.

    This is useful for passport/identity document checks where the last digit is a checksum.
    """
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(data):
        if ch.isdigit():
            val = ord(ch) - 48
        elif 'A' <= ch <= 'Z':
            val = ord(ch) - 55
        elif ch == '<':
            val = 0
        else:
            return -1
        total += val * weights[i % 3]
    return total % 10


def iso_7064_mod_11_10(full_digits: str) -> bool:
    """Validate a numeric string using ISO/IEC 7064, MOD 11,10 algorithm.

    Returns True if the final check digit matches the computed value.
    """
    if not (len(full_digits) == 11 and full_digits.isdigit()):
        return False
    p = 10
    for d in full_digits[:-1]:
        s = (int(d) + p) % 10
        if s == 0:
            s = 10
        p = (2 * s) % 11
    return ((11 - p) % 10) == int(full_digits[-1])

def is_valid_numeric_field(field_value):
    """
    Check if the input field contains any alphabetic characters.

    Args:
    - field_value (str): The value to check.

    Returns:
    - bool: True if it contains any alphabetic characters, False otherwise.
    """
    return bool(re.search(r"[A-Za-z]+", field_value))


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

def is_not_part_of_decimal(text, start_index, end_index):
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