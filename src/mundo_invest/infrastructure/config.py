from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = "sqlite:///./mundo_invest.db"
    log_level: str = "INFO"
    pipefy_pipe_id: str = "000000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
