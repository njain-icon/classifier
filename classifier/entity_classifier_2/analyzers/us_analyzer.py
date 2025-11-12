import re
from typing import List

from classifier.entity_classifier_2.core.config import CountryConfig
from classifier.entity_classifier_2.core.prompts import PromptProvider
from classifier.text_generation.text_generation import TextGeneration
from classifier.entity_classifier_2.analyzers.base_analyzer import BaseCountryAnalyzer
from classifier.entity_classifier_2.core.validation import ValidationProvider
from classifier.log import get_logger
from classifier.entity_classifier_2.core.utils import is_valid_numeric_field, has_consecutive_increasing_numbers, has_consecutive_decreasing_numbers, has_consecutive_repetitive_numbers
from stdnum.us import ssn
from dateutil.parser import parse

logger = get_logger(__name__)

class USAnalyzer(BaseCountryAnalyzer):
    """Country analyzer for US-specific entities: SSN, ITIN, and bank account.

    Args:
        cfg: Country configuration.
        supported_entities: Entity ids handled by this analyzer.
        enable_pattern: Whether regex detection is active.
        enable_llm: Whether LLM detection is active.
        prompt_provider: Prompt provider for LLM interactions.
        validation: Validation provider.
        text_gen: Optional text generation interface.
        supported_language: Presidio language code.
        context: Optional contextual hints.
    """
    def __init__(
        self,
        cfg: CountryConfig,
        supported_entities: List[str],
        enable_pattern: bool,
        enable_llm: bool,
        prompt_provider: PromptProvider,
        validation: ValidationProvider | None = None,
        text_gen: TextGeneration | None = None,
        supported_language: str = "en",
        context: List[str] | None = None,
    ) -> None:
        super().__init__(
            cfg,
            supported_entities,
            enable_pattern,
            enable_llm,
            prompt_provider,
            validation,
            text_gen,
            supported_language,
            context,
        )


def validate_us_ssn(value: str, text: str) -> bool:
    """Validate US Social Security Number via ``python-stdnum``.

    Args:
        value: Candidate SSN string.
        text: Source text (unused).

    Returns:
        ``True`` when library validation succeeds; otherwise ``False``.

    Failure Modes:
        Logs validation attempt and exception stack; returns ``False`` on errors.
    """
    try:
        op = bool(ssn.is_valid(value))
        return op
    except Exception:
        logger.exception("us ssn validation raised exception")
        return False


def validate_bank_account_number(value: str, text: str) -> bool:
    """Validate US bank account number heuristically.

    Args:
        value: Candidate account string.
        text: Source text (unused).

    Returns:
        ``True`` when length and pattern heuristics pass; otherwise ``False``.

    Failure Modes:
        Logs diagnostic flags and returns ``False`` on failure or exception.
    """
    try:
        digit_value = re.sub(r"\D", "", value)
        a1 = 6 <= len(digit_value) <= 17
        a2 = not is_valid_numeric_field(value)
        a3 = not has_consecutive_increasing_numbers(value)
        a4 = not has_consecutive_decreasing_numbers(value)
        a5 = not has_consecutive_repetitive_numbers(value)
        op = len(value) <= 15 and a2 and a3 and a4 and a5 and a1
        return op
    except Exception:
        logger.exception("bank account number validation raised exception")
        return False

def validate_email(value: str, text: str) -> bool:
    """Validate email address (basic check for ``@`` and ``.``).

    Args:
        value: Candidate email string.
        text: Source text (unused).

    Returns:
        ``True`` when both ``@`` and ``.`` appear; otherwise ``False``.

    Failure Modes:
        Returns ``False`` on exceptions while logging.
    """
    try:
        return "@" in value and "." in value
    except Exception:
        logger.exception("email validation raised exception")
        return False

def validate_phone_number(value: str, text: str)-> bool:
    """Heuristic phone-number validation.

    Args:
        value: Candidate phone number string.
        text: Source text (unused).

    Returns:
        ``True`` when length and sequence heuristics are met; otherwise ``False``.

    Failure Modes:
        Returns ``False`` and logs on failure or exception.
    """
    try:
        return 7 <= len(value) <= 30 and \
        not has_consecutive_increasing_numbers(value) and \
        not has_consecutive_decreasing_numbers(value) and \
        not has_consecutive_repetitive_numbers(value)
    except Exception:
        logger.exception("phone number validation raised exception")
        return False
    

def validate_date_of_birth(value: str, text: str) -> bool:
    """Validate date of birth by parsing.

    Args:
        value: Candidate date string.
        text: Source text (unused).

    Returns:
        ``True`` when parsing succeeds; otherwise ``False``.

    Failure Modes:
        Logs detailed message and returns ``False`` when parsing fails or raises.
    """
    try:
        parse(value)
        return True
    except Exception:
        logger.exception("date of birth validation raised exception")
        return False