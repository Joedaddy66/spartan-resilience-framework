import sys, pathlib
# Add repo/src to sys.path for local run without install
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import summarize_p_list, Q_p, factor_semismooth, forced_composite_by_5, is_probable_prime
import csv, os, datetime

P_DEFAULT = [2,3,5,7,13,17,19,31,61,89,107,127]

def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def write_md_table(path, rows):
    if not rows:
        return
    headers = list(rows[0].keys())
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Q_p Summary (generated {datetime.datetime.now(datetime.UTC).isoformat()})\n\n")
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"]*len(headers)) + "|\n")
        for r in rows:
            f.write("| " + " | ".join(str(r[h]) for h in headers) + " |\n")
        f.write("\n---\n\n")
        f.write("## Small-case factorizations (p=5,13,17)\n\n")
        for p in [5,13,17]:
            Q = Q_p(p)
            fac = factor_semismooth(Q, max_steps=6)
            term = " * ".join([f\"{b}^{e}\" if e>1 else f\"{b}\" for b,e in sorted(fac.items())])
            f.write(f"- p={p}: Q_p={Q} = {term}  ")
            f.write(f"(forced_by_5={forced_composite_by_5(p)}, Qp_probably_prime={is_probable_prime(Q)})\n")

def main():
    os.makedirs("report", exist_ok=True)
    rows = summarize_p_list(P_DEFAULT)
    write_csv("report/Qp_summary.csv", rows)
    write_md_table("report/Qp_mod5_summary.md", rows)
    print("Wrote report/Qp_summary.csv and report/Qp_mod5_summary.md")

if __name__ == "__main__":
    main()