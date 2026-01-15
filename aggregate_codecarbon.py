import glob
import os
import pandas as pd

def load_one(path):
    df = pd.read_csv(path)
    # emissions.csv di CodeCarbon può avere 1 riga (summary) o più righe (dipende dalla versione/config)
    # In ogni caso prendiamo l'ultima riga come "risultato finale"
    row = df.iloc[-1].to_dict()

    # Campi tipici CodeCarbon (possono cambiare leggermente a seconda della versione)
    duration_s = float(row.get("duration", row.get("duration(s)", 0)) or 0)
    energy_kwh = float(row.get("energy_consumed", row.get("energy_consumed(kWh)", 0)) or 0)
    emissions_kg = float(row.get("emissions", row.get("emissions(kg)", 0)) or 0)

    # Potenza media (W) = (kWh * 3.6e6 J/kWh) / s  => W = J/s
    avg_power_w = (energy_kwh * 3_600_000) / duration_s if duration_s > 0 else 0

    # Etichetta run = nome cartella (docente_run1, studente_run2, ...)
    run = os.path.basename(os.path.dirname(path))
    group = "docente" if run.startswith("docente") else ("studente" if run.startswith("studente") else "other")

    return {
        "group": group,
        "run": run,
        "duration_s": duration_s,
        "energy_kwh": energy_kwh,
        "avg_power_w": avg_power_w,
        "emissions_kg": emissions_kg,
        "file": path
    }

def main():
    paths = glob.glob("codecarbon_runs/*/emissions.csv")
    if not paths:
        raise SystemExit("Nessun emissions.csv trovato in codecarbon_runs/*/emissions.csv")

    rows = [load_one(p) for p in sorted(paths)]
    df = pd.DataFrame(rows)

    # Filtra solo docente/studente (evita cartelle extra)
    df = df[df["group"].isin(["docente", "studente"])].copy()

    # Salva tabella completa
    df.to_csv("codecarbon_summary_all_runs.csv", index=False)

    # Statistiche per gruppo
    stats = df.groupby("group").agg(
        n=("run", "count"),
        duration_mean_s=("duration_s", "mean"),
        duration_std_s=("duration_s", "std"),
        energy_mean_kwh=("energy_kwh", "mean"),
        energy_std_kwh=("energy_kwh", "std"),
        power_mean_w=("avg_power_w", "mean"),
        power_std_w=("avg_power_w", "std"),
        emissions_mean_kg=("emissions_kg", "mean"),
        emissions_std_kg=("emissions_kg", "std"),
    ).reset_index()

    stats.to_csv("codecarbon_summary_stats.csv", index=False)

    print("\n=== ALL RUNS ===")
    print(df[["group","run","duration_s","energy_kwh","avg_power_w","emissions_kg"]].to_string(index=False))

    print("\n=== STATS (mean/std) ===")
    print(stats.to_string(index=False))

    # Tabella LaTeX pronta (solo stats)
    latex = stats.to_latex(index=False, float_format="%.6f")
    with open("codecarbon_summary_stats.tex", "w", encoding="utf-8") as f:
        f.write(latex)
    print("\n[OK] Generati:")
    print(" - codecarbon_summary_all_runs.csv")
    print(" - codecarbon_summary_stats.csv")
    print(" - codecarbon_summary_stats.tex (tabella LaTeX)")

if __name__ == "__main__":
    main()
