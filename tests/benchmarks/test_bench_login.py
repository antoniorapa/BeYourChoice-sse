# tests/benchmarks/test_bench_login.py
import re
import bcrypt
import pytest

# Regex prese dal tuo loginController.py
EMAIL_REGEX = r"^[A-z0-9._%+-]+@[A-z0-9.-]+\.[A-z]{2,4}$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=])[A-Za-z\d@#$%^&+=]{8,20}$"

# Pre-compiliamo (best practice) per ridurre overhead e rendere misure ripetibili
EMAIL_RE = re.compile(EMAIL_REGEX)
PASS_RE = re.compile(PASSWORD_REGEX)

SAMPLE_EMAIL_OK = "mario.rossi01@example.com"
SAMPLE_PASS_OK = "Aa1@aaaa"  # 8 chars, rispetta i vincoli (1 maiuscola, 1 minuscola, 1 cifra, 1 simbolo)

@pytest.mark.benchmark(group="login")
def test_bench_email_regex_compiled(benchmark):
    def run():
        return bool(EMAIL_RE.match(SAMPLE_EMAIL_OK))

    benchmark.pedantic(run, rounds=20, iterations=5000, warmup_rounds=5)


@pytest.mark.benchmark(group="login")
def test_bench_password_regex_compiled(benchmark):
    def run():
        return bool(PASS_RE.match(SAMPLE_PASS_OK))

    benchmark.pedantic(run, rounds=20, iterations=5000, warmup_rounds=5)


@pytest.mark.benchmark(group="login")
def test_bench_bcrypt_checkpw(benchmark):
    # Hash una volta sola (fuori dal benchmark) per misurare solo la verifica
    hashed = bcrypt.hashpw(SAMPLE_PASS_OK.encode("utf-8"), bcrypt.gensalt(rounds=12))
    pwd = SAMPLE_PASS_OK.encode("utf-8")

    def run():
        return bcrypt.checkpw(pwd, hashed)

    # bcrypt è costoso → poche iterazioni per round
    benchmark.pedantic(run, rounds=10, iterations=50, warmup_rounds=3)
