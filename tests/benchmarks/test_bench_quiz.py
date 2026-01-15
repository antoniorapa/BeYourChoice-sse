# tests/benchmarks/test_bench_quiz.py
import re
import pytest
from datetime import datetime, timedelta
from app.models.quizModel import QuizModel

# Regex prese dal tuo quizController.py
TITOLO_REGEX = r"^[A-Za-zÀ-ú0-9\s\-_']{2,255}$"
TEMA_REGEX = r"^[A-Za-zÀ-ú0-9‘’',\.\(\)\s\/|\\{}\[\],\-!$%&?<>=^+°#*:']{2,255}$"

TITOLO_RE = re.compile(TITOLO_REGEX)
TEMA_RE = re.compile(TEMA_REGEX)

SAMPLE_DOMANDA_TXT_3 = """Qual è la capitale d'Italia?
A) Roma
B) Milano
C) Napoli
Risposta corretta: A) Roma
"""

@pytest.mark.benchmark(group="quiz")
def test_bench_parse_domanda(benchmark):
    def run():
        return QuizModel.parse_domanda(SAMPLE_DOMANDA_TXT_3)

    benchmark.pedantic(run, rounds=20, iterations=2000, warmup_rounds=5)


@pytest.mark.benchmark(group="quiz")
def test_bench_regex_titolo_tema(benchmark):
    titolo = "Quiz Educazione Civica 1"
    tema = "Costituzione italiana: diritti e doveri (art. 1-12)"

    def run():
        ok1 = bool(TITOLO_RE.match(titolo))
        ok2 = bool(TEMA_RE.match(tema))
        return ok1 and ok2

    benchmark.pedantic(run, rounds=20, iterations=5000, warmup_rounds=5)


@pytest.mark.benchmark(group="quiz")
def test_bench_scoring_valuta_quiz_logic(benchmark):
    # Simula domande recuperate dal DB
    domande = [
        {"id_domanda": i, "risposta_corretta": "A"} for i in range(1, 21)
    ]
    # Simula risposte utente in formato simile a request JSON: q<ID> -> risposta
    risposte_utente = {f"q{i}": ("A" if i % 2 == 0 else "B") for i in range(1, 21)}

    def score():
        corrette = 0
        for d in domande:
            if risposte_utente.get(f"q{d['id_domanda']}") == d["risposta_corretta"]:
                corrette += 1
        totale = len(domande)
        return int((corrette / totale) * 100)

    benchmark.pedantic(score, rounds=30, iterations=500, warmup_rounds=5)


@pytest.mark.benchmark(group="quiz")
def test_bench_build_quiz_document_cpu_only(benchmark):
    # Simula payload frontend di /salva (senza DB)
    data = {
        "titolo": "Titolo prova",
        "argomento": "Tema prova",
        "n_domande": 10,
        "modalita_quiz": "3_risposte",
        "durata": 30,
        "data_creazione": "2026-01-13T17:20:16.549Z",
        "domande": [
            {
                "id_domanda": i,
                "testo_domanda": f"Domanda {i}",
                "opzioni_risposte": ["Opzione A", "Opzione B", "Opzione C"],
                "risposta_corretta": "A) Opzione A"
            }
            for i in range(1, 11)
        ],
    }

    def build_only():
        # Replica la parte CPU della salva_quiz: split/normalizza risposta corretta e crea lista question docs
        nuovo_id = 1.0
        quiz_doc = {
            "id_quiz": nuovo_id,
            "titolo": data["titolo"],
            "argomento": data["argomento"],
            "n_domande": data["n_domande"],
            "domande": data["domande"],
            "modalita_quiz": data["modalita_quiz"],
            "durata": data["durata"],
            "data_creazione": data["data_creazione"],
            "id_classe": 13917,
        }

        question_docs = []
        for domanda in data["domande"]:
            risposta_corretta = domanda["risposta_corretta"].split(")", 1)[-1].strip()
            question_docs.append(
                {
                    "id_domanda": domanda["id_domanda"],
                    "testo_domanda": domanda["testo_domanda"],
                    "opzioni_risposte": domanda["opzioni_risposte"],
                    "risposta_corretta": risposta_corretta,
                    "id_quiz": nuovo_id,
                }
            )
        return quiz_doc, question_docs

    benchmark.pedantic(build_only, rounds=30, iterations=300, warmup_rounds=5)


@pytest.mark.benchmark(group="quiz")
def test_bench_tempo_rimanente_calc_only(benchmark):
    # Isoliamo solo la parte "calcolo delta"
    ora_inizio = datetime.utcnow()
    durata_min = 30

    def calc_only():
        ora_attuale = datetime.utcnow()
        fine_quiz = ora_inizio + timedelta(minutes=durata_min)
        return max(0, int((fine_quiz - ora_attuale).total_seconds()))

    benchmark.pedantic(calc_only, rounds=30, iterations=1000, warmup_rounds=5)
