from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Product Database URL
    PRODUCT_DATABASE_URL: str

    # Cache Database URL
    CACHE_DATABASE_URL: str

    # Optional settings
    PROXY_ENDPOINT_URL: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
