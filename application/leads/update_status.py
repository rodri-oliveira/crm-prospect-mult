from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.lead_repository import LeadRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository


@dataclass(frozen=True)
class UpdateLeadStatusRequest:
    lead_id: int
    novo_status: str


@dataclass(frozen=True)
class UpdateLeadStatusResponse:
    ok: bool


def update_lead_status(req: UpdateLeadStatusRequest) -> UpdateLeadStatusResponse:
    return update_lead_status_with_repo(req, SqliteLeadRepository())


def update_lead_status_with_repo(req: UpdateLeadStatusRequest, repo: LeadRepository) -> UpdateLeadStatusResponse:
    from application.shared.workflow import canonical_status
    status = canonical_status(req.novo_status)
    if status == 'Cliente ativo' and not repo.has_sales(req.lead_id):
        raise ValueError('Registre uma venda para marcar o lead como Cliente ativo.')
    ok = repo.update_status(req.lead_id, status)

    # Se status mudou para "Sem interesse", devolver para prospecção
    if ok and status == "Sem interesse":
        repo.devolver_para_prospeccao(req.lead_id)

    return UpdateLeadStatusResponse(ok=ok)
