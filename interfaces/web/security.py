"""Local-only by default, optional single-user Basic auth and CSRF protection."""
import hmac
import secrets
from urllib.parse import urlsplit
from flask import request, session, Response, abort


def register_security(app):
    if bool(app.config.get('CRM_USERNAME')) != bool(app.config.get('CRM_PASSWORD')):
        raise ValueError('Configure CRM_USERNAME e CRM_PASSWORD juntos.')

    @app.before_request
    def protect_request():
        username, password = app.config.get('CRM_USERNAME'), app.config.get('CRM_PASSWORD')
        if username and password:
            auth = request.authorization
            if not (auth and auth.type.lower() == 'basic'
                    and hmac.compare_digest((auth.username or '').encode(), username.encode())
                    and hmac.compare_digest((auth.password or '').encode(), password.encode())):
                return Response('Autenticação necessária.', 401, {'WWW-Authenticate': 'Basic realm="Prospect CRM", charset="UTF-8"'})
        elif request.remote_addr not in ('127.0.0.1', '::1') or urlsplit(request.host_url).hostname not in ('127.0.0.1', 'localhost', '::1'):
            abort(403, description='Acesso local. Configure usuário e senha para uso pela rede.')

        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            expected = session.get('csrf_token', '')
            supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token') or ''
            if not expected or not hmac.compare_digest(expected, supplied):
                abort(400, description='Sessão expirada. Recarregue a página antes de salvar.')
        session.setdefault('csrf_token', secrets.token_urlsafe(32))

    @app.context_processor
    def security_context():
        return {'csrf_token': session.get('csrf_token', '')}

    @app.after_request
    def secure_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store'
        return response
