"""Mecânicas da CP5: conversa em turnos com opções geradas, fragmentos, desfecho e fallback."""
import json
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from game.config import Settings
from game.models.state import new_game
from game.systems.choices import (CHOICES, INTENTS, ROUND_2, TOTAL_TURNS, apply_choice, apply_effects,
                                  choice_from_intent, fallback_options, get_choice)
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE, parse_turn
from game.systems.encounter import Encounter
from game.systems.ending import compute_ending
from game.systems.fragments import FRAGMENTS, get_fragment, newly_unlocked
from game.systems.openai_client import OpenAIClient
from game.systems.prompt_builder import PromptBuilder, TURN_SCHEMA


def turn_json(fala="Você acordou mesmo... Achei que tinha morrido.",
              intents=("curiosidade", "empatia", "lealdade", "agressividade")):
    return json.dumps({"fala": fala, "opcoes": [
        {"texto": f"Opção de {intent}", "intencao": intent} for intent in intents]})


def await_result(encounter):
    deadline = time.monotonic() + 3
    while encounter.generation_in_progress and time.monotonic() < deadline:
        encounter.update()
        time.sleep(0.001)
    assert not encounter.generation_in_progress


def pick(encounter, intent):
    """Escolhe a opção atual com a intenção pedida."""
    choice = next(c for c in encounter.current_choices if c.intent == intent)
    assert encounter.choose(choice.id)
    await_result(encounter)
    return choice


def generated_options(turn, intents=("curiosidade", "empatia", "lealdade", "agressividade")):
    return tuple(choice_from_intent(1000 + turn * 10 + i, f"Opção {turn}-{intent}", intent)
                 for i, intent in enumerate(intents))


def ai_service(intents=("curiosidade", "empatia", "lealdade", "agressividade")):
    service = MagicMock()
    turn = iter(range(1, 10))
    service.converse.side_effect = lambda state, choice, history, first_id: DialogueResult(
        text="Fique comigo.", options=generated_options(next(turn), intents))
    service.respond.return_value = DialogueResult(text="Adeus, Kael.")
    service.remember.return_value = DialogueResult(text="Fogo e metal.")
    return service


def test_intent_effects_are_fixed_in_python():
    assert set(INTENTS) == {"curiosidade", "empatia", "lealdade", "agressividade", "egoismo"}
    state = apply_effects(new_game(), choice_from_intent(1, "Chega de rodeios.", "agressividade"))
    assert state.player.agressividade == 1
    assert state.player.vida == 95
    assert state.npc.confianca_em_kael == 10


def test_fixed_and_fallback_options():
    assert fallback_options(1) == CHOICES
    assert fallback_options(2) == ROUND_2
    for turn in range(3, TOTAL_TURNS + 1):
        options = fallback_options(turn)
        assert len(options) == 4
        assert len({c.intent for c in options}) == 4
        assert all(c.fallback for c in options)


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
        state = apply_choice(state, 4)
    assert state.npc.confianca_em_kael == 0
    for _ in range(8):
        state = apply_choice(state, 7)
    assert state.player.energia == 0


def test_conversation_uses_generated_options_and_ends_after_five_turns():
    service = ai_service()
    encounter = Encounter(service)
    assert encounter.current_choices == CHOICES
    assert encounter.choose(3)
    await_result(encounter)
    assert encounter.options_generated
    assert encounter.current_choices == generated_options(1)
    assert not encounter.choose(1)  # opção fixa do turno 1 não vale mais
    for _ in range(TOTAL_TURNS - 1):
        pick(encounter, "empatia")
    assert encounter.finished
    assert encounter.current_choices == ()
    assert service.converse.call_count == TOTAL_TURNS - 1
    service.respond.assert_called_once()  # último turno: só a fala final
    history = service.respond.call_args.args[2]
    assert len(history) == TOTAL_TURNS - 1
    assert history[1]["acao"] == 'Kael respondeu: "Opção 1-empatia"'


def test_failed_turn_falls_back_to_fixed_options_and_continues():
    service = ai_service()
    service.converse.side_effect = lambda *args: DialogueResult(error=ERROR_MESSAGE)
    encounter = Encounter(service)
    assert encounter.choose(1)
    await_result(encounter)
    assert not encounter.result.ok
    assert encounter.current_choices == ROUND_2
    pick(encounter, "curiosidade")
    assert encounter.current_choices == fallback_options(3)
    for _ in range(TOTAL_TURNS - 2):
        encounter.choose(encounter.current_choices[0].id)
        await_result(encounter)
    assert encounter.finished


