from presidio_analyzer import Pattern, PatternRecognizer
from typing import Optional, List


class BusinessTaxIdRecognizer(PatternRecognizer):
    """
    Recognize Business / Practice Tax ID (EIN).

    Supported formats:
    - 12-3456789
    - 123456789
    """

    PATTERNS = [
        Pattern(
            "EIN_WITH_HYPHEN",
            r"\b\d{2}-\d{7}\b",
            0.8,
        ),
        Pattern(
            "EIN_NO_HYPHEN",
            r"\b\d{9}\b",
            0.6,
        ),
    ]

    CONTEXT = [
        "ein",
        "tax id",
        "tax identification",
        "business tax",
        "practice tax",
        "employer identification",
        "irs",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        super().__init__(
            supported_entity="BUSINESS_TAX_ID",
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
        )
