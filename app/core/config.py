import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chord Aligner AI"

    # AI Config
    INFERENCE_DEVICE: str = "cpu"
    WHISPER_MODEL_SIZE: str = "medium"
    COMPUTE_TYPE: str = "int8"

    # Path logic: convert relative .env paths to absolute Windows paths
    RAW_DATA_PATH: str = "data/raw"
    PROCESSED_DATA_PATH: str = "data/processed"

    # Redis
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # genius token
    GENIUS_API_TOKEN: str


settings = Settings()

# Add this to ensure the folders exist the moment the app starts
os.makedirs(settings.RAW_DATA_PATH, exist_ok=True)
os.makedirs(settings.PROCESSED_DATA_PATH, exist_ok=True)