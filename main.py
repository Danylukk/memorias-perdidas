"""Compatibilidade com o comando original: python main.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))

from game.app import GameApp

if __name__ == "__main__":
    GameApp().run()
