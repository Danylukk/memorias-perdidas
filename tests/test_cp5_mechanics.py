"""Mecânicas da CP5 fiéis à CP4: conversa com opções geradas, roteiro ramificado, exploração,
fragmentos, Lira, decisão final e save/continuar."""
import json
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from game.config import Settings
from game.models.state import initial_player, load_npc, new_game
from game.systems import save
from game.systems.choices import (CHOICES, CP4_ACTIONS, INTENTS, apply_choice, apply_effects, choice_from_dict,
                                  choice_from_intent, choice_to_dict, get_choice)
from game.systems.dialogue import DialogueResult, DialogueService, ERROR_MESSAGE, parse_turn
from game.systems.encounter import Encounter
from game.systems.ending import DECISIONS, compute_ending
from game.systems.fragments import FRAGMENTS, Memory, get_fragment, newly_unlocked
from game.systems.journey import DARIAN_OUTCOMES, HOTSPOTS, Journey, darian_outcome, load_gallery, load_progress
from game.systems.openai_client import OpenAIClient
from game.systems.prompt_builder import PromptBuilder, TURN_SCHEMA
from game.systems.script import BRANCH_OF_INTENT, load_script, opening, scripted_turn, total_turns


def turn_json(fala="Você acordou mesmo... Achei que tinha morrido.",
              intents=("curiosidade", "empatia", "lealdade", "agressividade")):
    return json.dumps({"fala": fala, "opcoes": [
        {"texto": f"Opção {intent}", "intencao": intent} for intent in intents]})


def settle(target):
    """Aguarda o worker de uma conversa ou da jornada."""
    deadline = time.monotonic() + 3
    busy = (lambda: target.busy) if isinstance(target, Journey) else (lambda: target.generation_in_progress)
    while busy() and time.monotonic() < deadline:
        target.update()
        time.sleep(0.001)
    target.update()
    assert not busy()


def pick(encounter, intent, journey=None):
    choice = next(c for c in encounter.current_choices if c.intent == intent)
    assert encounter.choose(choice.id)
    settle(journey or encounter)
    return choice


def generated_options(turn, intents=("curiosidade", "empatia", "lealdade", "agressividade")):
    return tuple(choice_from_intent(1000 + turn * 10 + i, f"Opção {turn}-{intent}", intent)
                 for i, intent in enumerate(intents))


def ai_service():
    service = MagicMock()
    turns = iter(range(1, 50))
    service.converse.side_effect = lambda *args: DialogueResult(text="Fique comigo.",
                                                                options=generated_options(next(turns)))
    service.respond.return_value = DialogueResult(text="Vá, Kael.")
    service.remember.return_value = DialogueResult(text="Fogo e metal.")
    return service


# --- Personagens e dados da CP4 ---

def test_three_characters_from_cp4():
    darian, lira = load_npc("darian"), load_npc("lira")
    assert (darian.nome, darian.papel, darian.confianca_em_kael) == ("Darian", "soldado", 20)
    assert (lira.nome, lira.papel) == ("Lira", "curandeira")
    assert lira.conhece_kael and not lira.pode_revelar_passado
    assert "Você conhece Kael, mas evita revelar tudo o que sabe sobre ele." in lira.informacoes_permitidas
    assert initial_player().nome == "Kael"


def test_fragments_are_the_ones_in_the_mockup():
    assert [f.titulo for f in FRAGMENTS] == ["A Batalha", "A Ordem de Arkan", "Lira", "Darian"]
    assert {f.origem for f in FRAGMENTS} == {"local", "objeto", "personagem"}
    batalha = get_fragment("a_batalha")
    assert batalha.fallback.startswith("O céu estava em chamas.")  # texto do teste real da CP4
    assert batalha.descricao.startswith("A batalha que mudou tudo.")  # texto do mockup


def test_cp4_table_effects():
    threatened = apply_choice(new_game(), 6)
    assert threatened.player.agressividade == 2
    assert threatened.player.empatia == 0  # limitado a 0
    assert threatened.npc.confianca_em_kael == 5
    helped = apply_choice(new_game(), 3)
    assert (helped.player.empatia, helped.player.lealdade) == (2, 1)
    assert apply_choice(new_game(), 5).player.curiosidade == 2


