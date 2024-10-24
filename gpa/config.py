import os
from dataclasses import dataclass


@dataclass
class Config:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    default_model: str = "mixtral-8x7b-32768"


config = Config()
