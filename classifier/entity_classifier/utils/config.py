"""
Copyright (c) 2024 Cloud Defense, Inc. All rights reserved.
"""

from enum import Enum

class Entities(Enum):
    US_SSN = "us-ssn"
    US_DRIVER_LICENSE = "us-drivers-license"
    EMAIL_ADDRESS = "email-address"
    PHONE_NUMBER = "phone-number"
    DATE_OF_BIRTH = "date-of-birth"
    US_BANK_NUMBER = "us-bank-account-number"
    ROUTING_NUMBER = "bank-routing-number"
    SERVICE_NUMBER = "service-number"
    DOD_ID = "dodi-number"
    VA_CLAIM_NUMBER = "va-claim-number"
    BUSINESS_TAX_ID = "business-tax-id"
    MEDICAL_LICENSE = "medical-license-number"
    EMPLOYEE_ID = "employee-id"



class ConfidenceScore(Enum):
    Entity = "0.8"  # based on this score entity output is finalized
    EntityMinScore = "0.45"  # It denotes the pattern's strength
    EntityContextSimilarityFactor = (
        "0.35"  # It denotes how much to enhance confidence of match entity
    )
    EntityMinScoreWithContext = "0.4"  # It denotes minimum confidence score
