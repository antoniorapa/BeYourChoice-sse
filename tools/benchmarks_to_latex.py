# tools/benchmarks_to_latex.py
import argparse
import json
import math
from pathlib import Path
import csv

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return math.nan

def load_benchmarks(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    benches = data.get("benchmarks", [])
    rows = []
    for b in benches:
        name = b.get("name", "")
        group = b.get("group", "")
        stats = b.get("stats", {}) or {}
        # pytest-benchmark salva tempi in secondi
        mean_s = safe_float(stats.get("mean"))
        std_s = safe_float(stats.get("stddev"))
        median_s = safe_float(stats.get("median"))
        min_s = safe_float(stats.get("min"))
        max_s = safe_float(stats.get("max"))
        ops = safe_float(stats.get("ops"))  # ops/sec

        rows.append({
            "group": group,
            "name": name,
            "mean_ms": mean_s * 1000.0,
            "std_ms": std_s * 1000.0,
            "median_ms": median_s * 1000.0,
            "min_ms": min_s * 1000.0,
            "max_ms": max_s * 1000.0,
            "ops_s": ops,
        })
    return rows

def write_csv(rows, out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["group", "name", "mean_ms", "std_ms", "median_ms", "min_ms", "max_ms", "ops_s"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def latex_escape(s: str) -> str:
    # escape minimo per LaTeX
    return (s.replace("\\", "\\textbackslash{}")
             .replace("_", "\\_")
             .replace("%", "\\%")
             .replace("&", "\\&")
             .replace("#", "\\#")
             .replace("{", "\\{")
             .replace("}", "\\}")
            )

def format_ms(x):
    if x != x:  # NaN
        return "-"
    # 3 decimali bastano per ms
    return f"{x:.3f}"

def format_ops(x):
    if x != x:
        return "-"
    return f"{x:.1f}"

def write_latex(rows, out_tex: Path, caption: str, label: str):
    out_tex.parent.mkdir(parents=True, exist_ok=True)

    # Ordina: prima group poi mean crescente
    rows = sorted(rows, key=lambda r: (r["group"], r["mean_ms"] if r["mean_ms"] == r["mean_ms"] else 1e18))

    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\setlength{\tabcolsep}{6pt}")
    lines.append(r"\renewcommand{\arraystretch}{1.15}")
    lines.append(r"\begin{tabular}{llrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Gruppo & Benchmark & Mean (ms) & Std (ms) & Median (ms) & Min (ms) & Ops/s \\")
    lines.append(r"\hline")

    for r in rows:
        group = latex_escape(r["group"] or "-")
        name = latex_escape(r["name"])
        line = " & ".join([
            group,
            name,
            format_ms(r["mean_ms"]),
            format_ms(r["std_ms"]),
            format_ms(r["median_ms"]),
            format_ms(r["min_ms"]),
            format_ops(r["ops_s"]),
        ]) + r" \\"
        lines.append(line)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(rf"\caption{{{caption}}}")
    lines.append(rf"\label{{{label}}}")
    lines.append(r"\end{table}")

    out_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path al JSON prodotto da pytest-benchmark (--benchmark-json)")
    ap.add_argument("--outdir", default="benchmark_reports", help="Cartella output")
    ap.add_argument("--tag", default="before", help="Etichetta run (es: before/after)")
    args = ap.parse_args()

    inp = Path(args.input)
    outdir = Path(args.outdir)
    tag = args.tag.strip()

    rows = load_benchmarks(inp)

    out_csv = outdir / f"bench_{tag}.csv"
    out_tex = outdir / f"bench_{tag}.tex"

    write_csv(rows, out_csv)
    write_latex(
        rows,
        out_tex,
        caption=f"Risultati microbenchmark (pytest-benchmark) – run: {tag}.",
        label=f"tab:microbench_{tag}",
    )

    print("[OK] Generati:")
    print(f" - {out_csv}")
    print(f" - {out_tex}")

if __name__ == "__main__":
    main()
