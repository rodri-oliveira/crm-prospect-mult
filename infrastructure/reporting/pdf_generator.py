"""Compatibility exports for report generation."""
from infrastructure.reporting.complete import build_relatorio_pdf_bytes
from infrastructure.reporting.prospecting import build_relatorio_prospeccao_pdf_bytes
from infrastructure.reporting.common import default_pdf_filename, save_pdf_copy

__all__ = ["build_relatorio_pdf_bytes", "build_relatorio_prospeccao_pdf_bytes", "default_pdf_filename", "save_pdf_copy"]