def test_intent_effects_and_limits():
    assert set(INTENTS) == {"curiosidade", "empatia", "lealdade", "agressividade", "egoismo"}
    state = apply_effects(new_game(), choice_from_intent(1, "Chega de rodeios.", "agressividade"))
    assert (state.player.agressividade, state.player.vida, state.npc.confianca_em_kael) == (1, 95, 10)
    for _ in range(25):
        state = apply_effects(state, choice_from_intent(0, "Deixe-me ajudar.", "empatia"))
    assert state.player.energia == 0 and state.npc.confianca_em_kael == 100


def test_choice_serialization_roundtrip():
    for choice in CHOICES + CP4_ACTIONS + (choice_from_intent(9, "Oi", "lealdade"),):
        assert choice_from_dict(json.loads(json.dumps(choice_to_dict(choice)))) == choice


# --- Roteiro offline ramificado ---

def test_offline_script_is_complete_for_both_characters():
    script = load_script()
    assert set(script) == {"darian", "lira"}
    assert (total_turns("darian"), total_turns("lira")) == (5, 3)
    assert opening("darian") == ("Você... está vivo?", CHOICES)
    for npc_id in script:
        line, choices = opening(npc_id)
        assert line and len(choices) == 4
        last = total_turns(npc_id)
        for turn in range(1, last + 1):
            branches = script[npc_id]["turnos"][str(turn)]
            if turn > 1 or npc_id == "lira":
                assert set(branches) == set(BRANCH_OF_INTENT.values()), (npc_id, turn)
            for branch in branches:
                intent = next(i for i, b in BRANCH_OF_INTENT.items() if b == branch)
                result = scripted_turn(turn, choice_from_intent(0, "x", intent), npc_id)
                assert result.text and result.source == "roteiro"
                if turn == last:
                    assert result.options == ()
                else:
                    assert len(result.options) == 4 and len({c.intent for c in result.options}) == 4
                    assert all(0 < len(c.label) <= 30 for c in result.options), (npc_id, turn, branch)


def test_offline_follows_the_chosen_path_without_calling_the_api():
    service = MagicMock()
    helped, left = Encounter(service, offline=True), Encounter(service, offline=True)
    helped.choose(3)
    left.choose(4)
    settle(helped)
    settle(left)
    assert (helped.branch, left.branch) == ("cuidado", "abandono")
    assert helped.result.text == get_choice(3).fallback
    assert [c.label for c in helped.current_choices] != [c.label for c in left.current_choices]
    assert not helped.retry()
    pick(helped, "agressividade")
    assert helped.branch == "confronto"
    assert helped.result.text == load_script()["darian"]["turnos"]["2"]["confronto"]["fala"]
    service.converse.assert_not_called()
    service.respond.assert_not_called()


def test_cp4_actions_are_offered_by_the_script():
    options = scripted_turn(1, get_choice(1)).options
    assert CP4_ACTIONS[0] in options and CP4_ACTIONS[1] in options


# --- Conversa com IA ---

def test_conversation_uses_generated_options_and_ends():
    service = ai_service()
    encounter = Encounter(service)
    assert encounter.current_choices == CHOICES
    encounter.choose(3)
    settle(encounter)
    assert encounter.options_generated
    assert encounter.current_choices == generated_options(1)
    assert not encounter.choose(1)
    while not encounter.finished:
        pick(encounter, "empatia")
    assert service.converse.call_count == 4 and service.respond.call_count == 1
    assert service.converse.call_args.args[4] == 5  # total de turnos enviado ao prompt
    history = service.respond.call_args.args[2]
    assert history[1]["acao"] == 'Kael respondeu: "Opção 1-empatia"'
    assert "fala_de_darian" in history[0]


