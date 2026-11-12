from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class AddLeadContatoRequest:
    lead_id: int
    tipo_contato: str
    resultado: str
    observacao: str | None
    data_retorno: str | None
    hora_retorno: str | None


@dataclass(frozen=True)
class AddLeadContatoResult:
    ok: bool
    redirect_to: str
    redirect_kwargs: dict[str, Any]
    message: str | None = None


def add_lead_contato(req: AddLeadContatoRequest) -> AddLeadContatoResult:
    return add_lead_contato_with_repo(req, SqliteLeadRepository())


def add_lead_contato_with_repo(req: AddLeadContatoRequest, repo: LeadRepository) -> AddLeadContatoResult:
    from application.shared.workflow import canonical_status, validate_schedule
    try:
        resultado = canonical_status(req.resultado)
        validate_schedule(req.data_retorno, req.hora_retorno, resultado == 'Agendar retorno')
    except ValueError as error:
        return AddLeadContatoResult(False, 'lead_detail', {'lead_id': req.lead_id, 'erro': str(error)})

    # Validações para resultados que exigem data/hora de retorno
    if resultado == "Agendar retorno":
        if not req.data_retorno:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe a data de retorno para continuar."},
            )
        if not req.hora_retorno:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe o horário de retorno."},
            )

    # Validação de segmento para início de negociação
    if resultado == "Em negociação":
        row = repo.get_by_id(req.lead_id)
        if not row:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="leads_list",
                redirect_kwargs={},
                message="Lead não encontrado.",
            )
        _, _, segmentos = row
        if not segmentos:
            return AddLeadContatoResult(
                ok=False,
                redirect_to="lead_detail",
                redirect_kwargs={"lead_id": req.lead_id, "erro": "Informe o segmento do lead antes de registrar o início de negociação."},
            )

    # Failed attempts retain the pending callback and its original deadline.
    data_retorno, hora_retorno = req.data_retorno, req.hora_retorno
    if resultado in ('Não atendeu', 'Caixa postal', 'Sem contato') and not data_retorno:
        current = repo.get_by_id(req.lead_id)
        if current:
            pending = next((c for c in current[1] if c.get('data_retorno') and not c.get('retorno_encerrado')), None)
            if pending:
                data_retorno, hora_retorno = pending['data_retorno'], pending.get('hora_retorno')

    if resultado == 'Cliente ativo' and not repo.has_sales(req.lead_id):
        raise ValueError('Registre uma venda para ativar o cliente.')

    # Adicionar contato
    repo.add_contato(
        lead_id=req.lead_id,
        tipo_contato=req.tipo_contato,
        resultado=resultado,
        observacao=req.observacao,
        data_retorno=data_retorno,
        hora_retorno=hora_retorno,
    )

    # Sincronizar Status do Lead com o Resultado da Interação
    # Se o resultado for um status válido de Lead, atualiza o status principal
    from application.shared.status import STATUS_LEADS
    status_alvo = resultado
    if resultado in ("Agendar retorno", "Não atendeu", "Caixa postal", "Sem contato"):
        status_alvo = None  # Scheduling is an action, never proof of interest.

    if status_alvo in STATUS_LEADS:
        from application.leads.update_status import UpdateLeadStatusRequest, update_lead_status_with_repo
        update_lead_status_with_repo(UpdateLeadStatusRequest(req.lead_id, status_alvo), repo)

    # Lógica Inteligente de Redirecionamento
    # Se for um status de "saída", mandamos para a lista para que ele suma da frente do usuário
    status_saida = ["Sem interesse", "Descartado", "Já tem consultor atendendo", "Cliente ativo"]

    redirect_to = ""
    if status_alvo in status_saida:
        redirect_to = "leads_list"

    return AddLeadContatoResult(
        ok=True,
        redirect_to=redirect_to,
        redirect_kwargs={},
    )
