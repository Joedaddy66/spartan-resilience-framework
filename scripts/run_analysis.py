import csv, os, datetime, sys, pathlib
import matplotlib
matplotlib.use("Agg")  # headless for CI
import matplotlib.pyplot as plt

# Make src/ importable without install (CI-safe)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import summarize_p_list, Q_p, factor_semismooth, forced_composite_by_5, is_probable_prime

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
        f.write("**Charts:**\n\n")
        f.write("1. Overall digits growth vs. exponent p\n\n")
        f.write("   ![Qp Digits Plot](qp_digits_plot.png)\n\n")
        f.write("2. Survivors vs. killed-by-5 (different markers)\n\n")
        f.write("   ![Survivors vs Killed-by-5](qp_digits_survivors.png)\n\n")
        f.write("3. Log-scale digits vs. p (useful for larger p)\n\n")
        f.write("   ![Log-scale Digits](qp_digits_log.png)\n\n")
        f.write("4. Grouped by p mod 4 (different markers)\n\n")
        f.write("   ![Grouped by p mod 4](qp_by_mod4.png)\n\n")
        f.write("## Detailed Analysis Table\n\n")
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"]*len(headers)) + "|\n")
        for r in rows:
            f.write("| " + " | ".join(str(r[h]) for h in headers) + " |\n")
        f.write("\n---\n\n")
        f.write("## Small-case factorizations (p=5,13,17)\n\n")
        for p in [5,13,17]:
            Q = Q_p(p)
            fac = factor_semismooth(Q, max_steps=6)
            term = " * ".join([f"{b}^{e}" if e>1 else f"{b}" for b,e in sorted(fac.items())])
            f.write(f"- p={p}: Q_p={Q} = {term}  ")
            f.write(f"(forced_by_5={forced_composite_by_5(p)}, Qp_probably_prime={is_probable_prime(Q)})\n")

def plot_digits_overall(rows, path_png):
    p_values = [r['p'] for r in rows]
    q_digits = [r['Qp_digits'] for r in rows]
    plt.figure(figsize=(10, 6))
    plt.scatter(p_values, q_digits, s=80, alpha=0.85)  # no explicit colors
    for i, p in enumerate(p_values):
        plt.annotate(f"p={p}", (p_values[i], q_digits[i]), textcoords="offset points", xytext=(0,10), ha="center")
    plt.title("Number of Digits in $Q_p$ vs. Mersenne Exponent $p$")
    plt.xlabel("Mersenne Exponent ($p$)")
    plt.ylabel("Number of Digits in $Q_p$")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    plt.tight_layout()
    plt.savefig(path_png, dpi=150)
    plt.close()

def plot_survivors_vs_killed(rows, path_png):
    killed = [(r['p'], r['Qp_digits']) for r in rows if r['forced_by_5']]
    surv   = [(r['p'], r['Qp_digits']) for r in rows if not r['forced_by_5']]

    plt.figure(figsize=(10, 6))
    if killed:
        kp, kd = zip(*killed)
        plt.scatter(kp, kd, marker='x', s=90, alpha=0.9, label="killed by 5")
        for i in range(len(kp)):
            plt.annotate(f"p={kp[i]}", (kp[i], kd[i]), textcoords="offset points", xytext=(0,10), ha="center")
    if surv:
        sp, sd = zip(*surv)
        plt.scatter(sp, sd, marker='o', s=80, alpha=0.85, label="survivor")
        for i in range(len(sp)):
            plt.annotate(f"p={sp[i]}", (sp[i], sd[i]), textcoords="offset points", xytext=(0,10), ha="center")

    plt.title("Survivors vs. Killed-by-5 — $Q_p$ Digit Count vs. $p$")
    plt.xlabel("Mersenne Exponent ($p$)")
    plt.ylabel("Number of Digits in $Q_p$")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path_png, dpi=150)
    plt.close()

def plot_digits_logscale(rows, path_png):
    p_values = [r['p'] for r in rows]
    q_digits = [r['Qp_digits'] for r in rows]
    plt.figure(figsize=(10, 6))
    plt.scatter(p_values, q_digits, s=80, alpha=0.85)
    for i, p in enumerate(p_values):
        plt.annotate(f"p={p}", (p_values[i], q_digits[i]), textcoords="offset points", xytext=(0,10), ha="center")
    plt.yscale("log")
    plt.title("Digits in $Q_p$ vs. $p$ (log-scale y)")
    plt.xlabel("Mersenne Exponent ($p$)")
    plt.ylabel("Number of Digits in $Q_p$ (log scale)")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    plt.tight_layout()
    plt.savefig(path_png, dpi=150)
    plt.close()

def plot_by_p_mod4(rows, path_png):
    buckets = {0: [], 1: [], 2: [], 3: []}
    for r in rows:
        buckets[r['p_mod_4']].append((r['p'], r['Qp_digits']))

    markers = {0: 's', 1: 'o', 2: 'x', 3: '^'}  # different shapes, no colors set
    plt.figure(figsize=(10, 6))
    for cls in [0,1,2,3]:
        pts = buckets[cls]
        if not pts:
            continue
        xp, yd = zip(*pts)
        plt.scatter(xp, yd, marker=markers[cls], s=80, alpha=0.85, label=f"p ≡ {cls} (mod 4)")
        for i in range(len(xp)):
            plt.annotate(f"p={xp[i]}", (xp[i], yd[i]), textcoords="offset points", xytext=(0,10), ha="center")

    plt.title(r"$Q_p$ Digits vs. $p$ grouped by $p \mathrm{\ mod\ } 4$")
    plt.xlabel("Mersenne Exponent ($p$)")
    plt.ylabel("Number of Digits in $Q_p$")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path_png, dpi=150)
    plt.close()

def main():
    out_dir = pathlib.Path("docs/report")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = summarize_p_list(P_DEFAULT)

    write_csv(str(out_dir / "Qp_summary.csv"), rows)
    write_md_table(str(out_dir / "Qp_mod5_summary.md"), rows)

    plot_digits_overall(rows, str(out_dir / "qp_digits_plot.png"))
    plot_survivors_vs_killed(rows, str(out_dir / "qp_digits_survivors.png"))
    plot_digits_logscale(rows, str(out_dir / "qp_digits_log.png"))
    plot_by_p_mod4(rows, str(out_dir / "qp_by_mod4.png"))

    print("Wrote docs/report/* including two new charts (log-scale, mod-4 grouping).")

if __name__ == "__main__":
    main()
