import importlib.util
import logging
import os
from typing import Optional, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from classifier.app.config import utils
from classifier.app.config.utils import (
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_FILE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MAX_FILE_SIZE,
    dir_path,
    expand_path,
    update_anonymize_snippets_exists,
)

# Port BaseModel
class DaemonConfig(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=8000)

    @field_validator("port")
    @classmethod
    def check_port_validity(cls, port: int) -> int:
        # check to validate port should be between 0 and 65535
        if not (0 < port <= 65535):
            raise ValueError(
                f"Error: Invalid port '{port}'. Port must be between 1 and 65535."
            )
        return port

# Logging BaseModel
class LoggingConfig(BaseSettings):
    level: str = Field(default=DEFAULT_LOG_LEVEL)
    file: str = Field(default=DEFAULT_LOG_FILE)
    maxFileSize: int = Field(default=DEFAULT_LOG_MAX_FILE_SIZE)
    backupCount: int = Field(default=DEFAULT_LOG_BACKUP_COUNT)

    @field_validator("level")
    @classmethod
    def validate_logging_level_value(cls, level: str) -> str:
        # check to validate level entry
        if level.upper() not in logging._nameToLevel:
            raise ValueError(
                f"Error: Unsupported logLevel '{level}' specified in the configuration"
            )
        return level


# ConfigFile BaseModel
class Config(BaseSettings):
    daemon: DaemonConfig
    logging: LoggingConfig

