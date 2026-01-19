# app/models/studenteModel.py
import logging
import bcrypt
from databaseManager import DatabaseManager

logger = logging.getLogger(__name__)


class StudenteModel:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()

    def aggiungi_studente(self, studente_dict: dict):
        studente_collection = self.db_manager.get_collection("Studente")

        # cifra password
        raw_pw = studente_dict.get("password", "")
        studente_dict["password"] = bcrypt.hashpw(raw_pw.encode("utf-8"), bcrypt.gensalt())

        studente_collection.insert_one(studente_dict)

    def trova_studente(self, email: str):
        """
        Restituisce documento studente per email.
        Nota: qui serve anche la password (login), quindi niente projection.
        """
        studente_collection = self.db_manager.get_collection("Studente")
        return studente_collection.find_one({"email": email})

    def trova_cf_per_email(self, email: str):
        """
        Ottimizzato: prende solo cf.
        """
        studente_collection = self.db_manager.get_collection("Studente")
        doc = studente_collection.find_one({"email": email}, {"_id": 0, "cf": 1})
        return doc.get("cf") if doc else None
