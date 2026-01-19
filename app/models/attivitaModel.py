# app/models/attivitaModel.py
from datetime import datetime
import logging
from databaseManager import DatabaseManager

logger = logging.getLogger(__name__)


class Attivita:
    """
    Gestisce operazioni relative alle attività/punteggi degli utenti.
    """

    def __init__(self, db_manager=None):
        # evita variabili di classe (init a import-time) e facilita test
        self.db_manager = db_manager or DatabaseManager()

    def get_classifica_classe(self, id_classe: int):
        """
        Recupera classifica della classe con punteggio totale (scenario + quiz).
        Ottimizzato: filtra su soli studenti della classe.
        """
        try:
            studente_col = self.db_manager.get_collection("Studente")
            scenario_col = self.db_manager.get_collection("PunteggioScenario")
            quiz_col = self.db_manager.get_collection("RisultatoQuiz")

            # prendo solo i campi necessari
            studenti = list(studente_col.find(
                {"id_classe": id_classe},
                {"_id": 0, "cf": 1, "nome": 1, "cognome": 1}
            ))
            if not studenti:
                return []

            cf_studenti = [s["cf"] for s in studenti if s.get("cf")]
            if not cf_studenti:
                return []

            punteggi_totali = {cf: {"punteggio_scenario": 0, "punteggio_quiz": 0} for cf in cf_studenti}

            # Somma scenari SOLO per CF della classe
            scenari_punteggi = scenario_col.aggregate([
                {"$match": {"CF_Studente": {"$in": cf_studenti}}},
                {"$group": {"_id": "$CF_Studente", "punteggio_scenario": {"$sum": "$Punteggio_Scenario"}}},
            ])
            for item in scenari_punteggi:
                cf = item["_id"]
                if cf in punteggi_totali:
                    punteggi_totali[cf]["punteggio_scenario"] = item.get("punteggio_scenario", 0)

            # Somma quiz SOLO per CF della classe
            quiz_punteggi = quiz_col.aggregate([
                {"$match": {"cf_studente": {"$in": cf_studenti}}},
                {"$group": {"_id": "$cf_studente", "punteggio_quiz": {"$sum": "$punteggio_quiz"}}},
            ])
            for item in quiz_punteggi:
                cf = item["_id"]
                if cf in punteggi_totali:
                    punteggi_totali[cf]["punteggio_quiz"] = item.get("punteggio_quiz", 0)

            # costruisco output
            classifica = []
            for s in studenti:
                cf = s["cf"]
                p_s = punteggi_totali.get(cf, {}).get("punteggio_scenario", 0)
                p_q = punteggi_totali.get(cf, {}).get("punteggio_quiz", 0)
                classifica.append({
                    "cf": cf,
                    "nome": s.get("nome", ""),
                    "cognome": s.get("cognome", ""),
                    "punteggio_totale": p_s + p_q
                })

            classifica.sort(key=lambda x: x["punteggio_totale"], reverse=True)
            return classifica

        except Exception as e:
            logger.exception("Errore nel recupero classifica: %s", e)
            return []

    def get_punteggio_personale(self, cf_studente: str):
        """
        Recupera punteggio personale (quiz + scenari) per studente.
        Fix: non consumare il cursore con list() di debug.
        """
        try:
            scenario_col = self.db_manager.get_collection("PunteggioScenario")
            quiz_col = self.db_manager.get_collection("RisultatoQuiz")

            scenario_cursor = scenario_col.aggregate([
                {"$match": {"CF_Studente": cf_studente}},
                {"$group": {"_id": "$CF_Studente", "PunteggioScenari": {"$sum": "$Punteggio_Scenario"}}}
            ])
            scenario_doc = next(scenario_cursor, None)
            punteggio_scenari = scenario_doc.get("PunteggioScenari", 0) if scenario_doc else 0

            quiz_cursor = quiz_col.aggregate([
                {"$match": {"cf_studente": cf_studente}},
                {"$group": {"_id": "$cf_studente", "punteggio_quiz": {"$sum": "$punteggio_quiz"}}}
            ])
            quiz_doc = next(quiz_cursor, None)
            punteggio_quiz = quiz_doc.get("punteggio_quiz", 0) if quiz_doc else 0

            return {"punteggio_quiz": punteggio_quiz, "PunteggioScenari": punteggio_scenari}

        except Exception as e:
            logger.exception("Errore nel calcolo punteggio personale: %s", e)
            return {"punteggio_quiz": 0, "PunteggioScenari": 0}

    def get_storico(self, cf_studente: str):
        """
        Recupera storico attività studente.
        """
        try:
            dashboard_col = self.db_manager.get_collection("Dashboard")
            attivita = list(dashboard_col.find(
                {"cf_studente": cf_studente},
                {"_id": 0, "id_attivita": 1, "data_attivita": 1, "descrizione_attivita": 1, "punteggio_attivita": 1}
            ))

            for a in attivita:
                dt = a.get("data_attivita")
                if isinstance(dt, datetime):
                    a["data_attivita"] = dt.strftime("%d/%m/%Y %H:%M:%S")

            return attivita

        except Exception as e:
            logger.exception("Errore recupero storico: %s", e)
            return []

    def get_classi_docente(self, id_docente):
        """
        Recupera classi docente e punteggio totale per classe.
        Ottimizzato: evita aggregazioni globali e riduce query.
        """
        try:
            classi_col = self.db_manager.get_collection("ClasseVirtuale")
            studente_col = self.db_manager.get_collection("Studente")
            quiz_col = self.db_manager.get_collection("RisultatoQuiz")
            scenario_col = self.db_manager.get_collection("PunteggioScenario")

            classi = list(classi_col.find(
                {"id_docente": id_docente},
                {"_id": 0, "id_classe": 1, "nome_classe": 1}
            ))
            if not classi:
                return []

            # Per ciascuna classe serve lista CF studenti. (Qui potresti ottimizzare ulteriormente
            # con una pipeline aggregata, ma già così eviti sprechi grossi.)
            for classe in classi:
                id_classe = classe["id_classe"]

                studenti = list(studente_col.find({"id_classe": id_classe}, {"_id": 0, "cf": 1}))
                cf_studenti = [s["cf"] for s in studenti if s.get("cf")]

                if not cf_studenti:
                    classe["punteggio_totale"] = 0
                    continue

                quiz_cursor = quiz_col.aggregate([
                    {"$match": {"cf_studente": {"$in": cf_studenti}}},
                    {"$group": {"_id": None, "totale_quiz": {"$sum": "$punteggio_quiz"}}}
                ])
                punteggio_quiz_totale = (next(quiz_cursor, {}) or {}).get("totale_quiz", 0)

                scenario_cursor = scenario_col.aggregate([
                    {"$match": {"CF_Studente": {"$in": cf_studenti}}},
                    {"$group": {"_id": None, "totale_scenario": {"$sum": "$Punteggio_Scenario"}}}
                ])
                punteggio_scenario_totale = (next(scenario_cursor, {}) or {}).get("totale_scenario", 0)

                classe["punteggio_totale"] = punteggio_quiz_totale + punteggio_scenario_totale

            classi.sort(key=lambda x: x.get("punteggio_totale", 0), reverse=True)
            return classi

        except Exception as e:
            logger.exception("Errore recupero classi docente: %s", e)
            return []
