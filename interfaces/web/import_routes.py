"""Preview before importing; signed payload expires and is rechecked on confirmation."""
from flask import current_app, render_template, request, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from application.prospeccao.import_csv import preview_csv, MAX_BYTES
from application.maps.accessories import SEGMENT as ACCESSORIES
from application.maps.car_dealers import is_car_dealer, CAMPAIGN
from infrastructure.repositories.csv_prospect_repository import CsvProspectRepository


def serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='prospects-csv-v1')


def import_view():
    rows, token, result, error = None, None, None, None
    segment = request.form.get('segmento') or ACCESSORIES
    if request.method == 'POST':
        try:
            if request.form.get('action') == 'confirm':
                rows = serializer().loads(request.form.get('preview_token', ''), max_age=1800)
                if rows:
                    segment = rows[0]['data'].get('segmento') or ACCESSORIES
                indexes = {int(value) for value in request.form.getlist('selected')}
                chosen = [row['data'] for index, row in enumerate(rows) if index in indexes and not row['errors']]
                if not chosen:
                    raise ValueError('Selecione ao menos um contato válido.')
                result = CsvProspectRepository().import_rows(chosen)
                rows = None
            else:
                upload = request.files.get('file')
                if not upload:
                    raise ValueError('Selecione o arquivo CSV.')
                rows = preview_csv(upload.read(MAX_BYTES + 1), segmento=segment)
                token = serializer().dumps(rows)
        except (BadSignature, SignatureExpired):
            error = 'Prévia inválida ou expirada. Envie o arquivo novamente.'
        except (ValueError, UnicodeError) as exc:
            error = str(exc)
    return render_template('import_prospects.html', rows=rows, preview_token=token,
                           result=result, error=error, selected_segment=segment, campaign=CAMPAIGN if is_car_dealer(segment) else None, active_page='prospeccao'), 400 if error else 200


def import_model():
    return Response('nome_loja;cidade;estado;telefone;whatsapp;cnpj;email;site;endereco;responsavel;fonte;url_fonte;observacoes\n',
                    mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=modelo_prospeccao.csv'})


def register_import_routes(app):
    app.add_url_rule('/prospeccao/importar', view_func=import_view, methods=['GET', 'POST'])
    app.add_url_rule('/prospeccao/importar/modelo.csv', view_func=import_model)
