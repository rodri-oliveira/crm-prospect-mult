from __future__ import annotations
import os
from datetime import datetime


def _row_get(row, key: str, default: str = ""):
    if row is None:
        return default
    try:
        val = row[key]
    except Exception:
        return default
    return default if val is None else val


def _fmt_cnpj(val: str) -> str:
    s = '' if val is None else str(val)
    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) != 14:
        return s
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def save_pdf_copy(pdf_bytes: bytes, export_dir: str, filename: str) -> str:
    """Salva cópia do PDF em diretório de exportação."""
    os.makedirs(export_dir, exist_ok=True)
    path = os.path.join(export_dir, filename)
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    return path


def default_pdf_filename(data_inicio: str, data_fim: str) -> str:
    """Gera nome padrão para arquivo PDF."""
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if data_inicio == data_fim:
        return f"relatorio_{data_inicio}_{stamp}.pdf"
    return f"relatorio_{data_inicio}_a_{data_fim}_{stamp}.pdf"
