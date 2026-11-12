from __future__ import annotations
from datetime import date
from flask import Flask, redirect, render_template, request, url_for
from infrastructure.container import pedido_repository, lead_repository

def vendas_list_view():
    repo = pedido_repository()
    clientes = repo.list_all_active_clients()
    total_carteira = sum(c['faturado_total'] for c in clientes)

    return render_template(
        "vendas.html",
        clientes=clientes,
        total_carteira=total_carteira,
        active_page="vendas"
    )

def vendas_registrar_view(lead_id: int):
    l_repo = lead_repository()
    result = l_repo.get_by_id(lead_id)
    if not result:
        return redirect(url_for('leads_list'))

    lead, _, _ = result

    return render_template(
        "vendas_registrar.html",
        lead=lead,
        hoje=date.today().isoformat(),
        active_page="vendas"
    )

def vendas_registrar_action():
    from application.vendas.registrar import pedido_from_form
    from flask import abort
    try:
        pedido = pedido_from_form(request.form)
        if not lead_repository().get_by_id(pedido.lead_id):
            abort(404)
        pedido_repository().registrar(pedido)
    except ValueError as error:
        abort(400, description=str(error))
    return redirect(url_for('vendas_list_view'))


def vendas_cliente_detalhe(lead_id: int):
    return redirect(url_for('lead_detail', lead_id=lead_id))

def register_vendas_routes(app: Flask) -> None:
    app.add_url_rule("/vendas", endpoint="vendas_list_view", view_func=vendas_list_view)
    app.add_url_rule("/vendas/registrar/<int:lead_id>", endpoint="vendas_registrar_view", view_func=vendas_registrar_view)
    app.add_url_rule("/vendas/registrar", endpoint="vendas_registrar_action", view_func=vendas_registrar_action, methods=["POST"])
    app.add_url_rule("/vendas/cliente/<int:lead_id>", endpoint="vendas_cliente_detalhe", view_func=vendas_cliente_detalhe)
