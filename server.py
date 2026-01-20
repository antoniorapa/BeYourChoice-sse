from flask import Flask, render_template, session, redirect, url_for, request
from flask_compress import Compress
import logging
import time
import os

from app.controllers.loginControl import login_bp
from app.controllers.quizControl import quiz_blueprint
from app.controllers.registrazioneControl import registrazione_bp
from app.controllers.dashboardControl import dashboard_blueprint

from app.views.inserimentoStudente import inserimentostudente
from app.views.classeDocente import classedocente
from app.views.scenarioView import scenario_bp
from app.views.creazioneClasse import creazioneclasse

from app.models.studenteModel import StudenteModel
from app.models.docenteModel import DocenteModel
from app.models.attivitaModel import Attivita

from app.views.materialeDocente import initialize_materiale_docente_blueprint
from app.views.materialeStudente import initialize_materiale_studente_blueprint
from app.views.profilo import initialize_profilo_blueprint

logging.basicConfig(level=logging.INFO)

app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder="public",
    static_url_path="/public"
)

# Compressione

app.config["COMPRESS_ALGORITHM"] = ["gzip"]
app.config["COMPRESS_LEVEL"] = 9
app.config["COMPRESS_MIN_SIZE"] = 500

Compress(app)

# Timer + Cache
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # LOG tempo risposta
    duration = time.time() - request.start_time
    logging.info(f"Request to {request.path} took {duration:.2f} seconds")

    # CACHE per statici
    if request.path.startswith("/public/") or request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

@app.route('/')
def home():
    if 'email' not in session:
        return redirect(url_for('login.login'))

    logged_in = True
    email = session.get('email')

    if not email:
        return redirect(url_for('login.login'))

    studenteModel = StudenteModel()
    docenteModel = DocenteModel()
    stud = studenteModel.trova_studente(email)
    doc = docenteModel.trova_docente(email)
    model = Attivita()

    if stud is not None:
        return render_template(
            'dashboardStudente.html',
            logged_in=logged_in,
            storico=model.get_storico(studenteModel.trova_cf_per_email(email))
        )

    if doc is not None:
        return render_template(
            'dashboardDocente.html',
            logged_in=logged_in,
            id_docente=docenteModel.get_codice_univoco_by_email(email)
        )

    return redirect(url_for('login.login'))

# Blueprint
app.register_blueprint(classedocente, url_prefix='/classedocente')
app.register_blueprint(inserimentostudente, url_prefix='/inserimentostudente')
app.register_blueprint(creazioneclasse, url_prefix='/')

app.register_blueprint(dashboard_blueprint)
app.register_blueprint(scenario_bp)
app.register_blueprint(login_bp)
app.register_blueprint(registrazione_bp)
app.register_blueprint(quiz_blueprint)

# Upload folder
UPLOAD_FOLDER = 'public/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())

# Blueprint aggiuntivi
initialize_materiale_docente_blueprint(app)
initialize_materiale_studente_blueprint(app)
initialize_profilo_blueprint(app)

if __name__ == "__main__":
    app.run(debug=False)