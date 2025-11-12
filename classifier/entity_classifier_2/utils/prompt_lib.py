# def get_entity_detection_prompt(text):
#     SYSTEM_PROMPT = """You are an advanced Named Entity Recognition (NER) extractor.
# Follow the definitions, rules, and examples exactly to extract entities from a sentence.
# You MUST:
# - Follow the output JSON schema exactly.
# - Preserve key names, casing, and order exactly as given.
# - Always include all keys, even if empty (use "").
# - Output valid JSON only, no commentary or extra text.
# """

#     ENTITY_DEFINITIONS = """
# Entity Types & Clues:
# - PERSON: Person name (short/full) with optional titles (Mr., Ms., Dr.).
# - STREET_ADDRESS: Full/partial street address; context: lives at, street, avenue.
# - COMPANY_NAME: Company/org name; context: works at, CEO of.
# - DATE_OF_BIRTH: DOB; context: born on, DOB, age.
# - EMAIL: Valid email; context: email, contact.
# - SSN: US Social Security Number; context: SSN, social security.
# - BBAN: Basic Bank Account Number; context: bank details, account number.
# - PHONE_NUMBER: Valid phone; context: phone, call.
# - API_KEY: 32–64 char key; context: API key, access token.
# - SWIFT_BIC_CODE: 8–11 char code; context: SWIFT code, BIC.
# - DRIVER_LICENSE_NUMBER: License ID; context: driver’s license, DL.
# - CREDIT_CARD_NUMBER: 16-digit card; context: credit card, card number.
# - IBAN: Up to 34-char bank account number; context: IBAN.
# - PASSPORT_NUMBER: Passport ID; context: passport, travel document.
# - BANK_ROUTING_NUMBER: 9-digit routing number; context: routing number.
# - BANK_ACCOUNT_NUMBER: Bank account number; context: account number.
# - ITIN: US tax ID; context: ITIN, taxpayer ID.
# """

#     EXTRACTION_RULES = """
# Extraction Rules:
# 1. Extract only if context keywords are present.
# 2. Do not hallucinate or guess entities.
# 3. Preserve original entity formatting exactly.
# 4. No splitting of multi-word entities (e.g., 'John Doe' stays together).
# """

#     RIGID_OUTPUT = """
# Output JSON Schema (keys & order MUST be exactly as shown):
# {"PERSON": [], "STREET_ADDRESS": [], "COMPANY_NAME": [], "DATE_OF_BIRTH": [], "EMAIL": [], "SSN": [], "BBAN": [], "PHONE_NUMBER": [], "API_KEY": [], "SWIFT_BIC_CODE": [], "DRIVER_LICENSE_NUMBER": [], "CREDIT_CARD_NUMBER": [], "IBAN": [], "PASSPORT_NUMBER": [], "BANK_ROUTING_NUMBER": [], "BANK_ACCOUNT_NUMBER": [], "ITIN": []}
# - Always output in this key order.
# - For empty categories, use "" inside the array.
# - Output JSON only, no text before or after.
# """

#     COT_INSTRUCTION = """
# Think step-by-step before output:
# Step 1: Identify potential entity spans from the sentence.
# Step 2: For each entity type, check for required keyword/context clues.
# Step 3: Keep only those matching the definition and context.
# Step 4: Fill the output JSON schema exactly as shown, with empty strings where no match.
# """

#     EXAMPLES = """
# Examples:
# Sentence: Mr. Jacob lives at 456 Oak Avenue, New York.
# Output: {"PERSON": ["Mr. Jacob"], "STREET_ADDRESS": ["456 Oak Avenue"], "COMPANY_NAME": [""], "DATE_OF_BIRTH": [""], "EMAIL": [""], "SSN": [""], "BBAN": [""], "PHONE_NUMBER": [""], "API_KEY": [""], "SWIFT_BIC_CODE": [""], "DRIVER_LICENSE_NUMBER": [""], "CREDIT_CARD_NUMBER": [""], "IBAN": [""], "PASSPORT_NUMBER": [""], "BANK_ROUTING_NUMBER": [""], "BANK_ACCOUNT_NUMBER": [""], "ITIN": [""]}

