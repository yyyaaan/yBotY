# YYYan
from pydantic import BaseSettings
from sys import modules


class Settings(BaseSettings):
    OPENAI_KEY: str
    AZ_OPENAI_KEY: str = "missing"
    AZ_OPENAI_BASE: str = "https://none"
    AZ_OPENAI_VERSION: str = "2023-05-15"
    AZ_OPENAI_DEPLOYMENT: str = "gpt4"

    class Config:
        env_prefix = "BOT"
