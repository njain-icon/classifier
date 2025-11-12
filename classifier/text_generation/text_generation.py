"""
Module for topic classification using Pebblo, Hugging Face, and Bedrock/vLLM/Together AI backends.
Defines the TextGeneration class with methods for predicting topics and extracting them from the model's response.

Supported backends:
- vLLM: For local or hosted vLLM instances
- Bedrock: For AWS Bedrock models
- Together AI: For Together AI hosted models

Rate Limiting and Retry Logic:
This module includes robust retry logic using the backoff library to handle rate limiting errors
from various LLM providers. The retry mechanism is implemented at the LLM call level for optimal efficiency:

- Retry logic is applied to _call_bedrock, _call_llm, _call_together_ai, and _call_vllm methods
- High-level methods (generate_entity, generate, etc.) automatically benefit from retry logic
- Only the actual API calls are retried, not the entire method execution
- Exponential backoff with configurable delays and limits
- Intelligent error detection for rate limit scenarios
- Comprehensive logging of retry attempts and failures

Environment variables for retry configuration:
- LLM_MAX_RETRIES: Maximum number of retry attempts (default: 5)
- LLM_BASE_DELAY: Base delay in seconds for exponential backoff (default: 1.0)
- LLM_MAX_DELAY: Maximum delay in seconds (default: 60.0)
- LLM_MAX_TIME: Maximum total time for all retries (default: 300.0 seconds)

Environment variables:
- BACKEND: Set to "together_ai" to use Together AI backend
- TOGETHER_API_KEY: Your Together AI API key
- TOGETHER_API_BASE: Together AI API base URL (defaults to https://api.together.xyz)
- MODEL_NAME: Model to use (e.g., "meta-llama/Llama-3-70b-chat-hf")

Example usage:
    export BACKEND="together_ai"
    export TOGETHER_API_KEY="your_api_key_here"
    export MODEL_NAME="meta-llama/Llama-3-70b-chat-hf"
    
    # Real-time inference
    text_gen = TextGeneration()
    result = text_gen.generate([{"role": "user", "content": "Hello"}])
"""

import os
from typing import List, Dict, Union, Optional, Any

import backoff
from boto3 import client as boto3_client
from json_repair import repair_json
from litellm import completion
from litellm.exceptions import RateLimitError
from classifier.log import get_logger
from classifier.app.enums.common import BackendType
from langchain_core.output_parsers.json import JsonOutputParser
from classifier.text_generation.model import EntityClassification
import litellm

logger = get_logger(__name__)


# Environment variables for backend configuration
BACKEND: str = os.getenv("BACKEND", BackendType.VLLM.value)
MODEL_NAME: str = os.getenv("MODEL_NAME", "")
API_BASE_URL: str = os.getenv("API_BASE_URL", "")
AWS_REGION: Optional[str] = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
# Together AI configuration
TOGETHER_API_KEY: Optional[str] = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_BASE: str = os.getenv("TOGETHER_API_BASE", "https://api.together.xyz")


# Retry configuration for rate limiting using backoff library
MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "5"))
BASE_DELAY: float = float(os.getenv("LLM_BASE_DELAY", "30.0"))
MAX_DELAY: float = float(os.getenv("LLM_MAX_DELAY", "60.0"))
MAX_TIME: float = float(os.getenv("LLM_MAX_TIME", "300.0"))  # 5 minutes total


def _is_rate_limit_error(error_msg: str) -> bool:
    """
    Check if an error message indicates a rate limit error.
    
    Args:
        error_msg (str): The error message to check
        
    Returns:
        bool: True if it's a rate limit error, False otherwise
    """
    rate_limit_indicators = [
        "Too many tokens",
        "RateLimitError",
        "rate limit",
        "rate limiting",
        "too many requests",
        "quota exceeded",
        "throttling",
        "throttled"
    ]
    
    error_lower = error_msg.lower()
    return any(indicator.lower() in error_lower for indicator in rate_limit_indicators)


