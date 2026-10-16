import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    api_url: str = "http://127.0.0.1:8000"
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        return cls(
            api_key=os.getenv("API_KEY", "").strip(),
            api_url=os.getenv("API_URL", "http://127.0.0.1:8000").strip(),
        )

    def validate(self) -> None:
        if not self.api_key or not self.api_url:
            raise ConfigurationError("Configure API_URL e API_KEY no frontend/.env e reinicie o jogo.")