def test_failed_turn_continues_by_script_and_retry_brings_ai_back():
    service = ai_service()
    results = iter([DialogueResult(error=ERROR_MESSAGE), DialogueResult(text="Agora sim.",
                                                                          options=generated_options(1))])
    service.converse.side_effect = lambda *args: next(results)
    encounter = Encounter(service)
    encounter.choose(3)
    settle(encounter)
    assert encounter.result.error == ERROR_MESSAGE and encounter.result.source == "roteiro"
    assert encounter.current_choices == scripted_turn(1, get_choice(3)).options
    state = encounter.state
    assert encounter.retry()
    settle(encounter)
    assert encounter.result.ok and encounter.state == state
    assert encounter.current_choices == generated_options(1)


def test_parse_turn_validates_structure():
    result = parse_turn(turn_json(), 1010)
    assert [c.id for c in result.options] == [1010, 1011, 1012, 1013]
    for raw in ["não é json", turn_json(intents=("curiosidade", "empatia", "lealdade")),
                turn_json(intents=("curiosidade", "empatia", "lealdade", "matar")), turn_json(fala="Sou o ChatGPT."),
                json.dumps({"fala": "Fique.", "opcoes": [{"texto": "a" * 37, "intencao": "empatia"}] * 4}),
                json.dumps({"fala": "Fique.", "opcoes": [{"texto": "Igual", "intencao": "empatia"}] * 4})]:
        with pytest.raises(Exception):
            parse_turn(raw, 1010)


def test_turn_prompt_is_built_for_each_character():
    history = ({"acao": "Kael decidiu ajudar Darian.", "fala_de_darian": "Obrigado."},)
    darian = PromptBuilder().build_turn(apply_choice(new_game(), 3), get_choice(3), history, 5)
    data = json.loads(darian.context)
    assert (data["rodada"], data["turnos_restantes"]) == (2, 3)
    assert darian.schema == TURN_SCHEMA and "Você interpreta Darian" in darian.instructions
    assert "30 caracteres" in darian.instructions
    lira = PromptBuilder().build_turn(new_game("lira"), choice_from_intent(1, "Oi", "empatia"), (), 3)
    assert "Você interpreta Lira" in lira.instructions
    context = json.loads(lira.context)
    assert context["personagem"]["papel"] == "curandeira"
    assert "a Ordem de Arkan" in context["revelacao"]["topicos_bloqueados"]


