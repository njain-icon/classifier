from collections import defaultdict
from typing import List, Optional
from datetime import datetime

from presidio_analyzer import Pattern, PatternRecognizer


class MedicalLicenseRecognizer(PatternRecognizer):
    """
    Recognize Medical Staff License Numbers.

    Supported formats:
    - MD123456
    - LIC-987654
    - DMC/12345
    """

    PATTERNS = [
        Pattern(
            "MED_LICENSE",
            r"\b(?:LIC|MD|DMC|MED)[-/]?\d{4,10}\b",
            1,
        ),
    ]

    CONTEXT = [
        "medical license",
        "license number",
        "doctor license",
        "physician license",
        "medical registration",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        super().__init__(
            supported_entity="MEDICAL_LICENSE",
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
        )
