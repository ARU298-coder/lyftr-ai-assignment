import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "gemini/gemini-2.0-flash"
)

LLM_API_KEYS = [
    key.strip()
    for key in os.getenv("LLM_API_KEYS", "").split(",")
    if key.strip()
]

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if origin.strip()
]

ENABLE_FAILURE_SIMULATION = (
    os.getenv(
        "ENABLE_FAILURE_SIMULATION",
        "false"
    ).lower() == "true"
)