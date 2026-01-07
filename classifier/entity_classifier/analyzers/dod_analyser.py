from presidio_analyzer import Pattern, PatternRecognizer

class DoDIdRecognizer(PatternRecognizer):
    """
    Recognize DoD ID Number (10 digits).
    """

    PATTERNS = [
        Pattern("DOD_ID",r"\bDOD[-\s]?\d{8,12}\b", 0.95)

    ]

    CONTEXT = ["dod id", "department of defense", "military id", "dod number","DOD"]

    def __init__(
        self,
        supported_language: str = "en",
        supported_entity: str = "DOD_ID",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )
