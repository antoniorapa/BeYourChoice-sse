from flask import Blueprint, session
from app.models.attivitaModel import Attivita
from app.views.dasboardDocente import TeacherDashboardView
from app.views.dasboardStudente import StudentDashboardView
from app.controllers.loginControl import teacher_required, student_required

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='../templates')


class DashboardController:
    @staticmethod
    @dashboard_blueprint.route('/dashboard-docente', methods=['GET'])
    @teacher_required
    def dashboard_docente():
        cu = session.get('cu')
        if not cu:
            return TeacherDashboardView.render_errore("Codice univoco del docente non trovato", 404)

        model = Attivita()
        classi = model.get_classi_docente(cu)
        return TeacherDashboardView.render_dashboard(classi)

    @staticmethod
    @dashboard_blueprint.route('/classifica/<int:id_classe>', methods=['GET'])
    @teacher_required
    def classifica_classe(id_classe: int):
        # Salviamo in session per UX (es. ricerche AJAX successive),
        # ma la route funziona comunque perché l'id arriva dal path.
        session['id_classe'] = id_classe

        model = Attivita()
        classifica = model.get_classifica_classe(id_classe)
        return TeacherDashboardView.render_classifica(classifica, id_classe)

    @staticmethod
    @dashboard_blueprint.route('/storico/<string:cf_studente>', methods=['GET'])
    @teacher_required
    def storico_studente(cf_studente: str):
        model = Attivita()
        storico = model.get_storico(cf_studente)
        return TeacherDashboardView.render_storico(storico, cf_studente)

    @staticmethod
    @dashboard_blueprint.route('/dashboard-studente', methods=['GET'])
    @student_required
    def dashboard_studente():
        cf = session.get('cf')
        id_classe = session.get('id_classe')

        if not cf:
            return StudentDashboardView.render_errore("Sessione non valida", 400)

        model = Attivita()
        punteggi = model.get_punteggio_personale(cf) or {}
        classifica = model.get_classifica_classe(id_classe) if id_classe is not None else []
        storico = model.get_storico(cf)

        scenari = punteggi.get("PunteggioScenari", 0) or 0
        quiz = punteggi.get("punteggio_quiz", 0) or 0

        return StudentDashboardView.render_dashboard(
            classifica=classifica,
            punteggio_scenario=scenari,
            punteggio_quiz=quiz,
            punteggio_totale=scenari + quiz,
            storico=storico
        )
