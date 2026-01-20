import re
from flask import jsonify
from app.models.scenarioModel import ScenarioModel

class scenarioControl:
    @staticmethod
    def registra_scenario(id, titolo, descrizione, modalita, argomento):
        try:
            # Validazione dei campi
            if not titolo or not descrizione or not argomento or not modalita:
                return {"error": "DatiObbligatori"}

            # Validazioni dei campi
            titolo_regex = r"^[A-Za-z\s]{2,50}$"
            descrizione_regex = r"^[^§]{2,255}$"

            if not re.match(titolo_regex, titolo):
                return {"error": "formatoTitolo"}

            if not re.match(descrizione_regex, descrizione):
                return {"error": "formatoDescrizione"}

            argomento_options = [
                "Politiche per il cambiamento climatico",
                "Parità di genere",
                "Diritti dei migranti",
                "Intelligenza artificiale nella medicina",
                "Legalizzazione delle droghe leggere",
                "Espansione della NATO",
                "Sicurezza sul lavoro"
            ]

            if argomento not in argomento_options:
                return {"error": "argomentoNonValido"}

            # Creazione dello scenario
            scenario_dict = {
                'id_scenario': id,
                "titolo": titolo,
                "descrizione": descrizione,
                "argomento": argomento,
                "modalità": modalita
            }

            scenario_model = ScenarioModel()
            scenario_model.aggiungi_scenario(scenario_dict)

            return {"success": True}

        except Exception as e:
            return {"error": f"Errore interno: {str(e)}"}