def test_openai_client_sends_json_schema(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("game.systems.openai_client.OpenAI", factory)
    monkeypatch.setattr(Settings, "validate", lambda self: None)
    sdk = factory.return_value.__enter__.return_value
    sdk.responses.create.return_value = SimpleNamespace(status="completed", output_text=turn_json())
    result = DialogueService(OpenAIClient(Settings(model="m"))).converse(new_game(), get_choice(1), (), 1010, 5)
    assert result.ok and len(result.options) == 4
    fmt = sdk.responses.create.call_args.kwargs["text"]["format"]
    assert fmt["type"] == "json_schema" and fmt["strict"] is True


# --- Fragmentos ---

def test_character_fragments_unlock_by_trust():
    state = replace(new_game(), npc=replace(new_game().npc, confianca_em_kael=40))
    assert [f.id for f in newly_unlocked(state, set())] == ["darian"]
    assert newly_unlocked(state, {"darian"}) == ()
    lira = new_game("lira")
    assert newly_unlocked(replace(lira, npc=replace(lira.npc, confianca_em_kael=44)), set()) == ()
    assert [f.id for f in newly_unlocked(replace(lira, npc=replace(lira.npc, confianca_em_kael=45)), set())] == ["lira"]


def test_fragment_prompt_and_validation():
    client = MagicMock(spec=OpenAIClient)
    client.generate.return_value = "Velas acesas. Figuras encapuzadas. Uma cruz dourada. Um juramento."
    result = DialogueService(client).remember(new_game(), get_fragment("ordem_de_arkan"))
    assert result.ok
    prompt = client.generate.call_args.args[0]
    assert "quatro frases" in prompt.instructions
    assert json.loads(prompt.context)["fragmento"] == "A Ordem de Arkan"
    client.generate.return_value = "Um. Dois. Três. Quatro. Cinco."
    assert not DialogueService(client).remember(new_game(), get_fragment("a_batalha")).ok


# --- Jornada completa: Darian → exploração → Lira → decisão ---

def play_darian(service, offline, intent="empatia"):
    journey = Journey(service, offline)
    encounter = journey.encounter
    encounter.choose(3)
    settle(journey)
    while not encounter.finished:
        choices = encounter.current_choices
        choice = next((c for c in choices if c.intent == intent), choices[0])
        encounter.choose(choice.id)
        settle(journey)
    return journey


def test_full_journey_offline():
    service = MagicMock()
    journey = play_darian(service, offline=True)
    assert journey.phase == "darian" and journey.conversation_over
    assert "darian" in journey.memories  # confiança de Darian chegou a 40
    assert journey.advance() and journey.phase == "exploracao"
    energy = journey.player.energia
    assert journey.interact("estandarte")
    settle(journey)
    memory = journey.memories["ordem_de_arkan"]
    assert not memory.generated and memory.text == get_fragment("ordem_de_arkan").fallback
    assert journey.message.heading == "Memória recuperada — A Ordem de Arkan"
    assert journey.player.energia == energy - 5
    assert journey.interact("estandarte")  # investigar de novo não repete o fragmento
    assert not journey.busy and journey.player.energia == energy - 5
    journey.interact("espadas")
    settle(journey)
    assert "a_batalha" in journey.memories
    assert journey.interact("lira") and journey.phase == "lira"
    lira = journey.encounter
    assert lira.npc_id == "lira" and lira.state.player == journey.player
    for _ in range(3):
        pick(lira, next(c.intent for c in lira.current_choices if c.intent in ("empatia", "lealdade")), journey)
    assert lira.finished and "lira" in journey.memories
    assert journey.advance() and journey.phase == "decisao"
    assert not journey.decide("ninguem")
    assert journey.decide("ambos") and journey.phase == "fim"
    ending = journey.ending()
    assert ending.titulo in ("O Protetor", "O Companheiro")
    assert "reúne Darian e Lira" in ending.destino
    assert journey.player.fragmentos == len(journey.memories) == 4
    service.converse.assert_not_called()
    service.remember.assert_not_called()


def test_journey_with_ai_generates_memories():
    service = ai_service()
    journey = play_darian(service, offline=False)
    assert journey.memories["darian"].generated
    journey.advance()
    journey.interact("espadas")
    settle(journey)
    assert journey.memories["a_batalha"] == Memory(get_fragment("a_batalha"), "Fogo e metal.", True)
    assert journey.message.source == "ia"


def test_exploration_rules():
    journey = Journey(MagicMock(), offline=True)
    assert not journey.interact("estandarte")  # antes de terminar a conversa com Darian
    assert not journey.advance()
    assert [h.id for h in HOTSPOTS] == ["estandarte", "espadas", "darian", "soldado", "medalhao", "lira"]
    assert not journey.decide("darian")


@pytest.mark.parametrize("decision,trust,expected", [
    ("darian", {"darian": 30, "lira": 0}, "ao lado de Darian"),
    ("darian", {"darian": 10, "lira": 0}, "desvia o olhar"),
    ("lira", {"darian": 0, "lira": 40}, "parte com Lira"),
    ("ambos", {"darian": 50, "lira": 20}, "desconfiança"),
    ("sozinho", {"darian": 90, "lira": 90}, "sozinho"),
])
def test_endings(decision, trust, expected):
    player = replace(initial_player(), egoismo=3, empatia=1)
    ending = compute_ending(player, trust, decision)
    assert ending.titulo == "O Sobrevivente"
    assert expected in ending.destino
    assert [d for d, _ in DECISIONS] == ["darian", "lira", "ambos", "sozinho"]


# --- Save / Continuar ---

def test_progress_is_saved_and_continued():
    service = MagicMock()
    journey = play_darian(service, offline=True)
    journey.advance()
    journey.interact("estandarte")
    settle(journey)
    journey.persist()
    assert save.has_progress()
    loaded = load_progress(service, True)
    assert loaded.phase == "exploracao"
    assert loaded.player == journey.player
    assert loaded.memories == journey.memories
    assert loaded.trust("darian") == journey.trust("darian")
    assert set(load_gallery()) == {"darian", "ordem_de_arkan"}
    loaded.interact("lira")
    loaded.encounter.choose(loaded.encounter.current_choices[0].id)
    settle(loaded)
    loaded.persist()
    resumed = load_progress(service, True)
    assert resumed.phase == "lira" and resumed.encounter.round_index == 1
    assert resumed.encounter.current_choices == loaded.encounter.current_choices


def test_finished_journey_clears_progress_but_keeps_gallery():
    journey = play_darian(MagicMock(), offline=True)
    journey.persist()
    journey.advance()
    journey.interact("lira")
    while not journey.encounter.finished:
        journey.encounter.choose(journey.encounter.current_choices[0].id)
        settle(journey)
    journey.advance()
    journey.decide("sozinho")
    journey.persist()
    assert not save.has_progress()
    assert "darian" in load_gallery()


def test_corrupted_save_is_ignored():
    save.write(save.PROGRESS, {"phase": "darian"})
    assert load_progress(MagicMock(), True) is None
    save.write(save.GALLERY, {"x": {"fragment": "inexistente", "text": "", "generated": False}})
    assert load_gallery() == {}
    assert save.load_settings() == save.DEFAULT_SETTINGS


# --- Consequências entre cenas: Lira sabe o que Kael fez com Darian ---

def play_darian_path(first_choice, intent):
    journey = Journey(MagicMock(), offline=True)
    encounter = journey.encounter
    encounter.choose(first_choice)
    settle(journey)
    while not encounter.finished:
        choices = encounter.current_choices
        encounter.choose(next((c for c in choices if c.intent == intent), choices[0]).id)
        settle(journey)
    journey.advance()
    return journey


def test_lira_reacts_to_how_kael_treated_darian():
    helped = play_darian_path(3, "empatia")
    left = play_darian_path(4, "egoismo")
    assert (helped.darian_outcome, left.darian_outcome) == ("cuidado", "abandono")
    assert helped.trust("lira") == 40 and left.trust("lira") == 20  # 30 inicial ±10
    helped.interact("lira")
    left.interact("lira")
    assert helped.encounter.opening_line.startswith("Kael... Darian disse que você o ajudou.")
    assert left.encounter.opening_line.startswith("Então é verdade. Você ia deixar Darian morrer")
    assert helped.encounter.state.historia[0] == DARIAN_OUTCOMES["cuidado"][0]
    assert "Confiança de Darian" in helped.encounter.state.historia[1]
    context = json.loads(PromptBuilder().build(helped.encounter.state, get_choice(1)).context)
    assert context["historia_da_partida"] == list(helped.encounter.state.historia)
    assert "historia_da_partida" in PromptBuilder().build(helped.encounter.state, get_choice(1)).instructions
    assert json.loads(PromptBuilder().build(new_game(), get_choice(1)).context)["historia_da_partida"] == []


def test_darian_outcome_uses_predominant_path_and_survives_save():
    encounter = Encounter(MagicMock(), offline=True)
    assert darian_outcome(encounter) == "perguntas"
    encounter.choose(4)
    settle(encounter)
    pick(encounter, "agressividade")
    assert darian_outcome(encounter) == "confronto"  # empate: vale o mais recente
    journey = play_darian_path(1, "agressividade")
    journey.interact("lira")
    journey.persist()
    loaded = load_progress(MagicMock(), True)
    assert loaded.darian_outcome == journey.darian_outcome
    assert loaded.encounter.opening_line == journey.encounter.opening_line
    assert loaded.encounter.state.historia == journey.encounter.state.historia


def test_medallion_and_fallen_soldier_apply_once():
    journey = play_darian_path(3, "empatia")
    player = journey.player
    assert journey.interact("medalhao") and not journey.busy
    assert journey.player.curiosidade == player.curiosidade + 1
    journey.interact("medalhao")
    assert journey.player.curiosidade == player.curiosidade + 1
    journey.interact("soldado")
    journey.interact("soldado")
    assert journey.player.empatia == player.empatia + 1
    assert {"medalhao", "soldado"} <= journey.explored
    assert journey.message.heading == "Soldado caído"
