import os
from dataclasses import dataclass


@dataclass
class Config:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    default_model: str = "llama3-8b-8192"


config = Config()
