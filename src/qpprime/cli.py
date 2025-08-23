import argparse, json, sys, pathlib

# Ensure "src" is on path when running from repo without install
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import (
    Q_p,
    summarize_p_list,
    factor_semismooth,
    forced_composite_by_5,
    is_probable_prime,
)

def cmd_analyze(args):
    rows = summarize_p_list(args.p)
    print(json.dumps(rows, indent=2))

def cmd_factor(args):
    for p in args.p:
        Q = Q_p(p)
        print(f"p={p}  Q_p has {len(str(Q))} digits")
        fac = factor_semismooth(Q, max_steps=args.max_steps)
        terms = []
        for base, exp in sorted(fac.items()):
            terms.append(f"{base}^{exp}" if exp > 1 else str(base))
        print("  factors (partial): " + " * ".join(terms))
        print(f"  probably prime? {is_probable_prime(Q)} | forced_by_5={forced_composite_by_5(p)}")
        print()  # clean blank line

def cmd_table(args):
    rows = summarize_p_list(args.p)
    headers = ["p", "p_mod_4", "forced_by_5", "killed_by_7", "killed_by_11", "killers", "Qp_mod_5", "Qp_digits", "Qp_probably_prime"]
    def tick(b): return "✅" if b else "❌"
    # header
    if args.markdown:
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"] * len(headers)) + "|")
    else:
        print("\t".join(headers))
    # rows
    for r in rows:
        r2 = r.copy()
        for k in ["forced_by_5","killed_by_7","killed_by_11","Qp_probably_prime"]:
            r2[k] = tick(r[k])
        cols = [str(r2[h]) for h in headers]
        if args.markdown:
            print("| " + " | ".join(cols) + " |")
        else:
            print("\t".join(cols))

def main():
    ap = argparse.ArgumentParser(description="Q_p analysis toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("analyze", help="Analyze Q_p over a list of p's")
    pa.add_argument("--p", nargs="+", type=int, required=True)
    pa.set_defaults(func=cmd_analyze)

    pf = sub.add_parser("factor", help="Attempt to factor Q_p for given p's (partial)")
    pf.add_argument("--p", nargs="+", type=int, required=True)
    pf.add_argument("--max-steps", type=int, default=6)
    pf.set_defaults(func=cmd_factor)

    pt = sub.add_parser("table", help="Emit a table (markdown or TSV) for given p's")
    pt.add_argument("--p", nargs="+", type=int, required=True)
    pt.add_argument("--markdown", action="store_true")
    pt.set_defaults(func=cmd_table)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()