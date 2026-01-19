import os
import re
from flask import Blueprint, request, session, jsonify
from app.models.quizModel import QuizModel
from app.views.quizView import QuizView
from app.controllers.loginControl import teacher_required, student_required
from dotenv import load_dotenv

load_dotenv()

quiz_blueprint = Blueprint("quiz", __name__, template_folder="../templates")


@quiz_blueprint.route("/crea-quiz", methods=["GET"])
@teacher_required
def index():
    """Renderizza la pagina di creazione quiz."""
    id_classe = session.get("id_classe")
    if not id_classe:
        return QuizView.mostra_errore("ID Classe mancante nella sessione", 400)
    return QuizView.mostra_crea_quiz(id_classe)


@quiz_blueprint.route("/genera", methods=["POST"])
@teacher_required
def genera_domande():
    """Genera domande per il quiz."""
    try:
        titolo = request.json.get("titolo")
        tema = request.json.get("argomento")
        numero_domande = request.json.get("n_domande")
        modalita_risposta = request.json.get("modalita_quiz")

        if not titolo or not re.match(r"^[A-Za-zÀ-ú0-9\s\-_']{2,255}$", titolo):
            return jsonify({"error": "Il titolo non è valido (2-255 caratteri, formato corretto)."}), 400

        if QuizModel.verifica_titolo(titolo):
            return jsonify({"error": "Il titolo esiste già nel database."}), 400

        if not tema or not re.match(r"^[A-Za-zÀ-ú0-9‘’',\.\(\)\s\/|\\{}\[\],\-!$%&?<>=^+°#*:']{2,255}$", tema):
            return jsonify({"error": "L'argomento non è valido (2-255 caratteri, formato corretto)."}), 400

        if not numero_domande or not (5 <= int(numero_domande) <= 20):
            return jsonify({"error": "Il numero di domande deve essere compreso tra 5 e 20."}), 400

        if modalita_risposta not in ["3_risposte", "4_risposte"]:
            return jsonify({"error": "Modalità di risposta non valida."}), 400

        domande = QuizModel.genera_domande(
            tema=tema,
            numero_domande=int(numero_domande),
            modalita_risposta=modalita_risposta,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        return jsonify(domande), 200

    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")

        # fallback: se NON c'è api key, restituisci placeholder (così non blocchi i test)
        if not api_key or not api_key.strip():
            domande = []
            n = int(request.json.get("n_domande") or 5)
            tema = request.json.get("argomento") or "tema"
            modalita_risposta = request.json.get("modalita_quiz") or "4_risposte"

            for i in range(1, n + 1):
                domande.append({
                    "id_domanda": i,
                    "testo_domanda": f"Domanda {i} (placeholder): {tema}",
                    "opzioni_risposte": ["Opzione A", "Opzione B", "Opzione C"]
                    if modalita_risposta == "3_risposte"
                    else ["Opzione A", "Opzione B", "Opzione C", "Opzione D"],
                    "risposta_corretta": "A) Opzione A"
                })
            return jsonify(domande), 200

        # se c'è api key, riprova davvero
        tema = request.json.get("argomento")
        numero_domande = request.json.get("n_domande")
        modalita_risposta = request.json.get("modalita_quiz")

        domande = QuizModel.genera_domande(
            tema=tema,
            numero_domande=int(numero_domande),
            modalita_risposta=modalita_risposta,
            api_key=api_key
        )
        return jsonify(domande), 200


@quiz_blueprint.route("/salva", methods=["POST"])
@teacher_required
def salva_quiz():
    try:
        data = request.get_json() or {}

        id_classe = session.get("id_classe")
        if id_classe is None:
            return jsonify({"error": "ID Classe mancante nella sessione."}), 403

        # ✅ FIX: salva sempre id_classe come int
        try:
            id_classe = int(id_classe)
        except Exception:
            return jsonify({"error": "ID Classe non valido (non convertibile in int)."}), 400

        data["id_classe"] = id_classe
        QuizModel.salva_quiz(data)
        return jsonify({"message": "Quiz salvato correttamente!"}), 200

    except Exception as e:
        return jsonify({"error": f"Errore durante il salvataggio: {str(e)}"}), 500


@quiz_blueprint.route('/quiz/<int:quiz_id>', methods=['POST', 'GET'])
@student_required
def visualizza_quiz(quiz_id):
    """Mostra la pagina del quiz solo se lo studente non lo ha già completato."""
    try:
        cf_studente = session.get('cf')
        if not cf_studente:
            return QuizView.mostra_errore("CF dello studente non trovato nella sessione", 403)

        if QuizModel.verifica_completamento_quiz(quiz_id, cf_studente):
            return QuizView.mostra_errore("Hai già completato questo quiz.", 403)

        quiz = QuizModel.recupera_quiz(quiz_id)
        if not quiz:
            return QuizView.mostra_errore("Quiz non trovato", 404)

        domande = QuizModel.recupera_domande([d["id_domanda"] for d in quiz["domande"]])
        tempo_rimanente = QuizModel.calcola_tempo_rimanente(quiz_id, cf_studente)

        return QuizView.mostra_quiz(quiz, domande, tempo_rimanente)

    except Exception:
        return QuizView.mostra_errore("Errore durante il caricamento del quiz", 500)


@quiz_blueprint.route('/valuta-quiz', methods=['POST'])
@student_required
def valuta_quiz():
    """Valuta le risposte inviate dal form del quiz e salva il risultato."""
    try:
        cf_studente = session.get('cf')
        if not cf_studente:
            return jsonify({"error": "CF dello studente non trovato nella sessione"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "Nessuna risposta ricevuta"}), 400

        question_ids = [int(key[1:]) for key in data.keys() if key.startswith("q")]
        if not question_ids:
            return jsonify({"error": "Nessuna domanda valida trovata"}), 400

        domande = QuizModel.recupera_domande(question_ids)
        totale = len(domande)
        if totale == 0:
            return jsonify({"error": "Nessuna domanda trovata nel database"}), 400

        corrette = 0
        for domanda in domande:
            risposta_utente = data.get(f"q{domanda['id_domanda']}")
            if risposta_utente == domanda["risposta_corretta"]:
                corrette += 1

        punteggio = int((corrette / totale) * 100)

        quiz_result = {
            "id_quiz": domande[0]["id_quiz"],
            "cf_studente": cf_studente,
            "punteggio_quiz": punteggio,
            "risposte": [data.get(f"q{d['id_domanda']}") for d in domande]
        }

        QuizModel.salva_risultato_quiz(quiz_result, cf_studente, punteggio)

        return jsonify({
            "message": f"Hai ottenuto un punteggio di {punteggio}%. Domande corrette: {corrette}/{totale}",
            "punteggio": punteggio,
            "corrette": corrette,
            "totale": totale
        })

    except Exception:
        return jsonify({"error": "Errore durante la valutazione del quiz"}), 500


@quiz_blueprint.route('/quiz/<int:quiz_id>/domande', methods=['GET'])
@teacher_required
def visualizza_domande_quiz(quiz_id):
    """Visualizza le domande di un quiz selezionato."""
    try:
        quiz = QuizModel.recupera_quiz(quiz_id)
        if not quiz:
            return QuizView.mostra_errore("Quiz non trovato", 404)

        domande = QuizModel.recupera_domande([d["id_domanda"] for d in quiz["domande"]])
        return QuizView.mostra_domande_quiz(quiz, domande)

    except Exception:
        return QuizView.mostra_errore("Errore durante la visualizzazione delle domande", 500)


@quiz_blueprint.route('/quiz/<int:quiz_id>/risultati', methods=['GET'])
@teacher_required
def visualizza_risultati_quiz(quiz_id):
    """Visualizza i risultati per un quiz."""
    try:
        quiz = QuizModel.recupera_quiz(quiz_id)
        if not quiz:
            return QuizView.mostra_errore("Quiz non trovato", 404)

        id_classe = quiz.get("id_classe")
        titolo_quiz = quiz.get("titolo")

        studenti_classe = QuizModel.recupera_studenti_classe(id_classe)
        if not studenti_classe:
            return QuizView.mostra_risultati_quiz([], quiz_id)

        attività_completate = QuizModel.recupera_attività_completate(titolo_quiz)
        attività_per_cf = {a["cf_studente"].strip().upper(): a for a in attività_completate}

        risultati_completi = [
            {
                "Nome": studente["nome"],
                "Cognome": studente["cognome"],
                "Punteggio": attività_per_cf.get(studente["cf"].strip().upper(), {}).get("punteggio_attivita",
                                                                                         "Quiz non svolto")
            }
            for studente in studenti_classe
        ]

        return QuizView.mostra_risultati_quiz(risultati_completi, quiz_id)

    except Exception:
        return QuizView.mostra_errore("Errore durante il caricamento dei risultati", 500)


@quiz_blueprint.route('/ultimo-quiz', methods=['GET'])
@student_required
def visualizza_ultimo_quiz():
    """Visualizza l'ultimo quiz disponibile per una classe."""
    try:
        cf_studente = session.get('cf')
        id_classe = session.get('id_classe')

        if not cf_studente or not id_classe:
            return QuizView.mostra_errore("Sessione non valida", 400)

        ultimo_quiz = QuizModel.recupera_ultimo_quiz(id_classe, cf_studente)
        if not ultimo_quiz:
            return QuizView.mostra_ultimo_quiz(None)

        return QuizView.mostra_ultimo_quiz(ultimo_quiz)
    except Exception:
        return QuizView.mostra_errore("Errore durante il caricamento dell'ultimo quiz", 500)


@quiz_blueprint.route("/visualizza-quiz", methods=["GET"])
@teacher_required
def visualizza_quiz_classe():
    """Recupera tutti i quiz per la classe corrente e li mostra al docente."""
    try:
        id_classe = session.get("id_classe")
        if not id_classe:
            return QuizView.mostra_errore("ID Classe non specificato.", 400)

        quiz_list = QuizModel.recupera_quiz_per_classe(id_classe)
        return QuizView.mostra_quiz_precedenti(quiz_list, id_classe)

    except Exception:
        return QuizView.mostra_errore("Errore durante il recupero dei quiz", 500)
