from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    kproduction = "production"
    development = "development"
    staging = "staging"


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    ENVIRONMENT: Environment = Environment.development


envConfig = EnvConfig()


@lru_cache
def get_settings():
    return EnvConfig()


settings = get_settings()
