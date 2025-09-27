import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str = "AIzaSyDUp4ROMTn76KUSwd6MWR5i60K-rfw9b1Q"
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    environment: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        env_file = ".env"

settings = Settings()