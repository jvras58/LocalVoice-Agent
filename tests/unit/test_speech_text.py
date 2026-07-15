"""Testes da normalização aplicada antes da interface e do Piper."""

from src.core.speech_text import normalize_for_speech


def test_removes_markdown_and_asterisks() -> None:
    result = normalize_for_speech("**Olá!** *Estou pensando.* `teste`")
    assert result == "Olá! Estou pensando. teste"
    assert "*" not in result
    assert "`" not in result


def test_flattens_lists_links_and_emojis() -> None:
    text = "# Resultado\n- Veja [a documentação](https://example.com) ✅\n2. Pronto"
    assert normalize_for_speech(text) == "Resultado Veja a documentação Pronto"


def test_handles_empty_values() -> None:
    assert normalize_for_speech(None) == ""
    assert normalize_for_speech("   ") == ""
