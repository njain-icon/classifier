from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
try:
    # Pydantic v2
    from pydantic import ConfigDict
except Exception:
    ConfigDict = dict  # fallback type hint only


class RegexPattern(BaseModel):
    pattern: str
    score: float = 0.5


class RegexConfig(BaseModel):
    patterns: List[RegexPattern] = Field(default_factory=list)
    context: List[str] = Field(default_factory=list)


class Thresholds(BaseModel):
    min_confidence: float = 0.6


class LLMTemplate(BaseModel):
    system: str = ""
    user_template: str = ""
    # Optional structured sections for composing the system prompt
    compose: List[str] = Field(default_factory=list)
    role: str = ""
    instructions: str = ""
    entities_doc: str = "{entities_doc}"
    extraction_rules: str = ""
    cot: str = ""
    output_json_schema: str = "{output_json_schema}"
    reflection: str = ""


class EntityLLM(BaseModel):
    # Output key the LLM must emit for this entity
    output_key: Optional[str] = None
    # Short description used in prompt composition
    description: Optional[str] = None
    # Additional guidance lines for this entity (appear in prompt)
    notes: List[str] = Field(default_factory=list)
    # Example strings to include in prompt docs
    examples: List[str] = Field(default_factory=list)
    detection: Optional[LLMTemplate] = None
    validation: Optional[LLMTemplate] = None

    @validator("notes", pre=True)
    def _normalize_notes(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v


class DetectConfig(BaseModel):
    methods: List[str] = Field(default_factory=list)  # any of ["builtin", "regex", "llm"]
    regex: Optional[RegexConfig] = None
    thresholds: Optional[Thresholds] = None
    # Names emitted by Presidio builtin recognizers that should map to this YAML entity id
    builtin_names: List[str] = Field(default_factory=list)

    @validator("methods", pre=True, always=True)
    def _normalize_methods(cls, v: Any) -> List[str]:
        if not v:
            return []
        allowed = {"builtin", "regex", "llm"}
        return [m for m in v if m in allowed]


class ValidateConfig(BaseModel):
    fn: Optional[str] = None
    rules: Dict[str, Any] = Field(default_factory=dict)


class EntityConfig(BaseModel):
    group: str
    enabled: bool = True
    detect: DetectConfig
    # Optional override for output/display name (e.g., map 'us-ssn' -> 'US_SSN' or vice-versa)
    return_name: Optional[str] = None
    # Preferred flat field: use this moving forward
    validate_fn: Optional[str] = None
    # Back-compat: nested validate { fn: ... } – use 'validation' attribute, keep alias for YAML key 'validate'
    validation: Optional[ValidateConfig] = Field(default=None, alias="validate")
    llm: Optional[EntityLLM] = None
    # Single-source keywords for prompts and regex context (fallback)
    context_indicators: List[str] = Field(default_factory=list)
    compliance_tags: List[str] = Field(default_factory=list)

    # Allow population by field name so the alias works bidirectionally (pydantic v2)
    try:
        model_config = ConfigDict(populate_by_name=True)
    except Exception:
        pass


class EnhancerConfig(BaseModel):
    similarity_factor: float = 0.35
    min_score_with_context: float = 0.4


class LLMDefaults(BaseModel):
    detection: LLMTemplate = Field(default_factory=LLMTemplate)
    validation: LLMTemplate = Field(default_factory=LLMTemplate)


class CountryConfig(BaseModel):
    country: str
    use_presidio_defaults: bool = True
    builtin_recognizers: List[str] = Field(default_factory=list)
    enhancer: EnhancerConfig = Field(default_factory=EnhancerConfig)
    llm: Optional[LLMDefaults] = None
    entities: Dict[str, EntityConfig]


