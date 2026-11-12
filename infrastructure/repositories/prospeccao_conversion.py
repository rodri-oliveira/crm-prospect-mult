from __future__ import annotations
from database import get_db_connection

def convert_prospect(prospeccao_id: int, db_path) -> int | None:
    """Convert once, atomically: lead, segments, source link and history."""
    from contextlib import closing
    with closing(get_db_connection(db_path)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        c = conn.cursor()
        # Buscar dados da prospecção
        c.execute("SELECT * FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        row = c.fetchone()
        if not row:
            return None
        prospeccao = dict(row)
        # Se já foi convertido, apenas retornar o ID
        if prospeccao.get("convertido_lead_id"):
            lead_id = prospeccao["convertido_lead_id"]
            c.execute('UPDATE leads SET status = ? WHERE id = ?', (prospeccao.get('status_prospeccao') or 'Novo Lead', lead_id))

            # Garantir que está arquivado
            if not prospeccao.get("arquivado"):
                c.execute("UPDATE prospeccao_temp SET arquivado = 1 WHERE id = ?", (prospeccao_id,))

            return lead_id
        # Mapear dados para o novo lead
        nome = (prospeccao.get("nome_loja") or "").strip()
        cidade = (prospeccao.get("cidade") or "").strip()
        estado = (prospeccao.get("estado") or "").strip()
        cnpj = (prospeccao.get("cnpj") or "").strip()
        telefone = (prospeccao.get("telefone") or "").strip()
        whatsapp = (prospeccao.get("whatsapp") or "").strip()
        endereco = (prospeccao.get("endereco") or "").strip()
        segmento = (prospeccao.get("segmento") or "").strip()
        observacao = (prospeccao.get("observacao") or "").strip()
        maps_place_id = (prospeccao.get("maps_place_id") or "").strip()
        maps_url = (prospeccao.get("maps_url") or "").strip()
        site = (prospeccao.get("site") or "").strip()
        responsavel = (prospeccao.get("responsavel") or "").strip()
        email = (prospeccao.get("email") or "").strip()
        # Inserir na tabela de leads
        c.execute(
            """
            INSERT INTO leads (nome_loja, cidade, estado, cnpj, telefone, whatsapp, endereco, status, observacoes, maps_place_id, maps_url, site, responsavel, email, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'))
        """,
            (
                nome,
                cidade or None,
                estado or None,
                cnpj or None,
                telefone or None,
                whatsapp or None,
                endereco or None,
                prospeccao.get("status_prospeccao") if prospeccao.get("status_prospeccao") in ("Interessado", "Em negociação") else "Novo Lead",
                observacao or None,
                maps_place_id or None,
                maps_url or None,
                site or None,
                responsavel or None,
                email or None,
            ),
        )
        lead_id = c.lastrowid
        # Inserir segmentos na tabela segmentos_loja
        if segmento and lead_id:
            segmentos_list = [s.strip() for s in segmento.split(",") if s.strip()]
            for seg in segmentos_list:
                c.execute(
                    "INSERT INTO segmentos_loja (lead_id, segmento) VALUES (?, ?)",
                    (lead_id, seg),
                )
        # Atualizar prospecção como convertida e arquivada
        c.execute(
            "UPDATE prospeccao_temp SET convertido_lead_id = ?, arquivado = 1 WHERE id = ?",
            (lead_id, prospeccao_id),
        )
        # Migrar histórico de eventos para a tabela contatos do lead
        c.execute("SELECT * FROM prospeccao_eventos WHERE prospeccao_id = ?", (prospeccao_id,))
        eventos = c.fetchall()
        for ev in eventos:
            detalhe = ev['detalhe'] or ""
            # Tentar separar resultado de observação se houver "|"
            if " | " in detalhe:
                res, obs = detalhe.split(" | ", 1)
            else:
                res, obs = detalhe, ""

            c.execute(
                """
                INSERT INTO contatos (lead_id, data, tipo_contato, resultado, observacao)
                VALUES (?, ?, ?, ?, ?)
            """,
                (lead_id, ev['data_evento'], "Prospecção", res, obs),
            )
        if prospeccao.get('data_retorno'):
            c.execute('INSERT INTO contatos (lead_id, tipo_contato, resultado, observacao, data_retorno, hora_retorno) VALUES (?, ?, ?, ?, ?, ?)',
                      (lead_id, 'Prospecção', 'Agendar retorno', 'Retorno preservado na conversão', prospeccao['data_retorno'], prospeccao.get('hora_retorno')))
        return lead_id
