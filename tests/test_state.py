from dataclasses import FrozenInstanceError, asdict

import pytest

from game.models.state import new_game


def test_initial_state():
    state = new_game()
    assert asdict(state.player) == {
        "nome": "Kael", "vida": 100, "energia": 100, "empatia": 0,
        "agressividade": 0, "curiosidade": 0, "egoismo": 0,
        "lealdade": 0, "fragmentos": 0,
    }
    assert state.npc.nome == "Darian"
    assert state.npc.confianca_em_kael == 20
    assert state.npc.conhece_kael is True
    assert state.npc.pode_revelar_passado is False
    assert state.npc.personalidade == ("disciplinado", "desconfiado", "leal")
    assert state.npc.estado == "gravemente ferido"


def test_new_game_is_independent_and_immutable():
    first, second = new_game(), new_game()
    assert first == second
    assert first is not second
    with pytest.raises(FrozenInstanceError):
        first.player.empatia = 999
