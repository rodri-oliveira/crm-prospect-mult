from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.agendamentos_repository import AgendamentosRepository
from domain.repositories.prospeccao_repository import ProspeccaoRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class RegistrarTentativaRequest:
    prospeccao_id: int
    resultado: str
    observacao: str | None
    data_retorno: str | None
    hora_retorno: str | None
    segmento: str | None
    pos_acao: str | None  # "converter" ou None
    responsavel: str | None = None
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None


@dataclass(frozen=True)
class RegistrarTentativaResult:
    ok: bool
    redirect_to: str
    redirect_kwargs: dict[str, Any]
    message: str | None = None


def registrar_tentativa(req: RegistrarTentativaRequest) -> RegistrarTentativaResult:
    return registrar_tentativa_with_repo(
        req,
        SqliteAgendamentosRepository(),
        SqliteProspeccaoRepository(),
    )


def registrar_tentativa_with_repo(
    req: RegistrarTentativaRequest,
    agendamentos_repo: AgendamentosRepository,
    prospeccao_repo: ProspeccaoRepository,
) -> RegistrarTentativaResult:
    from application.shared.workflow import canonical_status, validate_schedule
    try:
        resultado = canonical_status(req.resultado)
        if resultado == 'Pediu para retornar':
            resultado = 'Agendar retorno'
        validate_schedule(req.data_retorno, req.hora_retorno, resultado in ('Agendar retorno', 'Não analisou ainda o material'))
    except ValueError as error:
        return RegistrarTentativaResult(False, 'agendamentos_view', {'erro': str(error)})

    # Validações
    if not resultado:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Selecione o resultado da tentativa."},
        )

    resultados_tentativa = ("Não atendeu", "Caixa postal", "Sem contato")
    resultados_com_observacao_obrigatoria = ("Em negociação", "Pediu preço", "Não analisou ainda o material")
    resultados_status = (
        "Solicitou portfólio",
        "Já tem consultor atendendo",
        "Sem interesse",
        "Aguard. Lista Prod.",
        "Enviado Portfólio Whats",
        "Enviado Portfólio por E-mail",
        "Aguardando dados para cadastro",
    )

    if resultado in resultados_com_observacao_obrigatoria and not req.observacao:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Observação obrigatória para registrar o próximo passo."},
        )

    if resultado in ("Agendar retorno", "Não analisou ainda o material") and not req.data_retorno:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Informe a data de retorno para continuar."},
        )
    if resultado in ("Agendar retorno", "Não analisou ainda o material") and req.data_retorno and not req.hora_retorno:
        return RegistrarTentativaResult(
            ok=False,
            redirect_to="agendamentos_view",
            redirect_kwargs={"erro": "Informe o horário de retorno para continuar."},
        )

    # Validação de segmento para início de negociação
    if resultado == "Em negociação":
        if not req.segmento:
            prospeccao = prospeccao_repo.get_by_id(req.prospeccao_id)
            if not prospeccao or not prospeccao.get("segmento"):
                return RegistrarTentativaResult(
                    ok=False,
                    redirect_to="agendamentos_view",
                    redirect_kwargs={"erro": "Informe o segmento antes de registrar início de negociação."},
                )
        else:
            agendamentos_repo.update_segmento(req.prospeccao_id, req.segmento)

    # Atualizar dados de contato se fornecidos
    if any([req.responsavel, req.email, req.telefone, req.whatsapp]):
        prospeccao_repo.update_draft(
            prospeccao_id=req.prospeccao_id,
            responsavel=req.responsavel,
            email=req.email,
            telefone=req.telefone,
            whatsapp=req.whatsapp
        )

    # Processar resultado
    if resultado in resultados_tentativa:
        detalhe = resultado
        if req.observacao:
            detalhe = f"{resultado} | {req.observacao}"
        agendamentos_repo.registrar_tentativa_retorno(req.prospeccao_id, detalhe)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Descartado":
        prospeccao_repo.update_status(
            req.prospeccao_id,
            "Descartado",
            observacao=req.observacao,
            clear_retorno=True,
        )
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, "Descartado", observacao=req.observacao)
        prospeccao_repo.arquivar(req.prospeccao_id)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Interessado":
        from application.prospeccao.update_status import UpdateProspecctionStatusRequest, update_prospecction_status_with_repo
        converted = update_prospecction_status_with_repo(
            UpdateProspecctionStatusRequest(req.prospeccao_id, 'Interessado', req.observacao, None, None), prospeccao_repo)
        return RegistrarTentativaResult(converted.ok, converted.redirect_to, converted.redirect_kwargs)

    if resultado in resultados_status:
        prospeccao_repo.update_status(
            req.prospeccao_id,
            resultado,
            observacao=req.observacao,
            clear_retorno=True,
        )
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, resultado, observacao=req.observacao)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado in ("Agendar retorno", "Não analisou ainda o material"):
        prospeccao_repo.agendar_retorno(
            req.prospeccao_id,
            data_retorno=req.data_retorno,
            hora_retorno=req.hora_retorno,
            observacao=req.observacao,
        )
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, resultado, observacao=req.observacao)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    if resultado == "Em negociação":
        from application.prospeccao.update_status import UpdateProspecctionStatusRequest, update_prospecction_status_with_repo
        converted = update_prospecction_status_with_repo(
            UpdateProspecctionStatusRequest(req.prospeccao_id, resultado, req.observacao, req.data_retorno, req.hora_retorno), prospeccao_repo)
        return RegistrarTentativaResult(converted.ok, converted.redirect_to, converted.redirect_kwargs)

    if resultado == "Pediu preço":
        prospeccao_repo.update_status(req.prospeccao_id, resultado, observacao=req.observacao,
                                    data_retorno=req.data_retorno, hora_retorno=req.hora_retorno,
                                    clear_retorno=not bool(req.data_retorno))
        agendamentos_repo.registrar_resultado_retorno(req.prospeccao_id, "Pediu preço", observacao=req.observacao)
        return RegistrarTentativaResult(
            ok=True,
            redirect_to="agendamentos_view",
            redirect_kwargs={},
        )

    return RegistrarTentativaResult(
        ok=False,
        redirect_to="agendamentos_view",
        redirect_kwargs={"erro": "Resultado inválido."},
    )
