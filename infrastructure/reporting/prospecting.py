from __future__ import annotations
from io import BytesIO
from infrastructure.reporting.common import _row_get


def build_relatorio_prospeccao_pdf_bytes(relatorio: dict, data_inicio: str, data_fim: str) -> bytes:
    """Gera PDF do relatório de prospecção."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.0 * cm,
        title="Análise de Prospecção",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6,
        spaceBefore=10,
    )

    elements = []
    elements.append(Paragraph("ANÁLISE DE PROSPECÇÃO", title_style))
    elements.append(Paragraph(f"Período: {data_inicio} a {data_fim}", subtitle_style))

    total_geral = int(relatorio.get('total_geral', 0) or 0)
    total_tentativas = int(relatorio.get('total_tentativas', 0) or 0)
    total_convertidos = int(relatorio.get('total_convertidos', 0) or 0)
    taxa = 0.0
    if total_tentativas > 0:
        taxa = (total_convertidos / total_tentativas) * 100.0

    elements.append(Paragraph("Resumo", section_style))
    resumo_data = [
        ["Total", "Tentativas", "Convertidos", "Conversão"],
        [str(total_geral), str(total_tentativas), str(total_convertidos), f"{taxa:.1f}%"],
    ]
    resumo_table = Table(resumo_data, colWidths=[4.0 * cm] * 4)
    resumo_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('TOPPADDING', (0, 1), (-1, 1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ]
        )
    )
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.4 * cm))

    resumo_status = relatorio.get('resumo') or []
    elements.append(Paragraph("Resultados por Status", section_style))
    status_data = [["Status", "Total"]]
    for row in resumo_status:
        try:
            status = row['status_prospeccao']
            total = row['total']
        except Exception:
            try:
                status, total = row
            except Exception:
                continue
        status_data.append([str(status), str(total)])

    status_table = Table(status_data, colWidths=[14.0 * cm, 3.0 * cm], repeatRows=1)
    status_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(status_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Estilos para as células da tabela
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=8,
        alignment=0, # Left
    )
    cell_style_bold = ParagraphStyle(
        'CellStyleBold',
        parent=cell_style,
        fontSize=7,
        fontName='Helvetica-Bold',
        textColor=colors.white,
    )

    items = relatorio.get('items') or relatorio.get('detalhes_prospeccao') or []
    elements.append(Paragraph(f"Lista Detalhada ({len(items)})", section_style))

    # Cabeçalho com Paragraph para suportar quebra se necessário
    itens_data = [[
        Paragraph("Data", cell_style_bold),
        Paragraph("Loja", cell_style_bold),
        Paragraph("CNPJ", cell_style_bold),
        Paragraph("Cidade/UF", cell_style_bold),
        Paragraph("Segmento", cell_style_bold),
        Paragraph("Status", cell_style_bold),
        Paragraph("Retorno", cell_style_bold),
        Paragraph("Observação", cell_style_bold)
    ]]

    for item in items:
        cidade = str(_row_get(item, 'cidade', ''))
        uf = str(_row_get(item, 'estado', ''))
        cidade_uf = cidade
        if uf:
            cidade_uf = f"{cidade}/{uf}" if cidade else uf

        data_retorno = str(_row_get(item, 'data_retorno', ''))
        hora_retorno = str(_row_get(item, 'hora_retorno', ''))
        retorno = "-"
        if data_retorno:
            retorno = f"{data_retorno} {hora_retorno}" if hora_retorno else data_retorno
        observacao = str(_row_get(item, 'observacao', '')) or '-'

        itens_data.append([
            Paragraph(str(_row_get(item, 'data_prospeccao', '')), cell_style),
            Paragraph(str(_row_get(item, 'nome_loja', '')), cell_style),
            Paragraph(str(_row_get(item, 'cnpj', '') or '-'), cell_style),
            Paragraph(cidade_uf, cell_style),
            Paragraph(str(_row_get(item, 'segmento', '') or '-'), cell_style),
            Paragraph(str(_row_get(item, 'status_prospeccao', '')), cell_style),
            Paragraph(retorno, cell_style),
            Paragraph(observacao, cell_style)
        ])

    itens_table = Table(
        itens_data,
        colWidths=[1.4 * cm, 3.0 * cm, 2.0 * cm, 2.2 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 2.5 * cm],
        repeatRows=1
    )
    itens_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(itens_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
