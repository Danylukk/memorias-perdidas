"""Progresso, galeria de fragmentos e configurações em JSON local (CP4 §4: estado narrativo em JSON)."""
import json
import os

from game.config import PROJECT_ROOT

SAVE_DIR = PROJECT_ROOT / "save"
PROGRESS = "progresso.json"
GALLERY = "fragmentos.json"
SETTINGS = "configuracoes.json"
DEFAULT_SETTINGS = {"usar_ia": True, "tela_cheia": False, "texto_animado": True}


def read(name: str, default=None):
    try:
        return json.loads((SAVE_DIR / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write(name: str, data) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = SAVE_DIR / f"{name}.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(temporary, SAVE_DIR / name)


def delete(name: str) -> None:
    try:
        (SAVE_DIR / name).unlink()
    except OSError:
        pass


def has_progress() -> bool:
    return (SAVE_DIR / PROGRESS).exists()


def load_settings() -> dict:
    stored = read(SETTINGS, {})
    return {key: stored.get(key, value) if isinstance(stored, dict) else value
            for key, value in DEFAULT_SETTINGS.items()}


def save_settings(settings: dict) -> None:
    write(SETTINGS, settings)
