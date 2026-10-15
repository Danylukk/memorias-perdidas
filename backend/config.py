import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent


class ConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    model: str = ""
    timeout: float = 25.0
    access_key: str = field(default="", repr=False)
    cors_origins: tuple[str, ...] = ()

    @classmethod
    def from_env(cls):
        load_dotenv(BACKEND_ROOT / ".env", override=False)
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("OPENAI_MODEL", "").strip(),
            access_key=os.getenv("API_KEY", "").strip(),
            cors_origins=tuple(origin.strip() for origin in
                               os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()),
        )

    def validate(self):
        if not self.api_key or not self.model:
            raise ConfigurationError("Configure OPENAI_API_KEY e OPENAI_MODEL no backend/.env.")