# Sentence: John Doe works at Acme Corp. His email is john.doe@example.com, and his SSN is 123-45-6789.
# Output: {"PERSON": ["John Doe"], "STREET_ADDRESS": [""], "COMPANY_NAME": ["Acme Corp"], "DATE_OF_BIRTH": [""], "EMAIL": ["john.doe@example.com"], "SSN": ["123-45-6789"], "BBAN": [""], "PHONE_NUMBER": [""], "API_KEY": [""], "SWIFT_BIC_CODE": [""], "DRIVER_LICENSE_NUMBER": [""], "CREDIT_CARD_NUMBER": [""], "IBAN": [""], "PASSPORT_NUMBER": [""], "BANK_ROUTING_NUMBER": [""], "BANK_ACCOUNT_NUMBER": [""], "ITIN": [""]}
# """

#     FINAL_INSTRUCTION = f"Sentence: {text}\nOutput:"

#     messages = [
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": ENTITY_DEFINITIONS + EXTRACTION_RULES + RIGID_OUTPUT + COT_INSTRUCTION + EXAMPLES + FINAL_INSTRUCTION},
#     ]
#     return messages

# """
# Named Entity Recognition (NER) Prompt Generator
# -----------------------------------------------
# This script builds a structured prompt for extracting entities
# using an LLM in a strict JSON format.
# """


