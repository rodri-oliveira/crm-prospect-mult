from __future__ import annotations
import sqlite3
from typing import Any
from infrastructure.repositories.prospect_filters import filter_where, register_filter_functions
from database import DB_PATH, get_db_connection
from domain.repositories.prospeccao_repository import ProspecctionSummary, ProspeccaoRepository
class SqliteProspeccaoRepository(ProspeccaoRepository):
    def get_by_id(self, prospeccao_id: int) -> dict | None:
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    def list_by_filters(
        self,
        status: str | None = None,
        nome: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        telefone: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        mostrar_arquivados: bool = False,
        tipo_telefone: str | None = None,
    ) -> list[dict]:
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        register_filter_functions(conn)
        where_clause, params = filter_where(
            status=status, nome=nome, segmento=segmento, cidade=cidade,
            estado=estado, telefone=telefone, data_inicio=data_inicio,
            data_fim=data_fim, mostrar_arquivados=mostrar_arquivados,
            tipo_telefone=tipo_telefone,
        )
        # Ordenacao: a ultima tabulacao/evento aparece sempre primeiro.
        tel_clean = "replace(replace(replace(replace(replace(p.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
        order_by = f"""
            COALESCE(ev.ultimo_evento, p.updated_at, p.data_criacao) DESC,
            CASE
                WHEN substr({tel_clean}, 3, 1) IN ('2', '3', '4', '5') THEN 1
                WHEN substr({tel_clean}, 3, 1) = '9' THEN 2
                ELSE 3
            END ASC,
            p.id DESC
        """
        query = f"""
            SELECT p.*
            FROM prospeccao_temp p
            LEFT JOIN (
                SELECT prospeccao_id, MAX(data_evento) AS ultimo_evento
                FROM prospeccao_eventos
                GROUP BY prospeccao_id
            ) ev ON ev.prospeccao_id = p.id
            WHERE {where_clause}
            ORDER BY {order_by}
        """

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    def get_summary(
        self,
        data_inicio: str | None,
        data_fim: str | None,
        mostrar_arquivados: bool = False,
        status: str | None = None,
        nome: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        telefone: str | None = None,
        tipo_telefone: str | None = None,
    ) -> ProspecctionSummary:
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        register_filter_functions(conn)
        where_clause, params = filter_where(
            status=status, nome=nome, segmento=segmento, cidade=cidade,
            estado=estado, telefone=telefone, data_inicio=data_inicio,
            data_fim=data_fim, mostrar_arquivados=mostrar_arquivados,
            tipo_telefone=tipo_telefone,
        )
        c.execute(f"SELECT COUNT(*) FROM prospeccao_temp WHERE {where_clause}", params)
        total = c.fetchone()[0]
        c.execute(
            f"SELECT status_prospeccao, COUNT(*) FROM prospeccao_temp WHERE {where_clause} GROUP BY status_prospeccao",
            params,
        )
        por_status = {row[0]: row[1] for row in c.fetchall()}
        # Buscar cidades únicas acionadas no período
        c.execute(
            f"SELECT DISTINCT cidade FROM prospeccao_temp WHERE {where_clause} AND cidade IS NOT NULL AND cidade != '' ORDER BY cidade",
            params,
        )
        cidades = [row[0] for row in c.fetchall()]
        conn.close()
        return ProspecctionSummary(total=total, por_status=por_status, cidades=cidades)
    def add(self, dados: dict) -> tuple[int, bool]:
        from infrastructure.repositories.prospeccao_creation import add_prospect
        return add_prospect(dados, DB_PATH)

    def update_status(
        self,
        prospeccao_id: int,
        novo_status: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
        clear_retorno: bool = False,
    ) -> bool:
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        fields = ["status_prospeccao = ?", "data_prospeccao = CURRENT_DATE", "updated_at = CURRENT_TIMESTAMP"]
        params: list[Any] = [novo_status]
        if observacao is not None:
            fields.append("observacao = ?")
            params.append(observacao)
        if data_retorno:
            fields.extend(["data_retorno = ?", "hora_retorno = ?"])
            params.extend([data_retorno, hora_retorno])
        elif clear_retorno:
            fields.extend(["data_retorno = NULL", "hora_retorno = NULL"])
        params.append(prospeccao_id)
        c.execute(f"UPDATE prospeccao_temp SET {', '.join(fields)} WHERE id = ?", params)
        affected = c.rowcount
        if affected > 0:
            detalhe = novo_status if not observacao else f"{novo_status} | {observacao}"
            c.execute(
                "INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe) VALUES (?, ?, ?)",
                (prospeccao_id, "STATUS_CHANGE", detalhe),
            )
        conn.commit()
        conn.close()
        return affected > 0
    def agendar_retorno(
        self,
        prospeccao_id: int,
        data_retorno: str,
        hora_retorno: str | None = None,
        observacao: str | None = None,
    ) -> bool:
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT data_retorno FROM prospeccao_temp WHERE id = ?",
            (prospeccao_id,),
        )
        atual = c.fetchone()
        if not atual:
            conn.close()
            return False
        updates = [
            "data_retorno = ?",
            "hora_retorno = ?",
            "data_prospeccao = CURRENT_DATE",
            "data_ultima_tentativa = CURRENT_DATE",
            "tentativas_retorno = COALESCE(tentativas_retorno, 0) + 1",
            "updated_at = CURRENT_TIMESTAMP",
        ]
        params: list[Any] = [data_retorno, hora_retorno]
        if not atual["data_retorno"]:
            updates.append("data_primeiro_agendamento = COALESCE(data_primeiro_agendamento, ?)")
            params.append(data_retorno)
        if observacao is not None:
            updates.append("observacao = ?")
            params.append((observacao or "").strip() or None)
        params.append(prospeccao_id)
        c.execute(
            f"UPDATE prospeccao_temp SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        affected = c.rowcount
        if affected > 0:
            detalhe = "Agendamento"
            if observacao:
                detalhe = f"Agendamento | {observacao}"
            c.execute(
                """
                INSERT INTO prospeccao_eventos (
                    prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois
                )
                VALUES (?, 'RETORNO_AGENDADO', ?, ?, ?)
            """,
                (prospeccao_id, detalhe, atual["data_retorno"], data_retorno),
            )
            conn.commit()
        conn.close()
        return affected > 0
    def update_draft(
        self,
        prospeccao_id: int,
        observacao: str | None = None,
        telefone: str | None = None,
        whatsapp: str | None = None,
        responsavel: str | None = None,
        email: str | None = None,
    ) -> bool:
        """Atualiza campos do rascunho registrando histórico da observação se necessário."""
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        # Buscar dados atuais para histórico e comparação
        # Atualizamos a data_prospeccao também ao editar rascunho (pois é uma interação/contato)
        c.execute(
            "SELECT observacao, telefone, whatsapp, responsavel, email FROM prospeccao_temp WHERE id = ?",
            (prospeccao_id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return False

        obs_atual = row[0]

        # Histórico de observação
        if obs_atual and obs_atual.strip() and observacao and observacao.strip() and obs_atual != observacao:
            c.execute(
                """
                INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
                VALUES (?, 'OBSERVACAO_CHANGE', ?)
            """,
                (prospeccao_id, obs_atual),
            )
            conn.commit()
        updates = []
        params: list[Any] = []

        if observacao is not None:
            updates.append("observacao = ?")
            params.append((observacao or "").strip() or None)
            updates.append("data_prospeccao = CURRENT_DATE")

        if telefone is not None:
            from application.shared.phone_utils import normalize_phone
            updates.append("telefone = ?")
            params.append(normalize_phone(telefone))

        if whatsapp is not None:
            from application.shared.phone_utils import normalize_phone
            updates.append("whatsapp = ?")
            params.append(normalize_phone(whatsapp))

        if responsavel is not None:
            updates.append("responsavel = ?")
            params.append((responsavel or "").strip() or None)

        if email is not None:
            updates.append("email = ?")
            params.append((email or "").strip() or None)

        if not updates:
            conn.close()
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(prospeccao_id)
        query = f"UPDATE prospeccao_temp SET {', '.join(updates)} WHERE id = ?"

        c.execute(query, tuple(params))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    def converter_para_lead(self, prospeccao_id: int) -> int | None:
        from infrastructure.repositories.prospeccao_conversion import convert_prospect
        return convert_prospect(prospeccao_id, DB_PATH)

    def arquivar(self, prospeccao_id: int) -> bool:
        """Archive without qualifying or converting the prospect."""
        from contextlib import closing
        with closing(get_db_connection(DB_PATH)) as conn, conn:
            cursor = conn.execute(
                "UPDATE prospeccao_temp SET arquivado = 1, data_retorno = NULL, "
                "hora_retorno = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (prospeccao_id,),
            )
            return cursor.rowcount > 0

    def delete(self, prospeccao_id: int) -> bool:
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    def get_retornos_stats(self) -> dict:
        """Retorna estatísticas detalhadas de agendamentos: hoje, atrasados e urgentes."""
        from datetime import datetime, date, timedelta
        agora = datetime.now()
        hoje_date = date.today().isoformat()
        uma_hora_depois = (agora + timedelta(hours=1)).strftime("%H:%M")
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # 1. Atrasados (Data anterior a hoje)
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno < ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje_date,),
        )
        atrasados = c.fetchone()[0]
        # 2. Hoje (Total para hoje)
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje_date,),
        )
        hoje = c.fetchone()[0]
        # 3. Urgentes (Hoje, e o horário já passou ou falta < 1h)
        # Nota: Se hora_retorno for nulo, consideramos urgente se for hoje
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
              AND (hora_retorno <= ? OR hora_retorno IS NULL)
        """,
            (hoje_date, uma_hora_depois),
        )
        urgentes = c.fetchone()[0]
        conn.close()

        return {
            "hoje": hoje,
            "atrasados": atrasados,
            "urgentes": urgentes,
            "total": hoje + atrasados
        }
    def get_eventos(self, prospeccao_id: int) -> list[dict]:
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM prospeccao_eventos
            WHERE prospeccao_id = ?
            ORDER BY data_evento DESC
        """,
            (prospeccao_id,),
        )
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
