import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)


class Settings(BaseSettings):
    database_host: str
    database_port: str
    database_name: str
    database_user: str
    database_password: str

    # If you need these additional settings
    proxy_endpoint_url: str | None = None
    deepseek_api_key: str | None = None

    class Config:
        env_file = dotenv_path
        # Map environment variables to field names
        env_prefix = "DATABASE_"  # This will automatically convert DATABASE_HOST to database_host
        case_sensitive = False  # This makes the matching case-insensitive


settings = Settings()