def get_entity_detection_prompt(text: str):
    PROMPT = """# Named Entity Recognition (NER) Extractor

## Role
You are a highly accurate Named Entity Recognition (NER) extractor.

## Instructions

You MUST:
- Follow the output JSON schema exactly
- Preserve key names, casing, and order exactly as given
- Always include all keys, even if empty (use `""`)
- Extract ONLY if context keywords are present
- Do NOT guess or hallucinate entities
- Output valid JSON only; no commentary or extra text

## Entity Types & Context Clues

### Personal Information
- **PERSON**: Person name (short/full) with optional titles (Mr., Ms., Dr., Prof., etc.)
  - **Context indicators:** lives at, works with, referred as, called, named, known as, contact person, employee, customer, user, member
  - **Examples:** "John Doe", "Dr. Smith", "Mr. Johnson", "Sarah Wilson", "CEO Bob"
  - **Note:** Include titles when they appear with names, but don't extract titles alone

- **DATE_OF_BIRTH**: Date when a person was born. 
  - **Context indicators:** born on, DOB, date of birth, birthday, age, born, birth date, born in
  - **Examples:** "1990-05-15", "May 15, 1990", "15/05/1990", "born in 1990"
  - **Note:** Check the context carefully if only Date keyword is present, don't extract it as date of birth. If keywords like dob, date of birth etc are present, then extract it as date of birth.
  - **CRITICAL WARNING:** NEVER extract a date as DATE_OF_BIRTH unless you see explicit birth-related context. Common false positives to avoid:
    - "Date: 2024-01-15" → NOT a birth date
    - "Created on 1990-05-15" → NOT a birth date  
    - "Meeting date: May 15" → NOT a birth date
    - "Expiry date: 2025-12-31" → NOT a birth date
    - "Date of issue: 2020-03-20" → NOT a birth date
  - **ONLY extract when you see:** "born on", "DOB", "date of birth", "birthday", "born in [year]", "age [X] years old"

### Contact Information
- **EMAIL**: Valid email address
  - **Context indicators:** email, contact, send to, reach at, email address, contact email, email is
  - **Examples:** "john.doe@example.com", "contact@company.com", "user123@gmail.com"
  - **Note:** Must follow standard email format with @ symbol

- **PHONE_NUMBER**: Valid phone number in various formats
  - **Context indicators:** phone, call, contact, dial, phone number, mobile, cell, telephone, reach at
  - **Examples:** "+1-555-123-4567", "555-123-4567", "(555) 123-4567", "555.123.4567"
  - **Note:** Include country codes and various formatting styles

### Address Information
- **STREET_ADDRESS**: Full/partial street address
  - **Context indicators:** lives at, address, street, avenue, road, drive, lane, boulevard, located at, situated at
  - **Examples:** "123 Main Street", "456 Oak Avenue", "789 Pine Road", "100 Business Blvd"
  - **Note:** Can include street numbers, names, and types, but not full postal addresses

### Financial Information
- **SSN**: US Social Security Number (9 digits, may include hyphens)
  - **Context indicators:** SSN, social security, social security number, SSN is, taxpayer ID
  - **Examples:** "123-45-6789", "123456789", "SSN: 123-45-6789"
  - **Note:** Only US format, 9 digits total

- **CREDIT_CARD_NUMBER**: credit card number (may include spaces/dashes)
  - **Context indicators:** credit card, card number, card, payment card, visa, mastercard, amex
  - **Examples:** "1234-5678-9012-3456", "1234 5678 9012 3456", "1234567890123456"
  - **Note:** Various card types (Visa, MasterCard, AmEx, Discover)

- **BANK_ROUTING_NUMBER**: 9-digit US bank routing number
  - **Context indicators:** routing number, routing, ABA number, bank routing, routing code
  - **Examples:** "123456789", "123-456-789", "Routing: 123456789"
  - **Note:** US banks only, always 9 digits

- **BANK_ACCOUNT_NUMBER**: Bank account number (variable length)
  - **Context indicators:** account number, account, bank account, checking account, savings account
  - **Examples:** "1234567890", "ACC: 1234567890", "Account #1234567890"
  - **Note:** Length varies by bank, no specific format required

- **IBAN**: International Bank Account Number (up to 34 characters)
  - **Context indicators:** IBAN, international account, IBAN number, international bank account
  - **Examples:** "GB27GKPH81111877912857", "DE89370400440532013000"
  - **Note:** International format, country-specific lengths

- **SWIFT_BIC_CODE**: 8-11 character SWIFT/BIC code
  - **Context indicators:** SWIFT code, BIC, SWIFT/BIC, bank identifier, swift number
  - **Examples:** "BOFAUS3N", "DEUTDEFF", "SWIFT: BOFAUS3N"
  - **Note:** Bank identifier codes, international format

- **BBAN**: Basic Bank Account Number (variable length)
  - **Context indicators:** BBAN, basic account number, local account number, domestic account
  - **Examples:** "1234567890123456", "BBAN: 1234567890123456"
  - **Note:** Country-specific format, varies by region

- **ITIN**: Individual Taxpayer Identification Number (9 digits may include hyphens or spaces)
  - **Context indicators:** ITIN, taxpayer ID, individual taxpayer, ITIN number
  - **Examples:** "123-45-6789", "ITIN: 123-45-6789", "123456789"
  - **Note:** US tax ID for non-citizens, 9 digits

- **DRIVER_LICENSE_NUMBER**: Driver's license ID (format varies by state/country)
  - **Context indicators:** driver's license, DL, license number, driving license, license ID
  - **Examples:** "DL123456789", "123456789", "License: DL123456789"
  - **Note:** Format varies by jurisdiction

- **PASSPORT_NUMBER**: Passport ID (format varies by country)
  - **Context indicators:** passport, passport number, passport ID, travel document, passport #
  - **Examples:** "123456789", "AB1234567", "Passport: 123456789"
  - **Note:** Format varies by country, no standard length

### Business Information
- **COMPANY_NAME**: Company or organization name
  - **Context indicators:** works at, CEO of, employee of, company, corporation, organization, firm, business
  - **Examples:** "Acme Corp", "Microsoft Corporation", "Google LLC", "Small Business Inc"
  - **Note:** Include legal suffixes when present, but don't extract generic terms alone

- **API_KEY**: 32-64 character API key or access token
  - **Context indicators:** API key, access token, token, key, authentication, API token, secret key
  - **Examples:** "ghr_abcdef1234567890ghijklmnopqrstuvwxYZ", "sk-1234567890abcdef"
  - **Note:** Various formats including GitHub tokens, OpenAI keys, etc.

  ### Medical & Insurance Information (NEW)
- **MEDICAL_RECORD_NUMBER**: Medical Record Number (MRN) — patient record identifier used by hospitals/clinics
  - **Context indicators:** medical record number, MRN, patient ID, medical record, record #:, MRN:
  - **Examples:** "MRN: 12345678", "Medical Record Number 00012345", "Patient ID: 987654"
  - **Note:** MRN formats vary widely (digits, alphanumeric). Only extract when clear medical/patient context exists (e.g., patient, hospital, clinic, admission, discharge).

- **HEALTH_INSURANCE_NUMBER**: Health insurance / member / policy number (payer-issued identifier)
  - **Context indicators:** insurance number, policy number, member ID, subscriber ID, health insurance number, plan number, insurer, policy #
  - **Examples:** "Member ID: 1234567890", "Policy #: HIN-987654321", "Insurance number 0012345678"
  - **Note:** Formats vary by insurer and country. Only extract when insurance-related context is present (e.g., insurer name, policy, claim, coverage).

### Vehicle Information (NEW)
- **VIN**: Vehicle Identification Number (VIN) — 17-character vehicle identifier
  - **Context indicators:** VIN, vehicle identification number, chassis number, VIN:, vehicle, registration, odometer report
  - **Examples:** "VIN: 1HGCM82633A004352", "Vehicle Identification Number 1C4RJFBG0EC123456"
  - **Note:** Standard VINs are 17 characters (alphanumeric; letters I, O, Q are not used). Only extract when vehicle-related context indicators are present.

### License Plate Information
- **LICENSE_PLATE_NUMBER**: License plate number (format varies by country)
  - **Context indicators:** license plate, license plate number, license plate #, vehicle registration, vehicle license, license plate #, license plate number, license plate #
  - **Examples:** "AB1234567", "License Plate: AB1234567"
  - **Note:** 
    - Only extract LICENSE_PLATE_NUMBER if the text explicitly contains keywords like 
      "license plate", "registration plate", "plate number", or "vehicle registration".
    - Do NOT extract from general vehicle-related context such as "car", "vehicle", "fleet", "truck", "bus", etc.


## Extraction Rules

1. Extract entities ONLY if context clues are present
2. Do NOT guess or invent any entity
3. Preserve original formatting exactly
4. Do NOT split multi-word entities (e.g., 'John Doe' stays together)
5. **SPECIAL RULE for DATE_OF_BIRTH:** Dates are extremely common in text. Only extract as DATE_OF_BIRTH if you see explicit birth-related keywords like "born", "DOB", "birthday", "date of birth". Generic dates like "Date:", "Created on", "Meeting date" are NEVER birth dates.
6. **SPECIAL RULE for MEDICAL_RECORD_NUMBER, HEALTH_INSURANCE_NUMBER, and VIN:** Extract these only when their medical/insurance/vehicle context indicators appear. Do not extract standalone numeric/alphanumeric sequences without supporting context.

## Output JSON Schema

The keys and order MUST be exactly as shown:


{
  "PERSON": [],
  "STREET_ADDRESS": [],
  "COMPANY_NAME": [],
  "DATE_OF_BIRTH": [],
  "EMAIL": [],
  "SSN": [],
  "BBAN": [],
  "PHONE_NUMBER": [],
  "API_KEY": [],
  "SWIFT_BIC_CODE": [],
  "DRIVER_LICENSE_NUMBER": [],
  "CREDIT_CARD_NUMBER": [],
  "IBAN": [],
  "PASSPORT_NUMBER": [],
  "BANK_ROUTING_NUMBER": [],
  "BANK_ACCOUNT_NUMBER": [],
  "ITIN": [],
  "MEDICAL_RECORD_NUMBER": [],
  "HEALTH_INSURANCE_NUMBER": [],
  "VEHICLE_VIN": [],
  "LICENSE_PLATE_NUMBER": []
}


## Step-by-Step Extraction Procedure

1. Identify all potential entity spans in the sentence
2. For each entity type, check if context keywords exist
3. Keep only entities that match the definition AND context
4. Fill the output JSON schema exactly, using `[""]` for empty categories
5. Double-check order, key names, and formatting before output

## Reflection Process

Before providing your final JSON output, take a moment to reflect on your analysis:

**Think through these questions:**
- Have I identified all potential entities in the text?
- Does each extracted entity have clear context indicators?
- Am I following the exact JSON schema format?
- Have I avoided extracting entities without proper context?
- Are there any ambiguous cases that need careful consideration?
- **CRITICAL:** For any DATE_OF_BIRTH I extracted, did I see explicit birth-related keywords like "born", "DOB", "birthday"? Or am I just seeing a generic date?

**Reflection Steps:**
1. **Scan the text** - Look for any patterns that might indicate entities
2. **Verify context** - Ensure each potential entity has supporting context keywords
3. **Check format** - Confirm the entity matches the expected format for its type
4. **Validate extraction** - Double-check that you're not hallucinating or guessing
5. **Review schema** - Ensure all keys are present in the correct order

**Important:** Take your time to think through this carefully step by step. Accuracy is more important than speed. 

## Your Task
Identify the entities in the text based on above instructions and return the JSON response in the required format. It is important that you only identify an entity if there are relevant keyword present.
"""

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f" **Sentence:**  {text}"}
    ]
    return messages




