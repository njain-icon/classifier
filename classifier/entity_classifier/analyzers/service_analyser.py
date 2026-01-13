
from collections import defaultdict
from typing import List, Optional
from datetime import datetime

from presidio_analyzer import Pattern, PatternRecognizer

class ServiceNumberRecognizer(PatternRecognizer):
    """
    Recognize Military / Government Service Numbers.
    """

    PATTERNS = [
        Pattern(
            "SERVICE_NUMBER",
            r"\b[A-Z]{1,3}\d{6,10}\b",
            1),
        Pattern("SERVICE_NUMBER_HYPHEN",
                r"\b[A-Z]{1,3}[-\s]?\d{6,10}\b",
                1)]

    CONTEXT= ["service","number","service-number","military","army","navy","airforce","defense","service id"]


    def __init__(
        self,
        supported_language: str = "en",
        supported_entity: str = "SERVICE_NUMBER",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=supported_language,
        )
