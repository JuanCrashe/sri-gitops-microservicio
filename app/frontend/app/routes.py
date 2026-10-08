import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from functools import wraps

frontend_bp = Blueprint('frontend', __name__)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
PUBLIC_BACKEND_URL = os.environ.get('PUBLIC_BACKEND_URL', 'http://localhost:5000')

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
            response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", data={
                "username": ruc,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                session['token'] = data.get('token')
                session['ruc'] = data.get('ruc')
                return redirect(url_for('frontend.detalle'))
            else:
                error_msg = response.json().get('error', 'Credenciales inválidas')
                flash(error_msg, 'error')
        except requests.exceptions.RequestException:
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