def get_judge_prompt(text, results):
    SYSTEM_PROMPT = """You are an expert in Named Entity Recognition (NER) evaluation.
    Your task is to assess the correctness of identified entities by comparing them with the given text.
    """

    USER_PROMPT_1 = "Are you clear about your role?"

    ASSISTANT_PROMPT_1 = """Yes, I understand my role.
    Please provide me with the text and the identified NER results for evaluation.
    """

    GUIDELINES_PROMPT = """
    **Evaluation Criteria:**
    1. **Contextual Accuracy:** Does the identified entity exist within the text in a meaningful way?
    2. **Entity Type Appropriateness:** Is the assigned entity type correct (e.g., a person is identified as PERSON)?
    3. **Keyword Association:** Even if contextual signals are weak, does the entity match expected keywords?
    4. Think step by step before providing the output.

    **Output Format:**
    Return a JSON response in the format:
    ```
    {
        "entity_1": "Correct" / "Incorrect",
        "entity_2": "Correct" / "Incorrect",
        ...
    }
    ```
    Do not include explanations or extra text.
    """

    EXAMPLES_PROMPT = """
    **Example 1:**
    **Text:** "Barack Obama was born in Hawaii and served as the 44th President of the United States. His driving license was not issued."
    **NER Output:**
    ```
    {
        "person": ["Barack Obama"],
        "location": ["Hawaii", "United States"],
        "title": ["44th President"],
        "driving_license": ["not issued"]
    }
    ```
    **Expected JSON Response:**
    ```
    {
        "person": "Correct",
        "location": "Correct",
        "title": "Correct",
        "driving_license": "Incorrect",
        "reason": "Driving license is not mentioned in the text"
    }
    ```

    **Example 2:**
    **Text:** "Passport ID: 331410736  GitHub Token: ghr_abcdef1234567890ghijklmnopqrstuvwxYZ IBAN Number: GB27GKPH81111877912857."
    **NER Output:**

    {
        "us-passport-number": ["331410736"],
        "github-token": ["ghr_abcdef1234567890ghijklmnopqrstuvwxYZ"],
        "iban-code": ["GB27GKPH81111877912857"],
        "us-drivers-license": ["331410736"]
    }

    **Expected JSON Response:**

    {
        "us-passport-number": "Correct",
        "github-token": "Correct",
        "iban-code": "Correct",
        "us-drivers-license": "Incorrect",
        "reason": "No relevant keyword present in text related to driving license"
    }
    """

    FINAL_EVALUATION_PROMPT = f"""
    **Text to evaluate:**
    "{text}"

    **NER Output:**
    {results}

    **Provide the JSON Response in the required format:**
    """

    messages = [
        #{"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SYSTEM_PROMPT + " " + USER_PROMPT_1},
        {"role": "assistant", "content": ASSISTANT_PROMPT_1},
        {"role": "user", "content": GUIDELINES_PROMPT + " " + EXAMPLES_PROMPT + " " + FINAL_EVALUATION_PROMPT},
        #{"role": "user", "content": EXAMPLES_PROMPT},
        #{"role": "user", "content": FINAL_EVALUATION_PROMPT},
    ]

    return messages
