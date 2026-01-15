import argparse
import os
import signal
import subprocess
import time
from pathlib import Path

from codecarbon import EmissionsTracker


def run_measurement(label: str, seconds: int, output_dir: str):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ogni run produce un file dedicato
    # CodeCarbon scrive per default "emissions.csv" nella working dir: noi isoliamo per cartella
    run_dir = out_dir / label
    run_dir.mkdir(parents=True, exist_ok=True)

    tracker = EmissionsTracker(
        project_name="BeYourChoice",
        experiment_id=label,               # etichetta run (es. docente_run1)
        output_dir=str(run_dir),           # dove salvare emissions.csv
        output_file="emissions.csv",
        measure_power_secs=1,              # campionamento (1s è ok per journey di 1-3 min)
        log_level="error",
        save_to_file=True,
    )

    print(f"[INFO] Starting tracker: {label}")
    tracker.start()

    # Avvia il server Flask come processo separato
    # Usa lo stesso python dell'ambiente corrente (venv)
    print("[INFO] Starting server.py ...")
    popen_kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Su Windows serve un nuovo gruppo di processi per poter inviare CTRL+BREAK
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    server_proc = subprocess.Popen(
        ["python", "server.py"],
        **popen_kwargs
    )


    try:
        # Attendi che il server sia su (semplice buffer)
        print("[INFO] Waiting 5 seconds for server startup...")
        time.sleep(5)

        print("\n============================================================")
        print(f"[ACTION] Ora esegui il journey nel browser per ~{seconds} secondi:")
        print("  - Docente: login -> classe -> crea quiz -> salva -> visualizza -> materiale -> upload")
        print("  - Studente: login -> svolgi quiz -> risultati -> materiale")
        print("URL: http://127.0.0.1:5000")
        print("============================================================\n")

        # Timer fisso per rendere replicabile la durata tra run
        time.sleep(seconds)

    finally:
        print("[INFO] Stopping server...")
        if server_proc.poll() is None:
            try:
                # Metodo più compatibile su Windows: invia CTRL+BREAK al gruppo di processi
                if os.name == "nt":
                    server_proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    server_proc.send_signal(signal.SIGINT)

                server_proc.wait(timeout=10)
            except Exception:
                # Fallback: termina forzatamente
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_proc.kill()

        emissions = tracker.stop()
        print(f"[RESULT] Tracker stopped. Emissions summary object: {emissions}")
        print(f"[INFO] Output salvato in: {run_dir / 'emissions.csv'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="es: docente_run1")
    parser.add_argument("--seconds", type=int, default=120, help="durata finestra misura (default 120s)")
    parser.add_argument("--output-dir", default="codecarbon_runs", help="cartella output")
    args = parser.parse_args()

    run_measurement(args.label, args.seconds, args.output_dir)
