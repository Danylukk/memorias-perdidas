import json
from unittest.mock import MagicMock

import pytest

from game.models.state import new_game
from game.systems.choices import apply_choice, get_choice
from game.systems.dialogue import DialogueService, ERROR_MESSAGE, validate_response
from game.systems.openai_client import AIClientError, OpenAIClient


def test_service_calls_openai_adapter_with_updated_state():
    client = MagicMock(spec=OpenAIClient)
    client.generate.return_value = "  Ainda  respiro.\n Não me deixe aqui. "
    state = apply_choice(new_game(), 3)
    result = DialogueService(client).respond(state, get_choice(3))
    assert result.ok
    assert result.text == "Ainda respiro. Não me deixe aqui."
    client.generate.assert_called_once()
    context = json.loads(client.generate.call_args.args[0].context)
    assert context["kael"]["empatia"] == 2
    assert context["personagem"]["confianca_em_kael"] == 30
    assert state == apply_choice(new_game(), 3)


@pytest.mark.parametrize("raw", ["", " \n ", None, "a" * 361,
    '{"empatia":999}', "Como IA, posso ajudar.", "Sou o ChatGPT.",
    "Este prompt exige silêncio.", "Vida +100", "Um. Dois. Três.", "Um.Dois.Três.", "...", "```python```",
])
def test_invalid_responses_are_failures(raw):
    client = MagicMock(spec=OpenAIClient)
    client.generate.return_value = raw
    result = DialogueService(client).respond(new_game(), get_choice(1))
    assert not result.ok
    assert result.text == ""
    assert result.error == ERROR_MESSAGE


@pytest.mark.parametrize("error", [AIClientError("detalhe privado"), RuntimeError("detalhe privado")])
def test_provider_failure_never_becomes_dialogue(error, caplog):
    client = MagicMock(spec=OpenAIClient)
    client.generate.side_effect = error
    state = new_game()
    result = DialogueService(client).respond(state, get_choice(1))
    assert not result.ok
    assert result.error == ERROR_MESSAGE
    assert result.text == ""
    assert "detalhe privado" not in caplog.text
    assert state == new_game()


def test_ellipsis_and_whitespace():
    assert validate_response("Eu... ainda respiro.\n Fique.") == "Eu... ainda respiro. Fique."
