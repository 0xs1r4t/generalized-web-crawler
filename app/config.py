import os
from pydantic import BaseSettings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Settings(BaseSettings):

    database_hostname: str
    database_port: str
    database_name: str
    database_username: str
    database_password: str

    class Config:
        env_file = dotenv_path

settings = Settings()
