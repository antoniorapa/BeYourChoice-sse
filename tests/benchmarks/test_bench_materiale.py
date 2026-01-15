# tests/benchmarks/test_bench_materiale.py
import pytest
from app.controllers.materialeControl import MaterialeControl

class _FakeDBManager:
    """Stub minimo: MaterialeModel vuole db_manager.get_collection(...)."""
    def get_collection(self, name):
        return None  # non verrà usato nei benchmark "puri"


@pytest.fixture(scope="module")
def materiale_control():
    return MaterialeControl(_FakeDBManager())


@pytest.mark.benchmark(group="materiale")
def test_bench_titolo_valido(benchmark, materiale_control):
    titolo = "Materiale 12"

    def run():
        return materiale_control.titolo_valido(titolo)

    benchmark.pedantic(run, rounds=20, iterations=5000, warmup_rounds=5)


@pytest.mark.benchmark(group="materiale")
def test_bench_descrizione_valida(benchmark, materiale_control):
    descr = "Descrizione valida senza caratteri vietati. " * 3  # resta sotto 255

    def run():
        return materiale_control.descrizione_valida(descr)

    benchmark.pedantic(run, rounds=20, iterations=5000, warmup_rounds=5)


@pytest.mark.benchmark(group="materiale")
def test_bench_tipo_file_valido(benchmark, materiale_control):
    filename = "lezione_educazione_civica.pdf"

    def run():
        return materiale_control.tipo_file_valido(filename)

    benchmark.pedantic(run, rounds=20, iterations=10000, warmup_rounds=5)


@pytest.mark.benchmark(group="materiale")
def test_bench_mapping_materiali_for_view(benchmark):
    # Simula 500 documenti come tornerebbero da Mongo
    materiali = [
        {
            "id_materiale": f"m{i}",
            "titolo": f"Titolo {i}",
            "descrizione": "Descrizione",
            "file_path": f"file{i}.pdf",
            "tipo": "pdf",
            "id_classe": 13917,
        }
        for i in range(500)
    ]

    def map_for_view(items):
        # Esempio di trasformazione "render-ready"
        out = []
        for m in items:
            out.append(
                {
                    "id": m.get("id_materiale"),
                    "titolo": m.get("titolo", "").strip(),
                    "tipo": m.get("tipo"),
                    "file": m.get("file_path"),
                    "has_file": bool(m.get("file_path")),
                }
            )
        return out

    benchmark.pedantic(lambda: map_for_view(materiali), rounds=20, iterations=200, warmup_rounds=5)
