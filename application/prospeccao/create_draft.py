from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.prospeccao_repository import ProspeccaoRepository
from application.shared.phone_utils import normalize_phone
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class CreateProspecctionDraftRequest:
    nome_loja: str
    cnpj: str | None
    telefone: str | None
    whatsapp: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    segmento: str | None
    maps_place_id: str | None
    maps_url: str | None
    site: str | None
    observacoes: str | None = None
    status_prospeccao: str | None = None
    data_retorno: str | None = None
    hora_retorno: str | None = None
    responsavel: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class CreateProspecctionDraftResult:
    prospeccao_id: int
    created: bool
    lead_id: int | None = None


def create_prospeccao_draft(req: CreateProspecctionDraftRequest) -> CreateProspecctionDraftResult:
    return create_prospeccao_draft_with_repo(req, SqliteProspeccaoRepository())


def create_prospeccao_draft_with_repo(
    req: CreateProspecctionDraftRequest,
    repo: ProspeccaoRepository,
) -> CreateProspecctionDraftResult:
    from application.shared.workflow import canonical_status, validate_schedule
    from application.shared.cnpj_utils import is_valid_cnpj
    status = canonical_status(req.status_prospeccao or 'Não contatado')
    if not req.nome_loja.strip():
        raise ValueError('Informe o nome da loja.')
    if req.cnpj and not is_valid_cnpj(req.cnpj):
        raise ValueError('CNPJ inválido.')
    if status == 'Interessado' and not req.cnpj:
        raise ValueError('Informe CNPJ válido para converter um interessado em lead.')
    validate_schedule(req.data_retorno, req.hora_retorno, status == 'Pediu para retornar')
    dados = {
        "nome_loja": req.nome_loja,
        "cnpj": req.cnpj,
        "telefone": normalize_phone(req.telefone),
        "whatsapp": normalize_phone(req.whatsapp),
        "endereco": req.endereco,
        "cidade": req.cidade,
        "estado": req.estado,
        "segmento": req.segmento or "Acessórios de informática",
        "maps_place_id": req.maps_place_id,
        "maps_url": req.maps_url,
        "site": req.site,
        "observacoes": req.observacoes,
        "status_prospeccao": status,
        "data_retorno": req.data_retorno,
        "hora_retorno": req.hora_retorno,
        "responsavel": req.responsavel,
        "email": req.email,
    }

    prospeccao_id, created = repo.add(dados)
    if not created:
        return CreateProspecctionDraftResult(int(prospeccao_id), False)
    lead_id = None
    if status in ('Interessado', 'Em negociação'):
        lead_id = repo.converter_para_lead(prospeccao_id)
        if not lead_id:
            raise ValueError('Não foi possível converter em lead.')
    elif status == 'Descartado':
        repo.arquivar(prospeccao_id)
    return CreateProspecctionDraftResult(int(prospeccao_id), bool(created), lead_id)
