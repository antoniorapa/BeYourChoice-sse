import re
from flask import Blueprint, request, jsonify, redirect, url_for, session
from app.models.studenteModel import StudenteModel
from app.models.docenteModel import DocenteModel

registrazione_bp = Blueprint('registrazione', __name__)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
NOME_RE = re.compile(r"^[A-ZÀ-ÖØ-Ý][a-zà-öø-ý]{2,}(?:['-][A-ZÀ-ÖØ-Ýa-zà-öø-ý]+)*$")
COGNOME_RE = NOME_RE
SDA_RE = re.compile(r"^[A-Za-z0-9À-ù'’\- ]{10,50}$")
CF_RE = re.compile(r"^[A-Z]{6}[0-9]{2}[A-EHLMPR-T][0-9]{2}[A-Z0-9]{4}[A-Z]$")
DATA_RE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])[A-Za-z\d!@#$%^&*()\-_=+\[\]{};:,.<>?/\\|~]{8,20}$")
CU_RE = re.compile(r"^\d{6}$")


@registrazione_bp.route('/register', methods=['POST'])
def registra():
    try:
        nome = (request.form.get('nome') or '').strip()
        cognome = (request.form.get('cognome') or '').strip()
        sda = (request.form.get('sda') or '').strip()
        email = (request.form.get('email') or '').strip()
        cf = (request.form.get('cf') or '').strip().upper()
        data_nascita = (request.form.get('data-nascita') or '').strip()
        password = request.form.get('password') or ''
        codice_univoco = (request.form.get('cu') or '').strip()

        if not EMAIL_RE.match(email):
            return redirect(url_for('login.login', error='formatoEmail'))
        if not NOME_RE.match(nome):
            return redirect(url_for('login.login', error='formatoNome'))
        if not COGNOME_RE.match(cognome):
            return redirect(url_for('login.login', error='formatoCognome'))
        if not SDA_RE.match(sda):
            return redirect(url_for('login.login', error='formatoSDA'))
        if not CF_RE.match(cf):
            return redirect(url_for('login.login', error='formatocf'))
        if not DATA_RE.match(data_nascita):
            return redirect(url_for('login.login', error='formatoDataNascita'))
        if not PASSWORD_RE.match(password):
            return redirect(url_for('login.login', error='formatoPassword'))

        is_docente = bool(codice_univoco)
        if is_docente and not CU_RE.match(codice_univoco):
            return redirect(url_for('login.login', error='formatoCU'))

        docente_model = DocenteModel()
        studente_model = StudenteModel()

        if docente_model.trova_docente(email) is not None or studente_model.trova_studente(email) is not None:
            return redirect(url_for('login.login', error='alreadyRegistered'))

        if is_docente:
            docente_dict = {
                "nome": nome,
                "cognome": cognome,
                "sda": sda,
                "email": email,
                "cf": cf,
                "data_nascita": data_nascita,
                "password": password,
                "codice_univoco": int(codice_univoco)
            }
            docente_model.aggiungi_docente(docente_dict)
            session['email'] = email
            session['role'] = 'docente'
            return redirect(url_for('dashboard.dashboard_docente'))

        studente_dict = {
            "nome": nome,
            "cognome": cognome,
            "sda": sda,
            "email": email,
            "cf": cf,
            "data_nascita": data_nascita,
            "password": password
        }
        studente_model.aggiungi_studente(studente_dict)
        session['email'] = email
        session['role'] = 'studente'
        return redirect(url_for('dashboard.dashboard_studente'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
