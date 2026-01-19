from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
import bcrypt
import re
import uuid
from app.models.docenteModel import DocenteModel
from app.models.studenteModel import StudenteModel

login_bp = Blueprint('login', __name__)

# Regex compilate (micro-ottimizzazione reale e pulizia)
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=])[A-Za-z\d@#$%^&+=]{8,20}$")


def _require_logged_in():
    return 'email' in session and 'session_token' in session


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not _require_logged_in():
            flash("Devi effettuare il login per accedere", "error")
            return redirect(url_for('login.login'))

        studente = StudenteModel().trova_studente(session.get('email'))
        if studente is None:
            flash("Accesso negato: questa area è riservata agli studenti", "error")
            return redirect(url_for('home'))

        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not _require_logged_in():
            flash("Devi effettuare il login per accedere", "error")
            return redirect(url_for('login.login'))

        docente = DocenteModel().trova_docente(session.get('email'))
        if docente is None:
            flash("Accesso negato: questa area è riservata ai docenti", "error")
            return redirect(url_for('home'))

        return f(*args, **kwargs)
    return decorated_function


def _set_session_common(email: str, role: str):
    session['email'] = email
    session['session_token'] = str(uuid.uuid4())
    session['role'] = role


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            return render_template('registrazioneLogin.html')

        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        if not EMAIL_RE.match(email):
            flash("Formato email non valido", "error")
            return redirect(url_for('login.login'))

        if not PASSWORD_RE.match(password):
            flash("Password non valida", "error")
            return redirect(url_for('login.login'))

        studente_model = StudenteModel()
        docente_model = DocenteModel()

        studente = studente_model.trova_studente(email)
        if studente:
            if bcrypt.checkpw(password.encode('utf-8'), studente['password']):
                _set_session_common(email=email, role='studente')

                session['cf'] = studente.get("cf")
                session['nome'] = studente.get("nome")
                session['id_classe'] = studente.get("id_classe") or 0

                return redirect(url_for('dashboard.dashboard_studente'))

            flash("Password errata", "error")
            return redirect(url_for('login.login'))

        docente = docente_model.trova_docente(email)
        if docente:
            if bcrypt.checkpw(password.encode('utf-8'), docente['password']):
                _set_session_common(email=email, role='docente')

                session['sda'] = docente.get("sda")
                session['cu'] = docente.get("codice_univoco")
                session['nome'] = docente.get("nome")
                session['cf'] = docente.get("cf")

                return redirect(url_for('dashboard.dashboard_docente'))

            flash("Password errata", "error")
            return redirect(url_for('login.login'))

        flash("Email non registrata", "error")
        return redirect(url_for('login.login'))

    except Exception as e:
        flash("Errore interno", "error")
        return jsonify({"error": str(e)}), 500


@login_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Sei stato disconnesso", "success")
    return redirect(url_for('login.login'))
