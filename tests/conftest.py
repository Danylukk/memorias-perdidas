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
    """Bloqueia rede externa; permite o socketpair local do asyncio no Windows."""
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_getaddrinfo = socket.getaddrinfo

    def connect(sock, address):
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect(sock, address)
        raise AssertionError("Rede externa proibida nos testes automatizados.")

    def connect_ex(sock, address):
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect_ex(sock, address)
        raise AssertionError("Rede externa proibida nos testes automatizados.")

    def getaddrinfo(host, *args, **kwargs):
        if host in ("127.0.0.1", "::1", "localhost"):
            return original_getaddrinfo(host, *args, **kwargs)
        raise AssertionError("Rede externa proibida nos testes automatizados.")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
