"""Validate and calculate sales on the server, in decimal currency."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from domain.repositories.pedido_repository import Pedido, PedidoItem

CENT = Decimal('0.01')


def pedido_from_form(form) -> Pedido:
    try:
        lead_id = int(form.get('lead_id', ''))
        data_pedido = date.fromisoformat(form.get('data_pedido', '')).isoformat()
        retorno = form.get('data_proximo_contato') or None
        if retorno:
            retorno = date.fromisoformat(retorno).isoformat()
        names = ['familias[]', 'codigos[]', 'descricoes[]', 'quantidades[]', 'precos_unt[]']
        columns = [form.getlist(name) for name in names]
        if not columns[2] or len({len(col) for col in columns}) != 1 or len(columns[2]) > 200:
            raise ValueError('Informe itens completos (máximo de 200).')
        itens, total = [], Decimal('0.00')
        for familia, codigo, descricao, quantidade, preco in zip(*columns):
            if not descricao.strip():
                continue
            qtd = int(quantidade)
            unt = Decimal(preco)
            if qtd <= 0 or qtd > 1_000_000 or not unt.is_finite() or unt < 0 or unt > 1_000_000_000:
                raise ValueError('Quantidade ou preço fora do intervalo permitido.')
            unt = unt.quantize(CENT, rounding=ROUND_HALF_UP)
            subtotal = (qtd * unt).quantize(CENT)
            total += subtotal
            itens.append(PedidoItem(familia.strip(), codigo.strip(), descricao.strip(), qtd, float(unt), float(subtotal)))
        if lead_id <= 0 or not itens:
            raise ValueError('Informe um lead e ao menos um item válido.')
        return Pedido(None, lead_id, data_pedido, form.get('numero_pedido') or None,
                      float(total), 'Faturado', retorno, form.get('observacoes') or None, itens)
    except (TypeError, InvalidOperation, OverflowError) as error:
        raise ValueError('Dados do pedido inválidos.') from error
    except ValueError as error:
        raise ValueError(f'Pedido inválido: {error}') from error
