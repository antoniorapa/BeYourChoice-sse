from flask import Blueprint, render_template, request, redirect, url_for
from app.controllers.loginControl import teacher_required
from app.controllers.scenarioControl import scenarioControl
from app.models.scenarioModel import ScenarioModel

scenario_bp = Blueprint('scenario_bp', __name__)

@scenario_bp.route('/scenarioVirtuale', methods=['GET', 'POST'])
@teacher_required
def scenario_virtuale():

    # ===== GET =====
    if request.method == "GET":
        return render_template("scenarioVirtuale.html")


    # ===== POST =====
    scenarioModel = ScenarioModel()
    id = scenarioModel.get_ultimo_scenario_id()

    if id is None:
        id = 0
    elif id == 0:
        id = 1
    elif id > 0:
        id = id + 1

    titolo = request.form.get('titolo', '').strip()
    descrizione = request.form.get('descrizione', '').strip()
    modalita = request.form.get('modalita', '').strip()
    argomento = request.form.get('argomento', '').strip()

    result = scenarioControl.registra_scenario(id, titolo, descrizione, modalita, argomento)

    if "success" in result and result["success"]:
        return render_template("visore.html")  # oppure redirect dove vuoi

    else:
        error = result.get("error", "ErroreInterno")
        return redirect(url_for('scenario_bp.scenario_virtuale', error=error))


@scenario_bp.route('/postAssociazione')
@teacher_required
def postAssociazione():
    return render_template("scenarioVirtuale.html")