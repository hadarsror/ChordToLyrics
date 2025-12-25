import os
import torch
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chord Aligner AI"

    # AI Config
    # Auto-detect GPU: If you have an NVIDIA GPU, this will massive speed up the process.
    INFERENCE_DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    # "medium" is the balance. "distil-medium.en" is 6x faster with <1% accuracy loss.
    # If you want pure speed, change this to "Systran/faster-distil-whisper-medium.en"
    WHISPER_MODEL_SIZE: str = "medium"

    COMPUTE_TYPE: str = "float16" if torch.cuda.is_available() else "int8"

    # Path logic
    RAW_DATA_PATH: str = "data/raw"
    PROCESSED_DATA_PATH: str = "data/processed"

    # # Redis
    # CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    # CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"

    # Redis
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # genius token
    GENIUS_API_TOKEN: str


settings = Settings()

os.makedirs(settings.RAW_DATA_PATH, exist_ok=True)
os.makedirs(settings.PROCESSED_DATA_PATH, exist_ok=True)