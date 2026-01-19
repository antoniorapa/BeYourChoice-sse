# app/views/materialeDocente.py
from bson import ObjectId
from flask import render_template, request, redirect, url_for, Blueprint, session
import logging

from app.controllers.loginControl import teacher_required
from databaseManager import DatabaseManager
from app.controllers.materialeControl import MaterialeControl

logger = logging.getLogger(__name__)

MaterialeDocente = Blueprint("MaterialeDocente", __name__)


def initialize_materiale_docente_blueprint(app: object) -> object:
    db_manager = DatabaseManager()
    materiale_control = MaterialeControl(db_manager)
    materiale_control.set_cartella_uploads("public/uploads")

    @MaterialeDocente.route("/")
    def index():
        return redirect(url_for("MaterialeDocente.visualizza_materiale_docente"))

    @MaterialeDocente.route("/materiale/docente")
    @teacher_required
    def visualizza_materiale_docente():
        id_classe = session.get("id_classe")
        materiali = materiale_control.visualizza_materiali(id_classe)
        return render_template("materialeDocente.html", materiali=materiali)

    @MaterialeDocente.route("/servi_file/<path:nome_file>")
    def servi_file(nome_file: str):
        return materiale_control.servi_file(nome_file)

    @MaterialeDocente.route("/carica", methods=["GET", "POST"])
    @teacher_required
    def carica_materiale():
        if request.method == "POST":
            return materiale_control.carica_materiale(request)
        return render_template("caricamentoMateriale.html")

    @MaterialeDocente.route("/modifica/<string:id_materiale>", methods=["GET", "POST"])
    @teacher_required
    def modifica_materiale(id_materiale):
        if request.method == "POST":
            return materiale_control.modifica_materiale(id_materiale, request)

        try:
            id_materiale_obj = ObjectId(id_materiale)
            collezione_materiali = db_manager.get_collection("MaterialeDidattico")
            materiale = collezione_materiali.find_one({"_id": id_materiale_obj})
            if materiale is None:
                return render_template("modificaMateriale.html", messaggio="Il materiale non è stato trovato.")
            return render_template("modificaMateriale.html", materiale=materiale)
        except Exception as e:
            logger.exception("Errore recupero materiale %s: %s", id_materiale, e)
            return render_template("modificaMateriale.html", messaggio="Errore nel recupero del materiale.")

    @MaterialeDocente.route("/rimuovi/<id_materiale>")
    @teacher_required
    def rimuovi_materiale(id_materiale):
        return materiale_control.rimuovi_materiale(id_materiale)

    app.register_blueprint(MaterialeDocente)
    return app
