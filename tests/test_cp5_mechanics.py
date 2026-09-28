"""Mecânicas da CP5: rodadas, fragmentos de memória, desfecho e fallback."""
import json
import time
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from game.models.state import new_game
from game.systems.choices import ROUNDS, apply_choice, get_choice
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE
from game.systems.encounter import Encounter
from game.systems.ending import compute_ending
from game.systems.fragments import FRAGMENTS, get_fragment, newly_unlocked
from game.systems.openai_client import OpenAIClient
from game.systems.prompt_builder import PromptBuilder


def await_result(encounter):
    deadline = time.monotonic() + 3
    while encounter.generation_in_progress and time.monotonic() < deadline:
        encounter.update()
        time.sleep(0.001)
    assert not encounter.generation_in_progress


def play(encounter, *choice_ids):
    for choice_id in choice_ids:
        assert encounter.choose(choice_id)
        await_result(encounter)


def ok_service():
    service = MagicMock()
    service.respond.return_value = DialogueResult(text="Fique comigo.")
    service.remember.return_value = DialogueResult(text="Fogo e metal.")
    return service


def test_three_rounds_of_four_unique_choices():
    assert len(ROUNDS) == 3
    ids = [c.id for round_choices in ROUNDS for c in round_choices]
    assert all(len(r) == 4 for r in ROUNDS)
    assert len(ids) == len(set(ids)) == 12
    assert all(get_choice(c.id).fallback.strip() for r in ROUNDS for c in r)


def test_cp4_table_effects():
    # Tabela da seção 1.6 da CP4: ameaçar e perguntar sobre o passado.
    threatened = apply_choice(new_game(), 6)
    assert threatened.player.agressividade == 2
    assert threatened.player.empatia == 0  # limitado a 0
    assert threatened.player.vida == 90
    assert threatened.npc.confianca_em_kael == 5
    assert apply_choice(new_game(), 5).player.curiosidade == 2


def test_stats_are_clamped():
    state = new_game()
    for _ in range(3):
        state = apply_choice(state, 12)
    assert state.npc.confianca_em_kael == 0
    for _ in range(5):
        state = apply_choice(state, 9)
    assert state.player.energia == 0
    assert state.npc.confianca_em_kael == 50


def test_full_session_has_end_and_only_current_round_choices():
    service = ok_service()
    encounter = Encounter(service)
    assert not encounter.choose(5)  # rodada 2 ainda não começou
    play(encounter, 3)
    assert not encounter.choose(1)  # rodada 1 já foi
    play(encounter, 7, 9)
    assert encounter.finished
    assert encounter.current_choices == ()
    assert not encounter.choose(10)
    assert service.respond.call_count == 3
    # O histórico enviado na última rodada contém as falas anteriores.
    history = service.respond.call_args.args[2]
    assert [h["fala_de_darian"] for h in history] == ["Fique comigo.", "Fique comigo."]


def test_fragments_unlocked_by_python_and_text_by_ai():
    service = ok_service()
    encounter = Encounter(service)
    play(encounter, 3, 7)  # confiança 20 → 30 → 40
    assert set(encounter.memories) == {"darian"}
    assert encounter.state.player.fragmentos == 1
    memory = encounter.memories["darian"]
    assert memory.generated and memory.text == "Fogo e metal."
    assert [m.fragment.id for m in encounter.new_memories] == ["darian"]
    play(encounter, 10)
    assert set(encounter.memories) == {"darian", "a_batalha"}
    assert encounter.state.player.fragmentos == 2
    assert service.remember.call_count == 2


def test_fragment_failure_uses_labeled_fallback():
    service = ok_service()
    service.remember.return_value = DialogueResult(error=ERROR_MESSAGE)
    encounter = Encounter(service)
    play(encounter, 2, 8)
    memory = encounter.memories["o_medalhao"]
    assert not memory.generated
    assert memory.text == get_fragment("o_medalhao").fallback


def test_dialogue_failure_does_not_block_progress_and_retry_keeps_memories():
    service = ok_service()
    service.respond.side_effect = [DialogueResult(text="Quem é você?"), DialogueResult(error=ERROR_MESSAGE),
                                   DialogueResult(text="Agora sim.")]
    encounter = Encounter(service)
    play(encounter, 1, 5)
    assert not encounter.result.ok
    assert "a_batalha" in encounter.memories
    state = encounter.state
    assert encounter.retry()
    await_result(encounter)
    assert encounter.result.ok and encounter.state == state
    assert [m.fragment.id for m in encounter.new_memories] == ["a_batalha"]
    assert service.remember.call_count == 1
    play(encounter, 11)
    assert encounter.finished


def test_newly_unlocked_ignores_already_owned():
    state = replace(new_game(), npc=replace(new_game().npc, confianca_em_kael=50))
    assert [f.id for f in newly_unlocked(state, (), set())] == ["darian"]
    assert newly_unlocked(state, (), {"darian"}) == ()
    assert len(FRAGMENTS) == 4


@pytest.mark.parametrize("choices,title,fate", [
    ((3, 7, 9), "O Protetor", "levado para longe"),
    ((1, 6, 10), "O Implacável", "não confia mais"),
    ((2, 5, 11), "O Buscador", "hesita"),
    ((4, 8, 12), "O Sobrevivente", "ficou para trás"),
])
def test_endings(choices, title, fate):
    state = new_game()
    for choice_id in choices:
        state = apply_choice(state, choice_id)
    ending = compute_ending(state, choices[-1])
    assert ending.titulo == title
    assert fate in ending.destino_darian


def test_fragment_prompt_and_validation():
    client = MagicMock(spec=OpenAIClient)
    client.generate.return_value = "O céu ardia. Ouvi metal. Senti perda. Algo morreu em mim."
    fragment = get_fragment("a_batalha")
    result = DialogueService(client).remember(new_game(), fragment)
    assert result.ok
    prompt = client.generate.call_args.args[0]
    assert "quatro frases" in prompt.instructions
    context = json.loads(prompt.context)
    assert context["fragmento"] == "A Batalha"
    assert "não revele quem causou" in context["tema"]
    client.generate.return_value = "Um. Dois. Três. Quatro. Cinco."
    assert not DialogueService(client).remember(new_game(), fragment).ok


def test_dialogue_prompt_includes_round_and_history():
    history = ({"acao": "Kael decidiu ajudar Darian.", "fala_de_darian": "Obrigado."},)
    state = apply_choice(apply_choice(new_game(), 3), 7)
    data = json.loads(PromptBuilder().build(state, get_choice(7), history).context)
    assert data["rodada"] == 2
    assert data["historico"] == list(history)
    assert "histórico" in PromptBuilder().build(state, get_choice(7)).instructions
