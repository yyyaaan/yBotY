# YYYan, adjusted for pydantic settings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_KEY: str
    AZ_OPENAI_KEY: str = "missing"
    AZ_OPENAI_BASE: str = "https://none"
    AZ_OPENAI_VERSION: str = "2023-05-15"
    AZ_OPENAI_DEPLOYMENT: str = "gpt4"
    CHROMA_PATH: str = "/mnt/shared/chroma/"
    UPLOAD_PATH: str = "/mnt/shared/upload/"
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"

    class Config:
        env_prefix = "BOT_"
