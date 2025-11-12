from pydantic import BaseModel
from typing import List, Dict
from enum import Enum


class EntityClassification(BaseModel):
    """Pydantic model for entity classification results.

    All fields are lists of strings, which may be empty if no entities of that type are found.

    Attributes:
        SSN (List[str]): Social Security Numbers.
        PASSPORT_NUMBER (List[str]): Passport numbers.
        DRIVER_LICENSE_NUMBER (List[str]): Driver license numbers.
        EMAIL (List[str]): Email addresses.
        PERSON (List[str]): Person names.
        COMPANY_NAME (List[str]): Company names.
        STREET_ADDRESS (List[str]): Street addresses.
        PHONE_NUMBER (List[str]): Phone numbers.
        DATE_OF_BIRTH (List[str]): Dates of birth.
        IP_ADDRESS (List[str]): IP addresses.
        CREDIT_CARD_NUMBER (List[str]): Credit card numbers.
        BANK_ACCOUNT_NUMBER (List[str]): Bank account numbers.
        IBAN (List[str]): International Bank Account Numbers.
        ITIN (List[str]): Individual Taxpayer Identification Numbers.
        BANK_ROUTING_NUMBER (List[str]): Bank routing numbers.
        SWIFT_BIC_CODE (List[str]): SWIFT/BIC codes.
        BBAN (List[str]): Basic Bank Account Numbers.
        API_KEY (List[str]): API keys.
        MEDICAL_RECORD_NUMBER (List[str]): Medical record numbers.
        HEALTH_INSURANCE_NUMBER (List[str]): Health insurance numbers.
        VEHICLE_VIN (List[str]): Vehicle VINs.
    """

    SSN: List[str] = []
    PASSPORT_NUMBER: List[str] = []
    DRIVER_LICENSE_NUMBER: List[str] = []
    EMAIL: List[str] = []
    PERSON: List[str] = []
    COMPANY_NAME: List[str] = []
    STREET_ADDRESS: List[str] = []
    PHONE_NUMBER: List[str] = []
    DATE_OF_BIRTH: List[str] = []
    IP_ADDRESS: List[str] = []
    CREDIT_CARD_NUMBER: List[str] = []
    BANK_ACCOUNT_NUMBER: List[str] = []
    IBAN: List[str] = []
    ITIN: List[str] = []
    BANK_ROUTING_NUMBER: List[str] = []
    SWIFT_BIC_CODE: List[str] = []
    BBAN: List[str] = []
    API_KEY: List[str] = []
    MEDICAL_RECORD_NUMBER: List[str] = []
    HEALTH_INSURANCE_NUMBER: List[str] = []
    VEHICLE_VIN: List[str] = []
    LICENSE_PLATE_NUMBER: List[str] = []
    
class EntityDict(BaseModel):
    entity_dict: Dict[str, List[str]]

class EntityValidation(BaseModel):
    id: int
    is_valid: bool
    reason: str
    confidence: float



