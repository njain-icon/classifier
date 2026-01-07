from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class EmployeeIdRecognizer(PatternRecognizer):
    """
    Recognize Employee / Staff Identifier Codes.
    """

    PATTERNS = [
        Pattern(
            "EMPLOYEE_ID_PREFIXED",
            r"\b(?:EMP|EID|STAFF|HR)[-_]?\d{4,10}\b",
            0.85,
        ),
        Pattern(
            "EMPLOYEE_ID_GENERIC",
            r"\b[A-Z]{2,4}\d{4,10}\b",
            0.85,
        ),
        Pattern(
           "EMPLOYEE_ID",
           r"[a-z]{2}-[0-9]{4}",
           0.85
        )
    ]

    CONTEXT = [
        "employee id",
        "employee code",
        "staff id",
        "staff code",
        "employee number",
        "staff number",
        "hr id",
        "personnel id",
        "payroll id",
        "Employee ID Number",

    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "EMPLOYEE_ID",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
        )
