"""Prepara .env locais para a gravacao. Nunca imprime nem envia credenciais."""
from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "backend" / ".env"
FRONT = ROOT / "frontend" / ".env"
OLD = ROOT / ".env"


def ensure_env(path: Path) -> None:
    if not path.exists():
        example = path.with_name(".env.example")
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")


def read_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {k: v or "" for k, v in dotenv_values(path).items() if k}


def write_value(path: Path, name: str, value: str) -> None:
    content = path.read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    matcher = re.compile(r"^\s*" + re.escape(name) + r"\s*=")
    for index, line in enumerate(lines):
        if matcher.match(line):
            lines[index] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_env(BACK)
    ensure_env(FRONT)
    back, front, old = read_values(BACK), read_values(FRONT), read_values(OLD)
    a, b = back.get("API_KEY", "").strip(), front.get("API_KEY", "").strip()
    if a and b and a != b:
        print("ATENCAO: API_KEY diferente entre backend/.env e frontend/.env. Corrija antes de gravar.")
        return 2
    group_key = a or b or secrets.token_urlsafe(32)
    if a != group_key:
        write_value(BACK, "API_KEY", group_key)
    if b != group_key:
        write_value(FRONT, "API_KEY", group_key)
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL"):
        if not back.get(name, "").strip() and old.get(name, "").strip():
            write_value(BACK, name, old[name].strip())
            back[name] = old[name].strip()
    if not front.get("API_URL", "").strip():
        write_value(FRONT, "API_URL", "http://127.0.0.1:8000")
    missing = [k for k in ("OPENAI_API_KEY", "OPENAI_MODEL") if not back.get(k, "").strip()]
    if missing:
        print("PENDENTE: configure em backend/.env: " + ", ".join(missing))
        print("Nao exponha credenciais no video nem no repositorio.")
        return 2
    print("Configuracao local validada: credenciais presentes e API_KEY do grupo sincronizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
