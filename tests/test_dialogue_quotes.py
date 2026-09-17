from game.systems.dialogue import validate_response


def test_two_sentences_in_outer_quotes_from_real_response():
    text = "Pare… não sei se devo confiar em você, Kael. Mas se realmente veio me ajudar, estanque o sangue e não faça movimentos bruscos."
    assert validate_response(f"“{text}”") == text
