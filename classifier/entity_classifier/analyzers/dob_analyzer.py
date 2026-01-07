from collections import defaultdict
from typing import List, Optional
from datetime import datetime
from presidio_analyzer import Pattern, PatternRecognizer


class DobRecognizer(PatternRecognizer):
    """
    Recognize Date of Birth (DOB) using regex patterns.

    Supported formats:
    - DD-MM-YYYY
    - DD/MM/YYYY
    - YYYY-MM-DD
    - DD.MM.YYYY
    """

    PATTERNS = [
        Pattern(
            "DOB_DDMMYYYY",
            r"\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[0-2])[-/.]([12][0-9]{3})\b",
            0.85,
        ),
        Pattern(
            "DOB_YYYYMMDD",
            r"\b([12][0-9]{3})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12][0-9]|3[01])\b",
            0.85,
        ),
    ]

    CONTEXT = [
        "date of birth",
        "dob",
        "born",
        "birth",
        "birthdate",
        "birthday",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "DATE_OF_BIRTH",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
        )

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Validate whether detected text is a real date.
        """

        # Normalize delimiter
        normalized = pattern_text.replace(".", "-").replace("/", "-")

        date_formats = ["%d-%m-%Y", "%Y-%m-%d"]

        valid_date = False
        for fmt in date_formats:
            try:
                dob = datetime.strptime(normalized, fmt)
                valid_date = True
                break
            except ValueError:
                continue

        if not valid_date:
            return True

        # Future dates are invalid DOBs
        if dob.date() > datetime.today().date():
            return True

        # Unrealistic age (>120 years)
        if datetime.today().year - dob.year > 120:
            return True

        return False
