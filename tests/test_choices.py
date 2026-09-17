from dataclasses import asdict

import pytest

from game.models.state import new_game
from game.systems.choices import CHOICES, apply_choice


@pytest.mark.parametrize("choice_id,changes,trust", [
    (1, {"curiosidade": 1}, 20),
    (2, {"curiosidade": 2}, 20),
    (3, {"empatia": 2, "lealdade": 1}, 30),
    (4, {"egoismo": 2}, 10),
])
def test_exact_effects(choice_id, changes, trust):
    initial = new_game()
    updated = apply_choice(initial, choice_id)
    assert asdict(updated.player) == asdict(initial.player) | changes
    assert asdict(updated.npc) == asdict(initial.npc) | {"confianca_em_kael": trust}
    assert updated.situacao == initial.situacao
    assert initial == new_game()


def test_exactly_four_choices_and_invalid_choice():
    assert [c.label for c in CHOICES] == [
        "Quem é você?", "Você me conhece?", "Ajudar o soldado", "Ir embora",
    ]
    state = new_game()
    with pytest.raises(ValueError):
        apply_choice(state, 99)
    assert state == new_game()
