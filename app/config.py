from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Product Database URL
    PRODUCT_DATABASE_URL: str

    # Cache Database URL
    CACHE_DATABASE_URL: str

    # Admin settings
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_SECRET_KEY: str

    # Optional settings with defaults
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_ALGORITHM: str = "HS256"

    # Optional settings
    PROXY_ENDPOINT_URL: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
