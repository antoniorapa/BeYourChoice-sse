from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.controllers.classeVirtualeControl import ClasseVirtualeControl
from app.controllers.loginControl import teacher_required, student_required

classedocente = Blueprint('classedocente', __name__)

# Lazy singleton locale al modulo (non creato a import-time)
_classe_virtuale_control = None


def get_classe_virtuale_control():
    global _classe_virtuale_control
    if _classe_virtuale_control is None:
        _classe_virtuale_control = ClasseVirtualeControl()
    return _classe_virtuale_control


@classedocente.route('/classe/<int:id_classe>', methods=['GET', 'POST'])
@teacher_required
def classe_docente(id_classe):
    # Qui ha senso salvare id_classe in session perché le ricerche AJAX (cerca-studente)
    # si appoggiano a session['id_classe'].
    session['id_classe'] = id_classe

    try:
        control = get_classe_virtuale_control()
        dati_classe = control.mostra_studenti_classe(id_classe)

        if isinstance(dati_classe, dict) and "error" in dati_classe:
            return render_template("classeDocente.html")

        return render_template("classeDocente.html", classe=dati_classe)

    except Exception as e:
        return render_template("errore.html", messaggio=f"Errore: {str(e)}")


@classedocente.route('/cerca-studente', methods=['GET'])
@teacher_required
def cerca_studente():
    query = request.args.get('query', '').strip()
    id_classe = session.get('id_classe')

    if not id_classe:
        return jsonify([])

    control = get_classe_virtuale_control()

    if query == '':
        studenti = control.mostra_studenti_classe(id_classe)
    else:
        studenti = control.cerca_studenti_classe(query, id_classe)

    return jsonify(studenti)


@classedocente.route('/cerca-studente-istituto', methods=['GET'])
@teacher_required
def cerca_studente_istituto():
    query = request.args.get('query', '').strip()
    id_classe = session.get('id_classe')

    if not id_classe:
        return jsonify([])

    control = get_classe_virtuale_control()

    if query == '':
        studenti = control.mostra_studenti_istituto("Liceo scientifico galileo galilei")
    else:
        studenti = control.cerca_studenti_istituto(query)

    return jsonify(studenti)


@classedocente.route('/classestudente/<int:id_classe>', methods=['GET', 'POST'])
@student_required
def classe_studente(id_classe):
    if id_classe == 0:
        return redirect(url_for('classedocente.no_classe'))

    try:
        control = get_classe_virtuale_control()
        dati_classe = control.mostra_studenti_classe(id_classe)

        if isinstance(dati_classe, dict) and "error" in dati_classe:
            return render_template("errore.html", messaggio=dati_classe["error"])

        return render_template("classeStudente.html", classe=dati_classe)

    except Exception as e:
        return render_template("errore.html", messaggio=f"Errore: {str(e)}")


@classedocente.route('/noclasse', methods=['GET'])
@student_required
def no_classe():
    return render_template("noClasse.html", messaggio="Nessuna classe selezionata.")


@classedocente.route('/manutenzione', methods=['GET'])
def manutenzione():
    return render_template("error404.html", messaggio="Manutenzione in corso.")


@classedocente.route('/logoaction', methods=['GET'])
def logo_action():
    return render_template("logoaction.html", messaggio="Manutenzione in corso.")


@classedocente.route('/rimuovi-studente', methods=['POST'])
@teacher_required
def rimuovi_studente_classe():
    try:
        data = request.get_json() or {}
        id_studente = data.get('id_studente')

        if not id_studente:
            return jsonify({'error': 'ID studente mancante'}), 400

        control = get_classe_virtuale_control()
        control.rimuovi_studente_classe(id_studente)

        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classedocente.route('/aggiungi-studente', methods=['POST'])
@teacher_required
def aggiungi_studente_classe():
    try:
        data = request.get_json() or {}
        id_studente = data.get('id_studente')
        id_classe = data.get('id_classe')

        if not id_studente or id_classe is None:
            return jsonify({'error': 'ID dello studente o della classe non forniti'}), 400

        control = get_classe_virtuale_control()
        result = control.aggiungi_studente_classe(id_studente, int(id_classe))

        if result:
            return jsonify({'success': True}), 200
        return jsonify({'error': "Errore durante l'aggiunta dello studente"}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
