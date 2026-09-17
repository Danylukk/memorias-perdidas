import json
from dataclasses import replace

from game.models.state import new_game
from game.systems.choices import apply_choice, get_choice
from game.systems.prompt_builder import PromptBuilder


def test_updated_context_and_rules():
    state = apply_choice(new_game(), 3)
    prompt = PromptBuilder().build(state, get_choice(3))
    data = json.loads(prompt.context)
    assert data["kael"]["empatia"] == 2
    assert data["kael"]["lealdade"] == 1
    assert data["personagem"]["confianca_em_kael"] == 30
    assert data["acao_do_jogador"] == "Kael decidiu ajudar Darian."
    assert data["personagem"]["personalidade"] == ["disciplinado", "desconfiado", "leal"]
    assert data["personagem"]["estado"] == "gravemente ferido"
    assert data["situacao"] == state.situacao
    assert data["revelacao"]["pode_revelar_passado"] is False
    assert data["revelacao"]["topicos_bloqueados"] == list(state.npc.segredos)
    for rule in ("Não invente", "Não altere atributos", "Não desbloqueie", "false",
                 "duas frases", "português do Brasil", "ChatGPT"):
        assert rule in prompt.instructions


def test_private_knowledge_never_enters_prompt():
    state = new_game()
    private_fact = "FATO PRIVADO DE TESTE QUE NÃO PODE SAIR"
    state = replace(state, npc=replace(
        state.npc, informacoes_conhecidas=state.npc.informacoes_conhecidas + (private_fact,),
        informacoes_permitidas=state.npc.informacoes_permitidas + ("FATO DESCONHECIDO",),
    ))
    prompt = PromptBuilder().build(state, get_choice(2))
    assert private_fact not in prompt.context
    assert "FATO DESCONHECIDO" not in prompt.context
    assert "informacoes_conhecidas" not in prompt.context
    assert json.loads(prompt.context)["revelacao"]["pode_revelar_passado"] is False
