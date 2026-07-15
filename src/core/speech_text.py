"""Normalização determinística de respostas destinadas à fala sintetizada."""

import html
import re
import unicodedata

_CODE_FENCE_RE = re.compile(r"```(?:[\w+-]+)?\s*(.*?)```", re.DOTALL)
_IMAGE_RE = re.compile(r"!\[([^]]*)]\([^)]+\)")
_LINK_RE = re.compile(r"\[([^]]+)]\([^)]+\)")
_LINE_PREFIX_RE = re.compile(r"^\s*(?:#{1,6}|>|[-+•]|\d+[.)])\s*")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_for_speech(value: object) -> str:
    """Converte uma saída possivelmente formatada em texto simples para TTS."""
    text = html.unescape(str(value or ""))
    text = _CODE_FENCE_RE.sub(r"\1", text)
    text = _IMAGE_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)

    lines: list[str] = []
    for raw_line in text.splitlines():
        line = _LINE_PREFIX_RE.sub("", raw_line).strip()
        if line:
            lines.append(line)
    text = " ".join(lines)

    text = text.replace("*", "").replace("`", "").replace("~", "")
    text = re.sub(r"_+", " ", text)
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) not in {"So", "Sk"}
    )
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()
