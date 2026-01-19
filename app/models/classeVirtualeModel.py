# app/models/classeVirtualeModel.py
import re
import logging
from bson import ObjectId
from flask import session
from databaseManager import DatabaseManager

logger = logging.getLogger(__name__)

NOME_CLASSE_RE = re.compile(r"^[A-Za-zÀ-ú‘’',\(\)\s0-9]{2,20}$")
DESCRIZIONE_RE = re.compile(r"^[a-zA-Z0-9 ]{2,255}$")


class ClasseVirtuale:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()

    def _next_id_classe(self) -> int:
        """
        ID incrementale in modo atomico (safe anche con più richieste concorrenti).
        """
        counter_collection = self.db_manager.get_collection("counters")
        counter = counter_collection.find_one_and_update(
            {"_id": "ClasseVirtuale"},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=True
        )
        return int(counter["sequence_value"])

    def creazione_classe_virtuale(self, nome_classe, descrizione, id_docente):
        try:
            if not (2 <= len(nome_classe) <= 20) or not NOME_CLASSE_RE.match(nome_classe):
                raise ValueError("Formato o lunghezza del nome classe non corretti.")

            if not (2 <= len(descrizione) <= 255) or not DESCRIZIONE_RE.match(descrizione):
                raise ValueError("Formato o lunghezza della descrizione non corretti.")

            collection = self.db_manager.get_collection("ClasseVirtuale")
            id_classe = self._next_id_classe()

            documento = {
                "id_classe": id_classe,
                "nome_classe": nome_classe,
                "descrizione": descrizione,
                "id_docente": id_docente
            }

            collection.insert_one(documento)
            return True

        except Exception as e:
            logger.exception("Errore creazione classe: %s", e)
            return False

    def rimuovi_studente_classe(self, id_studente):
        studente_collection = self.db_manager.get_collection("Studente")
        result = studente_collection.update_one(
            {"_id": ObjectId(id_studente)},
            {"$set": {"id_classe": None}}
        )
        if result.modified_count == 0:
            raise ValueError("Nessuna modifica effettuata. Verifica l'ID dello studente.")

    def aggiungi_studente_classe(self, id_studente, id_classe):
        studente_collection = self.db_manager.get_collection("Studente")

        studente = studente_collection.find_one({"_id": ObjectId(id_studente)}, {"_id": 1})
        if not studente:
            return False

        result = studente_collection.update_one(
            {"_id": ObjectId(id_studente)},
            {"$set": {"id_classe": id_classe}}
        )
        return result.modified_count > 0

    def mostra_studenti_classe(self, id_classe):
        studente_collection = self.db_manager.get_collection("Studente")

        studenti = list(studente_collection.find(
            {"id_classe": id_classe},
            {"nome": 1, "cognome": 1, "data_nascita": 1}
        ).sort([("cognome", 1), ("nome", 1)]))

        if not studenti:
            raise ValueError(f"Nessuno studente trovato per la classe con ID {id_classe}")

        return [
            {
                "Nome": s.get("nome", "N/A"),
                "Cognome": s.get("cognome", "N/A"),
                "Data_Nascita": s.get("data_nascita", "N/A"),
                "_id": str(s["_id"])
            }
            for s in studenti
        ]

    def mostra_studenti_istituto(self, scuola_appartenenza):
        studente_collection = self.db_manager.get_collection("Studente")

        studenti = list(studente_collection.find(
            {
                "sda": scuola_appartenenza,
                "$or": [{"id_classe": {"$exists": False}}, {"id_classe": None}]
            },
            {"nome": 1, "cognome": 1, "data_nascita": 1}
        ).sort([("cognome", 1), ("nome", 1)]))

        if not studenti:
            raise ValueError(f"Nessuno studente trovato per la scuola: {scuola_appartenenza}")

        return [
            {
                "Nome": s.get("nome", "N/A"),
                "Cognome": s.get("cognome", "N/A"),
                "Data_Nascita": s.get("data_nascita", "N/A"),
                "_id": str(s["_id"])
            }
            for s in studenti
        ]

    def cerca_studenti_classe(self, query, id_classe):
        collection = self.db_manager.get_collection("Studente")

        filtro = {"id_classe": id_classe}
        if query:
            filtro["cf"] = {"$regex": query, "$options": "i"}

        studenti = list(collection.find(
            filtro,
            {"nome": 1, "cognome": 1, "data_nascita": 1}
        ).sort([("cognome", 1), ("nome", 1)]))

        return [
            {
                "Nome": s.get("nome", "N/A"),
                "Cognome": s.get("cognome", "N/A"),
                "Data_Nascita": s.get("data_nascita", "N/A"),
                "_id": str(s["_id"])
            }
            for s in studenti
        ]

    def cerca_studenti_istituto(self, query):
        sda = session.get("sda")
        collection = self.db_manager.get_collection("Studente")

        filtro = {
            "sda": sda,
            "$or": [{"id_classe": {"$exists": False}}, {"id_classe": None}]
        }
        if query:
            filtro["cf"] = {"$regex": query, "$options": "i"}

        studenti = list(collection.find(
            filtro,
            {"nome": 1, "cognome": 1, "data_nascita": 1}
        ).sort([("cognome", 1), ("nome", 1)]))

        return [
            {
                "Nome": s.get("nome", "N/A"),
                "Cognome": s.get("cognome", "N/A"),
                "Data_Nascita": s.get("data_nascita", "N/A"),
                "_id": str(s["_id"])
            }
            for s in studenti
        ]
