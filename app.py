import os
import logging
import secrets
from werkzeug.exceptions import HTTPException
from datetime import date
from database import init_db
from flask import Flask, jsonify, render_template, request

from interfaces.api.routes import register_api_routes
from interfaces.web.routes import register_web_routes
from infrastructure.container import agendamentos_repository, prospeccao_repository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('CRM_SECRET_KEY') or secrets.token_hex(32),
    CRM_USERNAME=os.environ.get('CRM_USERNAME'),
    CRM_PASSWORD=os.environ.get('CRM_PASSWORD'),
    MAX_CONTENT_LENGTH=3 * 1024 * 1024,
    TEMPLATES_AUTO_RELOAD=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('CRM_COOKIE_SECURE', '').lower() == 'true',
)
from interfaces.web.security import register_security
register_security(app)

# Context processor para disponibilizar dados globais em todos os templates
@app.context_processor
def inject_globals():
    try:
        stats = prospeccao_repository().get_retornos_stats()
        return {
            'retornos_stats': stats
        }
    except Exception as e:
        logger.error(f"Erro ao injetar globais: {e}", exc_info=True)
        return {'retornos_stats': {'hoje': 0, 'atrasados': 0, 'urgentes': 0, 'total': 0, 'indisponivel': True}}


# ==================== ERROR Handlers ====================

@app.errorhandler(ValueError)
@app.errorhandler(400)
def bad_request(error):
    """Handler para erros 400 - Bad Request."""
    logger.warning(f"Bad Request: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Requisição inválida',
            'error': str(error)
        }), 400
    return render_template('error.html',
        code=400,
        message=getattr(error, 'description', str(error)),
        active_page='error'
    ), 400


@app.errorhandler(404)
def not_found(error):
    """Handler para erros 404 - Not Found."""
    logger.warning(f"Not Found: {request.path}")
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Recurso não encontrado'
        }), 404
    return render_template('error.html',
        code=404,
        message='Página não encontrada',
        active_page='error'
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros 500 - Internal Server Error."""
    logger.error(f"Internal Server Error: {error}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Erro interno do servidor'
        }), 500
    return render_template('error.html',
        code=500,
        message='Erro interno do servidor',
        active_page='error'
    ), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handler global para exceções não tratadas."""
    if isinstance(error, HTTPException):
        if request.path.startswith('/api/'):
            return jsonify(ok=False, message=error.description), error.code
        return render_template('error.html', code=error.code, message=error.description, active_page='error'), error.code
    logger.error(f"Unhandled Exception: {error}", exc_info=True)

    if request.path.startswith('/api/'):
        return jsonify({
            'ok': False,
            'message': 'Erro inesperado',
            'error': str(error) if app.debug else 'Erro interno'
        }), 500

    return render_template('error.html',
        code=500,
        message='Erro inesperado',
        active_page='error'
    ), 500


# Auto-init db se não existir
init_db()

register_web_routes(app)
register_api_routes(app)

if __name__ == '__main__':
    from application.shared.runtime import port_in_use
    host = os.environ.get('CRM_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    auto_reload = os.environ.get('CRM_AUTO_RELOAD', '1').lower() not in ('0', 'false', 'off', 'no')
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and port_in_use(host, port):
        raise SystemExit(f'A porta {port} já está em uso. Feche a janela antiga do CRM antes de iniciar esta versão.')
    logger.info('CRM iniciado de %s | recarga de código: %s | recarga de templates: ativa', app.root_path, auto_reload)
    app.run(host=host, debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true',
            port=port, use_reloader=auto_reload)
