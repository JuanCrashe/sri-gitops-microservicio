import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, Response
from functools import wraps

frontend_bp = Blueprint('frontend', __name__)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
PUBLIC_BACKEND_URL = os.environ.get('PUBLIC_BACKEND_URL', '')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            return redirect(url_for('frontend.login'))
        return f(*args, **kwargs)
    return decorated_function

@frontend_bp.route('/')
def index():
    if 'token' in session:
        return redirect(url_for('frontend.detalle'))
    return redirect(url_for('frontend.login'))

@frontend_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ruc = request.form.get('ruc')
        password = request.form.get('password')
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                data={
                    "username": ruc,
                    "password": password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                session['token'] = data.get('token')
                session['ruc'] = data.get('ruc')
                return redirect(url_for('frontend.detalle'))
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = data.get('detail') or data.get('error') or 'Credenciales inválidas'
                flash(error_msg, 'error')
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error conectando al backend: {e}")
            flash('Error de conexión con el servidor de autenticación', 'error')
            
    return render_template('login.html')

@frontend_bp.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('frontend.login'))

@frontend_bp.route('/detalle')
@login_required
def detalle():
    ruc = session.get('ruc')
    if not ruc:
        # Si por alguna razon no hay RUC, lo sacamos
        return redirect(url_for('frontend.logout'))
    return render_template('detalle.html', backend_url=PUBLIC_BACKEND_URL, token=session.get('token'), ruc=ruc)

@frontend_bp.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_api(path):
    """
    Reverse proxy interno para peticiones AJAX del cliente hacia el backend.
    Evita exponer puertos o IPs públicas adicionales y previene problemas de CORS.
    """
    url = f"{BACKEND_URL}/api/{path}"
    headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'content-length']}
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            timeout=10
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        resp_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                        if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, resp_headers)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error en reverse proxy API: {e}")
        return {"error": "Error de comunicación con el backend"}, 502
