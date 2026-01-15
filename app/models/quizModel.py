import uuid
from datetime import datetime, timedelta
import openai
from flask import session
from databaseManager import DatabaseManager




class QuizModel:

    db_manager = DatabaseManager(db_name="BeYourChoice;")

    @staticmethod
    def parse_domanda(domanda_testo):
        """Elabora il testo della domanda generata da OpenAI per estrarre i dettagli."""
        try:
            domanda_lines = domanda_testo.strip().split("\n")

            if len(domanda_lines) < 3:
                raise ValueError("Formato della domanda non valido.")

            testo_domanda = domanda_lines[0].strip()

            opzioni_risposte = [
                line.strip() for line in domanda_lines[1:] if line.startswith(("A)", "B)", "C)", "D)"))
            ]

            risposta_corretta = next(
                (line.replace("Risposta corretta:", "").strip() for line in domanda_lines if
                 "Risposta corretta:" in line),
                None
            )

            if not testo_domanda or not opzioni_risposte or not risposta_corretta:
                raise ValueError("Alcuni componenti essenziali della domanda sono mancanti.")

            opzioni_risposte = [
                opzione.replace("A)", "").replace("B)", "").replace("C)", "").replace("D)", "").strip()
                for opzione in opzioni_risposte
            ]

            return {
                "testo_domanda": testo_domanda,
                "opzioni_risposte": opzioni_risposte,
                "risposta_corretta": risposta_corretta
            }
        except Exception as e:
            raise ValueError(f"Errore nel parsing della domanda: {e}")

    @staticmethod
    def genera_domande(tema, numero_domande, modalita_risposta, api_key):
        """Genera domande utilizzando OpenAI GPT (con gestione robusta della API key e retry)."""
        # Validazione input
        if not tema or not str(tema).strip():
            raise ValueError("Tema mancante o non valido.")
        try:
            numero_domande = int(numero_domande)
        except Exception:
            raise ValueError("Numero domande non valido.")
        if numero_domande <= 0:
            raise ValueError("Numero domande deve essere > 0.")

        # Se la key non c'è, non provare nemmeno la chiamata (evita errore OpenAI)
        if not api_key or not str(api_key).strip():
            raise ValueError(
                "Generazione automatica non disponibile: API key OpenAI mancante. "
                "Inserisci una API key valida oppure crea il quiz manualmente."
            )

        openai.api_key = str(api_key).strip()

        prompt_base = f"Genera una domanda sul tema: {tema}. "
        if modalita_risposta == "3_risposte":
            prompt_base += "La domanda deve avere 3 opzioni di risposta: una corretta e due sbagliate."
        elif modalita_risposta == "4_risposte":
            prompt_base += "La domanda deve avere 4 opzioni di risposta: una corretta e tre sbagliate."
        else:
            # fallback sensato
            prompt_base += "La domanda deve avere 4 opzioni di risposta: una corretta e tre sbagliate."

        domande = []
        # Evita loop infinito: mettiamo un tetto ai tentativi
        max_attempts = max(10, numero_domande * 5)
        attempts = 0

        while len(domande) < numero_domande and attempts < max_attempts:
            attempts += 1
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Sei un assistente esperto in educazione civica italiana. "
                        "Genera domande educative e coinvolgenti adatte al livello delle scuole superiori. "
                        "Formato richiesto:\n"
                        "1) Prima riga: testo domanda\n"
                        "2) Righe successive: A) ... B) ... C) ... (D) ...\n"
                        "3) Ultima riga: Risposta corretta: <LETTERA>) <testo>\n"
                    ),
                },
                {"role": "user", "content": prompt_base},
            ]

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=220,
                    temperature=0.7,
                )
                domanda_txt = response.choices[0].message["content"].strip()

                # Parsing robusto
                parsed = QuizModel.parse_domanda(domanda_txt)

                # Dedup (evita domande identiche se il modello ripete)
                key = (parsed.get("testo_domanda", "").lower().strip())
                if key and all(d.get("testo_domanda", "").lower().strip() != key for d in domande):
                    domande.append(parsed)

            except ValueError:
                # parsing fallito: riprova fino a max_attempts
                continue
            except Exception as e:
                # qualunque altro errore OpenAI: interrompi con messaggio chiaro
                raise ValueError(f"Errore OpenAI: {e}")

        if len(domande) < numero_domande:
            raise ValueError(
                f"Impossibile generare {numero_domande} domande valide. "
                f"Domande generate: {len(domande)}. Riprova o crea il quiz manualmente."
            )

        return domande

    @staticmethod
    def salva_quiz(data):
        """Salva un quiz e le sue domande nel database, generando un ID decimale."""
        try:
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")
            questions_collection = QuizModel.db_manager.get_collection("Domanda")

            # Genera un ID numerico decimale basato sull'ultimo ID nel database
            ultimo_quiz = quiz_collection.find_one(sort=[("id_quiz", -1)])
            nuovo_id = float(ultimo_quiz["id_quiz"] + 1) if ultimo_quiz else 1.0

            id_classe = session.get("id_classe")
            if not id_classe:
                raise ValueError("ID Classe mancante nella sessione.")

            # Prepara il documento del quiz
            quiz = {
                "id_quiz": nuovo_id,
                "titolo": data["titolo"],
                "argomento": data["argomento"],
                "n_domande": data["n_domande"],
                "domande": data["domande"],
                "modalita_quiz": data["modalita_quiz"],
                "durata": data["durata"],
                "data_creazione": data["data_creazione"],
                "id_classe": id_classe
            }

            # Inserisci il quiz nel database
            quiz_collection.insert_one(quiz)

            # Inserisci ogni domanda associata al quiz
            for domanda in data["domande"]:
                risposta_corretta = domanda["risposta_corretta"].split(")", 1)[-1].strip()
                question = {
                    "id_domanda": domanda["id_domanda"],
                    "testo_domanda": domanda["testo_domanda"],
                    "opzioni_risposte": domanda["opzioni_risposte"],
                    "risposta_corretta": risposta_corretta,
                    "id_quiz": nuovo_id  # Associa l'ID del quiz
                }
                questions_collection.insert_one(question)
        except Exception as e:
            raise ValueError(f"Errore durante il salvataggio del quiz: {e}")

    @staticmethod
    def recupera_domande(lista_id_domande):
        """Recupera le domande dalla Collection `Domanda` in base agli ID."""
        try:
            questions_collection = QuizModel.db_manager.get_collection("Domanda")
            domande = list(questions_collection.find({"id_domanda": {"$in": lista_id_domande}}))
            # Verifica che le opzioni di risposta siano presenti
            for domanda in domande:
                if "opzioni_risposta" not in domanda:
                    domanda["opzioni_risposta"] = []  # Fallback per evitare errori
            return domande
        except Exception as e:
            raise ValueError(f"Errore durante il recupero delle domande: {e}")

    @staticmethod
    def recupera_quiz(quiz_id):
        """Recupera un quiz in base al suo ID."""
        try:
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")
            quiz = quiz_collection.find_one({"id_quiz": quiz_id})
            if not quiz:
                raise ValueError("Quiz non trovato.")
            return quiz
        except Exception as e:
            raise ValueError(f"Errore durante il recupero del quiz: {e}")

    @staticmethod
    def recupera_quiz_per_classe(id_classe):
        """Recupera tutti i quiz per una classe specifica."""
        try:
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")

            # Debug per verificare id_classe
            print(f"DEBUG: id_classe = {id_classe}, tipo = {type(id_classe)}")

            # Effettua la query
            quiz_list = list(quiz_collection.find({"id_classe": id_classe}))

            # Converti _id in stringa per compatibilità
            for quiz in quiz_list:
                if "_id" in quiz:
                    quiz["_id"] = str(quiz["_id"])

            return quiz_list
        except Exception as e:
            raise ValueError(f"Errore durante il recupero dei quiz: {e}")

    @staticmethod
    def recupera_risultati_per_quiz(quiz_id):
        """Recupera i risultati di un quiz."""
        try:
            risultati_collection = QuizModel.db_manager.get_collection("RisultatoQuiz")
            return list(risultati_collection.find({"id_quiz": quiz_id}))
        except Exception as e:
            raise ValueError(f"Errore durante il recupero dei risultati: {e}")

    @staticmethod
    def recupera_ultimo_quiz(id_classe, cf_studente):
        """Recupera l'ultimo quiz non completato da uno studente."""
        try:
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")
            dashboard_collection = QuizModel.db_manager.get_collection("Dashboard")

            ultimo_quiz = quiz_collection.find_one(
                {"id_classe": id_classe},
                sort=[("data_creazione", -1)]
            )

            if not ultimo_quiz:
                return None

            completato = dashboard_collection.find_one({
                "cf_studente": cf_studente,
                "descrizione_attivita": {"$regex": f"Completamento Quiz: {ultimo_quiz['titolo']}"}
            })

            return None if completato else ultimo_quiz
        except Exception as e:
            raise ValueError(f"Errore durante il recupero dell'ultimo quiz: {e}")

    @staticmethod
    def recupera_studenti_classe(id_classe):
        """Recupera tutti gli studenti di una classe."""
        try:
            studenti_collection = QuizModel.db_manager.get_collection("Studente")
            return list(studenti_collection.find({"id_classe": id_classe}))
        except Exception as e:
            raise ValueError(f"Errore durante il recupero degli studenti: {e}")

    @staticmethod
    def recupera_attività_completate(titolo_quiz):
        """
        Recupera le attività completate per un determinato quiz basandosi sul titolo del quiz.
        :param titolo_quiz: Titolo del quiz
        :return: Lista di attività completate
        """
        try:
            dashboard_collection = QuizModel.db_manager.get_collection("Dashboard")
            return list(dashboard_collection.find({
                "descrizione_attivita": {"$regex": f"Completamento Quiz: {titolo_quiz}"}
            }))
        except Exception as e:
            raise ValueError(f"Errore durante il recupero delle attività completate: {e}")

    @staticmethod
    def calcola_tempo_rimanente(quiz_id, cf_studente):
        """
        Calcola il tempo rimanente per un quiz specifico.
        """
        quiz_collection = QuizModel.db_manager.get_collection("Quiz")

        # Recupera l'ora di inizio dal database o impostala
        sessione = quiz_collection.find_one({"id_quiz": quiz_id, "cf_studente": cf_studente})
        ora_attuale = datetime.utcnow()

        if not sessione:
            # Se la sessione non esiste, creala
            ora_inizio = ora_attuale
        else:
            ora_inizio = sessione["Ora_Inizio"]

        # Recupera la durata del quiz
        quiz = quiz_collection.find_one({"id_quiz": quiz_id})
        durata_quiz = quiz["durata"] if quiz else 30  # Default a 30 minuti

        # Calcola il tempo rimanente in secondi
        fine_quiz = ora_inizio + timedelta(minutes=durata_quiz)
        tempo_rimanente = max(0, int((fine_quiz - ora_attuale).total_seconds()))

        return tempo_rimanente

    @staticmethod
    def salva_risultato_quiz(risultato_quiz, cf_studente, punteggio):
        """
        Salva il risultato del quiz nel database e registra l'attività nella dashboard.
        :param quiz_result: Dati del risultato del quiz da salvare.
        :param cf_studente: Codice fiscale dello studente.
        :param punteggio: Punteggio ottenuto dallo studente.
        """
        try:
            # Collezioni necessarie
            quiz_results_collection = QuizModel.db_manager.get_collection("RisultatoQuiz")
            attività_collection = QuizModel.db_manager.get_collection("Dashboard")
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")

            # Salva il risultato del quiz
            quiz_results_collection.insert_one(risultato_quiz)

            # Recupera il titolo del quiz
            quiz = quiz_collection.find_one({"id_quiz": risultato_quiz["id_quiz"]}, {"titolo": 1})
            if not quiz:
                raise ValueError(f"Quiz con ID {risultato_quiz['id_quiz']} non trovato.")
            titolo_quiz = quiz["titolo"]

            # Genera l'attività svolta
            attività = {
                "id_attivita": attività_collection.count_documents({}) + 1,  # Genera un ID incrementale
                "data_attivita": datetime.utcnow(),
                "descrizione_attivita": f"Completamento Quiz: {titolo_quiz}",
                "punteggio_attivita": punteggio,
                "cf_studente": cf_studente
            }

            # Inserisce l'attività nella dashboard
            attività_collection.insert_one(attività)
            print(f"DEBUG: Risultato del quiz e attività salvati correttamente per lo studente {cf_studente}")
        except Exception as e:
            raise ValueError(f"Errore durante il salvataggio del risultato: {e}")

    @staticmethod
    def verifica_completamento_quiz(quiz_id, cf_studente):
        """
        Verifica se uno studente ha già completato un quiz specifico.
        """
        try:
            risultati_collection = QuizModel.db_manager.get_collection("RisultatoQuiz")
            risultato = risultati_collection.find_one({"id_quiz": quiz_id, "cf_studente": cf_studente})
            return risultato is not None  # Restituisce True se il quiz è completato
        except Exception as e:
            print(f"ERRORE durante la verifica del completamento del quiz: {e}")
            return False

    @staticmethod
    def verifica_titolo(titolo):
        """Verifica se il titolo del quiz esiste già nel database."""
        try:
            quiz_collection = QuizModel.db_manager.get_collection("Quiz")
            # Cerca un documento con il titolo specificato
            return quiz_collection.find_one({"titolo": titolo}) is not None
        except Exception as e:
            raise ValueError(f"Errore durante la verifica del titolo: {e}")

