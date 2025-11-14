"""YAML-driven, country-specific entity classifier (v2) scaffolding.

Modules:
- config: Pydantic models for country/entity configuration.
- loader: Load and validate country YAML into config models.
- prompts: PromptProvider for detection and validation messages.
- validation: ValidationRules methods and ValidationProvider dispatcher.
- factory: Build Presidio registry/engine from config.
- country_analyzer: Orchestrates Presidio + LLM + validation.
"""

from classifier.entity_classifier.core.config import (
    CountryConfig,
    EntityConfig,
    DetectConfig,
    RegexConfig,
    RegexPattern,
    Thresholds,
    LLMDefaults,
    LLMTemplate,
    EntityLLM,
    EnhancerConfig,
    ValidateConfig,
)
from classifier.entity_classifier.core.loader import load_country_config
from classifier.entity_classifier.core.prompts import PromptProvider
from classifier.entity_classifier.entity_classifier import EntityClassifier

__all__ = [
    "load_country_config",
    "PromptProvider",
    "AnalyzerPool",
    "EntityClassifier",
]


__all__ = [
    "CountryConfig",
    "EntityConfig",
    "DetectConfig",
    "RegexConfig",
    "RegexPattern",
    "Thresholds",
    "LLMDefaults",
    "LLMTemplate",
    "EntityLLM",
    "EnhancerConfig",
    "ValidateConfig",
    "load_country_config",
    "PromptProvider",
    "ValidationRules",
    "ValidationProvider",
]


