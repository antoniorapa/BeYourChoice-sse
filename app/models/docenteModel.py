# app/models/docenteModel.py
import bcrypt
from databaseManager import DatabaseManager


class DocenteModel:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DatabaseManager()

    def aggiungi_docente(self, docente_dict: dict):
        docente_collection = self.db_manager.get_collection("Docente")
        raw_pw = docente_dict.get("password", "")
        docente_dict["password"] = bcrypt.hashpw(raw_pw.encode("utf-8"), bcrypt.gensalt())
        docente_collection.insert_one(docente_dict)

    def trova_docente(self, email: str):
        docente_collection = self.db_manager.get_collection("Docente")
        return docente_collection.find_one({"email": email})

    def trova_docente_by_codice_univoco(self, codice_univoco):
        docente_collection = self.db_manager.get_collection("Docente")
        return docente_collection.find_one({"codice_univoco": codice_univoco})

    def aggiorna_docente(self, docente_dict: dict, codice_univoco):
        docente_collection = self.db_manager.get_collection("Docente")
        docente_collection.update_one({"codice_univoco": codice_univoco}, {"$set": docente_dict})

    def elimina_docente(self, codice_univoco):
        docente_collection = self.db_manager.get_collection("Docente")
        docente_collection.delete_one({"codice_univoco": codice_univoco})

    def get_codice_univoco_by_email(self, email: str):
        docente_collection = self.db_manager.get_collection("Docente")
        doc = docente_collection.find_one({"email": email}, {"_id": 0, "codice_univoco": 1})
        return doc.get("codice_univoco") if doc else None
