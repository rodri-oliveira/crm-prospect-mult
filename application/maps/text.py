from __future__ import annotations

import unicodedata


def _norm_key(v: str) -> str:
    s = (v or "").strip().casefold()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())

def _re_sub_ignoring_case(pattern: str, repl: str, text: str) -> str:
    import re

    return re.sub(pattern, repl, text, flags=re.IGNORECASE)