def _should_retry_on_exception(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception (Exception): The exception to check
        
    Returns:
        bool: True if retry should be attempted, False otherwise
    """
    if isinstance(exception, (RateLimitError)):
        error_msg = str(exception)
        return _is_rate_limit_error(error_msg)
    return False


# Bedrock client initialization - lazy loaded to avoid initialization before credentials are set
bedrock_client: Optional[Any] = None


class SingletonMeta(type):
    """
    Thread-safe Singleton implementation.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class TextGeneration(metaclass=SingletonMeta):
    """
    Singleton class for text generation and topic classification.
    
    Supports multiple backends:
    - vLLM for local/hosted inference
    - AWS Bedrock for cloud models
    - Together AI for hosted open-source models
    """


    @backoff.on_exception(
        backoff.expo,
        (RateLimitError),
        max_tries=MAX_RETRIES,
        max_time=MAX_TIME,
        giveup=lambda e: not _should_retry_on_exception(e),
        on_backoff=lambda details: logger.warning(
            f"vLLM rate limit hit, retrying in {details['wait']:.1f}s "
            f"(attempt {details['tries']}/{MAX_RETRIES + 1})"
        ),
        on_giveup=lambda details: logger.error(
            f"Max retries exceeded for vLLM rate limit. "
            f"Final error: {details['exception']}"
        )
    )
    def _call_vllm(self, message: List[Dict[str, Union[str, Any]]]) -> Dict[str, Any]:
        """
        Args:
           message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.
        Returns:
           Dict[str, Any]: Response from the vLLM API.
        """
        response = completion(
            model=f"hosted_vllm/{MODEL_NAME}",
            messages=message,
            temperature=0,
            api_base=API_BASE_URL,
            top_p=0.3
        )
        return response.json()

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError),
        max_tries=MAX_RETRIES,
        max_time=MAX_TIME,
        giveup=lambda e: not _should_retry_on_exception(e),
        on_backoff=lambda details: logger.warning(
            f"Bedrock rate limit hit, retrying in {details['wait']:.1f}s "
            f"(attempt {details['tries']}/{MAX_RETRIES + 1})"
        ),
        on_giveup=lambda details: logger.error(
            f"Max retries exceeded for Bedrock rate limit. "
            f"Final error: {details['exception']}"
        )
    )
    def _call_bedrock(
        self, message: List[Dict[str, Union[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.
            model_type (Optional[ModelType]): Type of model to use for response formatting.
        Returns:
            Dict[str, Any]: Response from the Bedrock API.
        """
       
        
        # Lazy initialization of bedrock client - only create if it doesn't exist
        if bedrock_client is None:
            bedrock_client = boto3_client(
                service_name="bedrock-runtime",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
            )
        
        
        response = completion(
            model=f"{os.environ.get('MODEL_NAME')}",
            messages=message,
            temperature=0,
            custom_llm_provider="bedrock",
            aws_bedrock_client=bedrock_client,
            response_format=EntityClassification
        )
       
        return response.json()
    

    def _call_together_ai(
        self, message: List[Dict[str, Union[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.
            model_type (Optional[ModelType]): Type of model to use for response formatting.
        Returns:
            Dict[str, Any]: Response from the Together AI API.
        """
        if not TOGETHER_API_KEY:
            logger.error("TOGETHER_API_KEY environment variable is required for Together AI backend")
            raise ValueError("TOGETHER_API_KEY environment variable is required for Together AI backend")
        
        try:
            litellm.drop_params=True
            response = completion(
                model=f"together_ai/{MODEL_NAME}",
                messages=message,
                temperature=0,
                api_key=TOGETHER_API_KEY,
                api_base=TOGETHER_API_BASE,
                response_format=EntityClassification
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error in Together AI API call: {e}")
            raise

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError),
        max_tries=MAX_RETRIES,
        max_time=MAX_TIME,
        giveup=lambda e: not _should_retry_on_exception(e),
        on_backoff=lambda details: logger.warning(
            f"LLM rate limit hit, retrying in {details['wait']:.1f}s "
            f"(attempt {details['tries']}/{MAX_RETRIES + 1})"
        ),
        on_giveup=lambda details: logger.error(
            f"Max retries exceeded for LLM rate limit. "
            f"Final error: {details['exception']}"
        )
    )

    def get_llm_response(
        self, message: List[Dict[str, Union[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.
        Returns:
            Dict[str, Any]: Response from the appropriate LLM backend.
        """
        if BACKEND == BackendType.BEDROCK.value:
            return self._call_bedrock(message)
        elif BACKEND == BackendType.TOGETHER_AI.value:
            return self._call_together_ai(message)
        else:
            return self._call_vllm(message)

    def generate_entity(
        self, message: List[Dict[str, Union[str, Any]]], bool_return_json: bool = True
    ) -> Union[str, None]:
        """
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.-            
            bool_return_json (bool): Whether to return repaired JSON.
        Returns:
            Union[str, None]: Generated text or error message.
        """
        try:
            response = self.get_llm_response(message)
            # Extract text from the response
            text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if isinstance(text, str):
                parser = JsonOutputParser()
                parsed = parser.parse(text)
            else:
                parsed = text
            return parsed
        except Exception as ex:
            logger.error(f"Error during generate_entity: {ex}")
            # Try to extract response if available
            try:
                if 'response' in locals():
                    text: str = (
                        response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    )
                    if bool_return_json:
                        text = repair_json(text)
                    return text
            except Exception:
                pass
            return None

        
    def generate(
        self, message: List[Dict[str, Union[str, Any]]], bool_return_json: bool = True
    ) -> Union[str, None]:
        """
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.-           
            bool_return_json (bool): Whether to return repaired JSON.
        Returns:
            Union[str, None]: Generated text or error message.
        """
        try:
            response = self.get_llm_response(message)

            # Extract text from the response
            text: str = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            if bool_return_json:
                text = repair_json(text.replace("```json", "").replace("```", ""))
            return text
        except Exception as ex:
            logger.error(f"Error during generation: {ex}")
            return None

        
    def generate_validation(
        self, message: List[Dict[str, Union[str, Any]]], bool_return_json: bool = True
    ) -> Union[str, None]:
        """
        Generates validation responses using the LLM for entity validation tasks.
        
        Args:
            message (List[Dict[str, Union[str, Any]]]): List of messages for the LLM.
            bool_return_json (bool): Whether to return repaired JSON.
        Returns:
            Union[str, None]: Generated validation response or error message.
        """
        try:
            response = self.get_llm_response(message, ModelType.ENTITY_VALIDATION)
            # Extract text from the response
            text: str = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            try:
                parser = JsonOutputParser()
                parsed = parser.parse(text)
                return parsed
            except Exception as ex:
                logger.error(f"Error during generate_validation: {ex}")
                # If JSON parsing fails, try to repair the JSON
                repaired_text = repair_json(text.replace("```json", "").replace("```", ""))
                return repaired_text
        except Exception as ex:
            logger.error(f"Error during generate_validation: {ex}")
            return None



