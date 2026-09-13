#!/usr/bin/env python3
"""Show what scoring BandER as distance-from-reference would change. Changes nothing.

Issue #24: BandER is `sum h(output)^2 / sum h(full_dose)^2`, so 1.0 is the ideal
— the output carries the same fine-structure energy as the reference. The board
sorts it descending and the trap gate asks only that the blur rank last, so
nothing anywhere references 1.0 and the score rewards high-frequency energy
without bound. A noise injector wins by orders of magnitude.

This script reports, from committed artifacts only:

  1. how a symmetric score reorders the measured methods
  2. what a noise-injection control would score, and whether the existing
     rank-only gate would catch it
  3. which rung separations survive the change

Run it before deciding; it writes nothing and touches no config.

    python3 scripts/prepare-bander-direction-fix.py
    python3 scripts/prepare-bander-direction-fix.py --json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
R3 = os.path.join(REPO, "WS-1_dataset/output/aapm_r3_roi_detectability.json")
CV = os.path.join(REPO, "WS-1_dataset/output/aapm_lidc_cross_vendor_spread.json")

#: Candidate replacements. Both are "lower is better" and symmetric about the
#: ideal, so over-smoothing and noise-injection are penalised alike.
def dev_log(b: float) -> float:
    """|log(BandER)| — treats 2x too much and 2x too little as equally wrong."""
    return abs(math.log(b)) if b > 0 else float("inf")


def dev_abs(b: float) -> float:
    """|BandER - 1| — simpler, but asymmetric in ratio terms."""
    return abs(b - 1.0)


def load_r3():
    d = json.load(open(R3, encoding="utf-8"))
    return {m: b["freq_roi"]["roi_band_energy_ratio"]["mean"] for m, b in d["by_split"].items()}


def load_cv():
    d = json.load(open(CV, encoding="utf-8"))
    out = {}
    for v, blk in d["per_vendor"].items():
        acc = {}
        for p in blk["patients"]:
            for m, mv in p["models"].items():
                b = mv.get("freq_roi", {}).get("roi_band_energy_ratio")
                if b is not None:
                    acc.setdefault(m, []).append(b)
        out[v] = {m: sum(x) / len(x) for m, x in acc.items()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r3 = load_r3()
    cv = load_cv()
    report = {"note": "analysis only; nothing was changed", "r3": {}, "per_vendor": {}}

    if not args.json:
        print("AAPM held-out — current ranking (BandER descending) vs distance-from-1.0\n")
        print(f"  {'method':12s} {'BandER':>8s} {'rank now':>9s} {'|log B|':>9s} {'rank fixed':>11s}")

    now = sorted(r3, key=lambda m: -r3[m])
    fixed = sorted(r3, key=lambda m: dev_log(r3[m]))
    for m in now:
        report["r3"][m] = {"bander": r3[m], "rank_now": now.index(m) + 1,
                           "dev_log": dev_log(r3[m]), "rank_fixed": fixed.index(m) + 1}
        if not args.json:
            print(f"  {m:12s} {r3[m]:8.3f} {now.index(m)+1:>9d} "
                  f"{dev_log(r3[m]):9.3f} {fixed.index(m)+1:>11d}")

    if not args.json:
        print(f"\n  order now   : {' > '.join(now)}")
        print(f"  order fixed : {' > '.join(fixed)}   (closest to the reference first)")
        moved = [m for m in r3 if now.index(m) != fixed.index(m)]
        print(f"  methods whose rank changes: {', '.join(moved) if moved else 'none'}")

        print("\nWould a noise injector be caught?\n")
        print(f"  {'control':26s} {'BandER':>10s} {'ranks last now?':>16s} {'caught by |log B|?':>19s}")
        worst = max(r3.values())
        for name, b in (("blur trap (measured)", r3.get("blur", 0.4315)),
                        ("noise +20HU (measured)", 182.95),
                        ("noise +60HU (measured)", 1597.69)):
            last_now = "yes" if b < min(v for k, v in r3.items() if k != "blur") else "NO"
            caught = "yes" if dev_log(b) > max(dev_log(v) for k, v in r3.items() if k != "blur") else "no"
            print(f"  {name:26s} {b:10.2f} {last_now:>16s} {caught:>19s}")
        print("\n  A rank-only gate asks whether the blur is last. A noise injector is")
        print("  first, so it passes untouched. Under |log B| it is the worst entry.")

        print("\nPer-vendor: does the trap still separate under the fixed score?\n")
        print(f"  {'vendor':22s} {'trap |log B|':>13s} {'worst real':>11s} {'trap still worst?':>18s}")

    for v, means in cv.items():
        trap = means.get("blur")
        reals = {m: b for m, b in means.items() if m != "blur"}
        if trap is None or not reals:
            continue
        t, worst_real = dev_log(trap), max(dev_log(b) for b in reals.values())
        ok = t > worst_real
        report["per_vendor"][v] = {"trap_dev": t, "worst_real_dev": worst_real, "trap_still_worst": ok}
        if not args.json:
            print(f"  {v:22s} {t:13.3f} {worst_real:11.3f} {('yes' if ok else 'NO'):>18s}")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        bad = [v for v, r in report["per_vendor"].items() if not r["trap_still_worst"]]
        print()
        if bad:
            print(f"  !! In {len(bad)} group(s) the blur is NO LONGER the worst entry under the")
            print(f"     fixed score: {', '.join(bad)}.")
            print("     That is information, not a reason to keep the current direction: it means")
            print("     some real method deviates from the reference more than the trap does.")
        else:
            print("  The trap remains the worst entry in every group under the fixed score.")
        print("\n  Nothing was changed. See issue #24.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
