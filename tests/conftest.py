import os
import socket

import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


@pytest.fixture(autouse=True)
def isolated_saves(monkeypatch, tmp_path):
    """Progresso, galeria e configurações dos testes nunca tocam a pasta save/ real."""
    monkeypatch.setattr("game.systems.save.SAVE_DIR", tmp_path / "save")


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Até um teste mal configurado deve falhar antes de acessar a rede."""
    def blocked(*args, **kwargs):
        raise AssertionError("Rede proibida nos testes automatizados.")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
