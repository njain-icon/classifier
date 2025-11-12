from enum import Enum


class BackendType(Enum):
    """Enum for supported LLM backend types."""
    VLLM = "vllm"
    BEDROCK = "bedrock"
    TOGETHER_AI = "together_ai"

