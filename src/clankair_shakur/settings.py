from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings
import logging as log

class AppSettings(BaseSettings):
    discord_token: str
    thread_limit: int | None = Field(default=None, gt=0)

@lru_cache
def get_settings() -> AppSettings:
    try:
        return AppSettings()
    except ValueError as e:
        log.error(f"Failed to load app settings: {e}")
        raise