def test_retry_after_failure_brings_generated_options():
    service = ai_service()
    results = iter([DialogueResult(error=ERROR_MESSAGE),
                    DialogueResult(text="Agora sim.", options=generated_options(1))])
    service.converse.side_effect = lambda *args: next(results)
    encounter = Encounter(service)
    encounter.choose(3)
    await_result(encounter)
    state = encounter.state
    assert encounter.retry()
    await_result(encounter)
    assert encounter.result.ok and encounter.state == state
    assert encounter.current_choices == generated_options(1)


def test_fragments_unlocked_by_python_and_text_by_ai():
    service = ai_service()
    encounter = Encounter(service)
    encounter.choose(3)  # confiança 30
    await_result(encounter)
    pick(encounter, "lealdade")  # 35
    assert encounter.memories == {}
    pick(encounter, "lealdade")  # 40 e lealdade 3
    assert set(encounter.memories) == {"darian", "o_medalhao"}
    assert encounter.state.player.fragmentos == 2
    assert all(m.generated and m.text == "Fogo e metal." for m in encounter.memories.values())
    assert service.remember.call_count == 2


def test_fragment_failure_uses_labeled_fallback():
    service = ai_service()
    service.remember.return_value = DialogueResult(error=ERROR_MESSAGE)
    encounter = Encounter(service)
    encounter.choose(1)
    await_result(encounter)
    pick(encounter, "agressividade")
    pick(encounter, "agressividade")
    memory = encounter.memories["maos_manchadas"]
    assert not memory.generated
    assert memory.text == get_fragment("maos_manchadas").fallback


def test_newly_unlocked_ignores_already_owned():
    state = replace(new_game(), npc=replace(new_game().npc, confianca_em_kael=50))
    assert [f.id for f in newly_unlocked(state, set())] == ["darian"]
    assert newly_unlocked(state, {"darian"}) == ()
    assert len(FRAGMENTS) == 4


@pytest.mark.parametrize("choice_ids,intent,title,fate", [
    ((3, 7), "lealdade", "O Protetor", "levado para longe"),
    ((1, 6), "agressividade", "O Implacável", "não confia mais"),
    ((2, 5), "curiosidade", "O Buscador", "hesita"),
    ((4,), "egoismo", "O Sobrevivente", "ficou para trás"),
])
def test_endings(choice_ids, intent, title, fate):
    state = new_game()
    for choice_id in choice_ids:
        state = apply_choice(state, choice_id)
    ending = compute_ending(state, intent)
    assert ending.titulo == title
    assert fate in ending.destino_darian


def test_parse_turn_validates_structure():
    result = parse_turn(turn_json(), 1010)
    assert result.ok
    assert [c.id for c in result.options] == [1010, 1011, 1012, 1013]
    assert result.options[3].intent == "agressividade"
    bad = [
        "não é json",
        turn_json(intents=("curiosidade", "empatia", "lealdade")),
        turn_json(intents=("curiosidade", "empatia", "lealdade", "matar")),
        turn_json(fala="Sou o ChatGPT."),
        json.dumps({"fala": "Fique.", "opcoes": [{"texto": "a" * 81, "intencao": "empatia"}] * 4}),
        json.dumps({"fala": "Fique.", "opcoes": [{"texto": "Igual", "intencao": "empatia"}] * 4}),
    ]
    for raw in bad:
        with pytest.raises(Exception):
            parse_turn(raw, 1010)


def test_turn_prompt_schema_and_rules():
    history = ({"acao": "Kael decidiu ajudar Darian.", "fala_de_darian": "Obrigado."},)
    state = apply_choice(new_game(), 3)
    prompt = PromptBuilder().build_turn(state, get_choice(3), history)
    data = json.loads(prompt.context)
    assert data["rodada"] == 2
    assert data["turnos_restantes"] == TOTAL_TURNS - 2
    assert data["historico"] == list(history)
    assert prompt.schema == TURN_SCHEMA
    assert "exatamente 4" in prompt.instructions and "Não invente" in prompt.instructions
    assert TURN_SCHEMA["properties"]["opcoes"]["items"]["properties"]["intencao"]["enum"] == list(INTENTS)


def test_openai_client_sends_json_schema(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("game.systems.openai_client.OpenAI", factory)
    monkeypatch.setattr(Settings, "validate", lambda self: None)
    sdk = factory.return_value.__enter__.return_value
    sdk.responses.create.return_value = SimpleNamespace(status="completed", output_text=turn_json())
    prompt = PromptBuilder().build_turn(new_game(), get_choice(1))
    result = DialogueService(OpenAIClient(Settings(model="m"))).converse(new_game(), get_choice(1), (), 1010)
    assert result.ok and len(result.options) == 4
    kwargs = sdk.responses.create.call_args.kwargs
    assert kwargs["text"]["format"]["type"] == "json_schema"
    assert kwargs["text"]["format"]["strict"] is True
    assert kwargs["max_output_tokens"] == prompt.max_output_tokens


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
