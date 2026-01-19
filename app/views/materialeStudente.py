# app/views/materialeStudente.py
from flask import Blueprint, render_template, redirect, url_for, abort, session
import logging

from app.controllers.materialeControl import MaterialeControl
from databaseManager import DatabaseManager

logger = logging.getLogger(__name__)

MaterialeStudente = Blueprint("MaterialeStudente", __name__)


def initialize_materiale_studente_blueprint(app: object) -> object:
    db_manager = DatabaseManager()
    materiale_control = MaterialeControl(db_manager)
    materiale_control.set_cartella_uploads("public/uploads")

    @MaterialeStudente.route("/")
    def index():
        return redirect(url_for("MaterialeStudente.visualizza_materiale_studente"))

    @MaterialeStudente.route("/materiale/studente")
    def visualizza_materiale_studente():
        id_classe = session.get("id_classe")
        cf_studente = session.get("cf")
        if not cf_studente:
            abort(400, "Parametro cf_studente mancante")

        if id_classe is None:
            return redirect(url_for("dashboard.storico_studente", cf_studente=cf_studente))

        materiali = materiale_control.visualizza_materiali(id_classe)
        return render_template("materialeStudente.html", ID_Classe=id_classe, materiali=materiali)

    @MaterialeStudente.route("/servi_file/<path:nome_file>")
    def servi_file(nome_file: str):
        return materiale_control.servi_file(nome_file)

    app.register_blueprint(MaterialeStudente)
    return app
