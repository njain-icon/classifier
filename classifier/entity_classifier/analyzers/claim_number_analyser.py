from collections import defaultdict
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class VaClaimNumberRecognizer(PatternRecognizer):
    """
    Recognize VA Claim Numbers using regex patterns.

    Supported formats:
    - 9 digit number (123456789)
    - Hyphen separated (123-45-6789)
    - Space separated (123 456 789)
    """

 
    PATTERNS = [
        # Continuous 9 digits
        Pattern(
            "VA_CLAIM_CONTINUOUS",
            r"\b\d{9}\b",
            0.85,
        ),

        # Space separated: 123 456 789
        Pattern(
            "VA_CLAIM_SPACED",
            r"\b\d{3}\s\d{3}\s\d{3}\b",
            0.9,
        ),

        # Hyphen separated: 123-45-6789
        Pattern(
            "VA_CLAIM_HYPHENATED",
            r"\b\d{3}-\d{2}-\d{4}\b",
            0.9,
        ),
    ]


    CONTEXT = [
        "va claim",
        "va claim number",
        "claim number",
        "va file number",
        "va file no",
        "claim #",
        "va benefits",
        "veterans affairs",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "VA_CLAIM_NUMBER",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
        )

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Validate VA Claim Number.
        """

        # Extract only digits
        only_digits = "".join(c for c in pattern_text if c.isdigit())

        # Must be exactly 9 digits
        if len(only_digits) != 9:
            return True

        # Cannot be all same digit (e.g. 000000000)
        if all(only_digits[0] == d for d in only_digits):
            return True

        # Disallow obvious dummy numbers
        if only_digits in (
            "123456789",
            "987654321",
            "000000000",
        ):
            return True

        return False


# from typing import List, Optional
# from presidio_analyzer import Pattern, PatternRecognizer


# class VaClaimNumberRecognizer(PatternRecognizer):
#     """
#     Recognize VA Claim Numbers using regex patterns.

#     Supported formats:
#     - 9 digit number (123456789)
#     - Hyphen separated (123-45-6789)
#     - Space separated (123 456 789)
#     """

#     PATTERNS = [ Pattern("VA_CLAIM_NUMBER",r"\b\d{9}\b",1)]

#     CONTEXT = [
#         "va claim",
#         "va claim number",
#         "claim number",
#         "va file number",
#         "va file no",
#         "claim #",
#         "va benefits",
#         "veterans affairs",
#     ]

#     def __init__(
#         self,
#         patterns: Optional[List[Pattern]] = None,
#         context: Optional[List[str]] = None,
#         supported_language: str = "en",
#         supported_entity: str = "VA_CLAIM_NUMBER",
#     ):
#         super().__init__(
#             supported_entity=supported_entity,
#             patterns=patterns if patterns else self.PATTERNS,
#             context=context if context else self.CONTEXT,
#             supported_language=supported_language,
#         )

    # def invalidate_result(self, pattern_text: str) -> bool:
    #     """
    #     Reject invalid or fake VA claim numbers.
    #     """

    #     # Keep only digits
    #     digits = "".join(c for c in pattern_text if c.isdigit())

    #     # Must resolve to exactly 9 digits
    #     if len(digits) != 9:
    #         return True

    #     # Reject dummy / sequential numbers
    #     if digits in {
    #         "000000000",
    #         "111111111",
    #         "123456789",
    #         "987654321",
    #     }:
    #         return True

    #     return False
