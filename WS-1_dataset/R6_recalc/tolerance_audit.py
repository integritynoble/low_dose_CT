#!/usr/bin/env python3
"""Audit the R6 full-764 comparison verdict against its tolerance criterion.

Why this exists
---------------
``results/comparison_full764.json`` ships ``"overall": "FAIL"`` with red_cnn,
ctformer and corediff marked FAIL, while ``R6_recalc_report.md`` marks the same
three ``PASS*`` on the grounds that the differences are cuDNN non-determinism.
The repository therefore contains a machine-readable FAIL that only prose
overrides.  This script does not resolve that disagreement -- it *characterises*
it, so the decision is visible and is made on the record rather than by
adjusting a threshold after seeing the result.

What it establishes
-------------------
The comparison applies an **absolute** tolerance of 1e-6 uniformly, to metrics
whose magnitudes differ by five orders of magnitude:

    metric      magnitude   absolute 1e-6 means...   as a relative tolerance
    cnr_mean    ~ 5.2e+0    ~7 significant figures   ~2e-7
    psnr        ~ 5.2e+1    ~8 significant figures   ~2e-8
    npwe_mean   ~ 1.56e+5   ~11 significant figures  ~6e-12   (worst case 9.7e5 -> ~1e-12)

An absolute 1e-6 on a quantity near 1.56e5 (worst case 9.7e5) demands agreement
to roughly eleven significant figures.  That is a badly scaled criterion: it is
five orders of magnitude stricter, in relative terms, for npwe_mean than for
cnr_mean, so a single threshold means something different for each metric and
will misfire again on the next submission.

It is *not*, however, unattainable.  Float64 carries ~15-16 significant digits,
and a 764-term reduction accumulates on the order of 1e-13 relative, i.e. about
1e-8 absolute at 9.7e5 -- two orders of magnitude inside the 1e-6 budget.  With
deterministic kernels the two runs should agree bit-for-bit (absdiff exactly 0)
and the absolute criterion passes untouched.  The differences seen here come
from non-deterministic kernel selection, not from float64 headroom.

That asymmetry matters for the choice of route below: enabling determinism
satisfies the guide's same-hardware clause exactly as pre-registered, with no
amendment and no change to the kind of test.

Splitting the two questions
---------------------------
Re-adjudicating on a *relative* criterion at the same 1e-6 strictness isolates
the real finding:

    ctformer            worst relative difference 4.4e-07  -> passes at rel 1e-6
    corediff            worst relative difference 2.5e-05  -> exceeds rel 1e-6
    red_cnn             worst relative difference 6.4e-05  -> exceeds rel 1e-6
    blur, learn         bit-identical                      -> pass under any criterion

So ctformer's FAIL is an artifact of the scale-inappropriate criterion, while
red_cnn and corediff genuinely exceed 1e-6 in relative terms.  Those two are the
live cuDNN question, and this script deliberately does **not** answer it.  The
two defensible routes, both of which leave the artifact carrying its own
verdict, are:

  (a) PREFERRED -- enable deterministic kernels
      (``torch.backends.cudnn.deterministic=True``,
      ``torch.use_deterministic_algorithms(True)``) and re-run. The runs should
      then be bit-identical and the existing absolute 1e-6 passes as written.
      This is the only route that leaves the pre-registered rule untouched: it
      needs no amendment and no change to the kind of test.
  (b) amend the operator guide in writing, dated, to state that GPU inference
      paths compare at a relative 1e-4 -- and record *why* -- then re-run. This
      changes the kind of test, which is a larger thing to ask a reviewer to
      accept.

Independently of which route is taken, the comparator should declare agreement
per metric in that metric's own units rather than applying one absolute
threshold across metrics spanning five orders of magnitude.

Relaxing the number without (a) or (b) would relocate the prose ``PASS*`` into a
script, which is the same post-hoc adjudication in a less visible place.

Usage
-----
    python3 tolerance_audit.py            # print the ladder
    python3 tolerance_audit.py --write    # add a non-destructive
                                          # "tolerance_audit" block to
                                          # results/comparison_full764.json
                                          # (existing status fields untouched)
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
COMPARISON = os.path.join(HERE, "results", "comparison_full764.json")
LADDER = (1e-6, 1e-5, 1e-4, 1e-3)

DIFF_RE = re.compile(
    r"^(?P<model>\S+)\s+s(?P<seed>\S+)\s+(?P<dose>\S+)\s+(?P<metric>\w+):\s+"
    r"recalc=(?P<recalc>\S+)\s+onboard=(?P<onboard>\S+)\s+"
    r"absdiff=(?P<absdiff>\S+)\s+reldiff=(?P<reldiff>\S+)"
)


def parse(doc: dict) -> dict:
    """max abs/rel difference per model, and per model x metric."""
    out = {}
    for model, block in doc["per_model"].items():
        per_metric = collections.defaultdict(lambda: {"absdiff": 0.0, "reldiff": 0.0})
        worst = {"absdiff": 0.0, "reldiff": 0.0}
        for line in block.get("diffs", []):
            m = DIFF_RE.match(line)
            if not m:
                continue
            a, r = float(m["absdiff"]), float(m["reldiff"])
            met = m["metric"]
            per_metric[met]["absdiff"] = max(per_metric[met]["absdiff"], a)
            per_metric[met]["reldiff"] = max(per_metric[met]["reldiff"], r)
            worst["absdiff"] = max(worst["absdiff"], a)
            worst["reldiff"] = max(worst["reldiff"], r)
        out[model] = {
            "shipped_status": block.get("status"),
            "n_checked": block.get("n_checked"),
            "n_diffs": block.get("n_diffs"),
            "worst": worst,
            "per_metric": {k: dict(v) for k, v in sorted(per_metric.items())},
        }
    return out


def ladder(models: dict) -> dict:
    out = {}
    for kind in ("absdiff", "reldiff"):
        for tol in LADDER:
            failing = sorted(m for m, v in models.items() if v["worst"][kind] > tol)
            out[f"{kind}@{tol:.0e}"] = {
                "verdict": "PASS" if not failing else "FAIL",
                "failing_models": failing,
            }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="add the audit block to comparison_full764.json (additive only)")
    args = ap.parse_args()

    doc = json.load(open(COMPARISON, encoding="utf-8"))
    models = parse(doc)
    lad = ladder(models)

    print(f"shipped criterion: absolute tolerance {doc['tolerance']:.0e}, "
          f"overall {doc['overall']}\n")
    print(f"{'model':12s} {'shipped':8s} {'worst absdiff':>14s} {'worst reldiff':>14s}")
    for m, v in sorted(models.items()):
        print(f"{m:12s} {v['shipped_status'] or '-':8s} "
              f"{v['worst']['absdiff']:14.3e} {v['worst']['reldiff']:14.3e}")

    print("\nper-metric worst differences (shows the scale problem):")
    for m, v in sorted(models.items()):
        for met, d in v["per_metric"].items():
            print(f"  {m:12s} {met:12s} abs={d['absdiff']:.3e}  rel={d['reldiff']:.3e}")

    print("\ntolerance ladder:")
    for k, v in lad.items():
        detail = "" if v["verdict"] == "PASS" else "  failing: " + ", ".join(v["failing_models"])
        print(f"  {k:16s} {v['verdict']}{detail}")

    if args.write:
        doc["tolerance_audit"] = {
            "generated_by": "R6_recalc/tolerance_audit.py",
            "shipped_criterion": {
                "kind": "absolute",
                "tolerance": doc["tolerance"],
                "overall": doc["overall"],
            },
            "finding": (
                "The shipped criterion applies one absolute tolerance of 1e-6 to "
                "metrics spanning five orders of magnitude (cnr_mean ~5, "
                "npwe_mean ~1.56e5, worst case 9.7e5). In relative terms it is "
                "therefore ~5 orders stricter for npwe_mean than for cnr_mean, "
                "which is why ctformer is marked FAIL on a worst relative "
                "difference of 4.4e-07. The criterion is badly scaled and will "
                "misfire again on the next submission. It is NOT unattainable: "
                "a 764-term float64 reduction accumulates ~1e-13 relative "
                "(~1e-8 absolute at 9.7e5), well inside the 1e-6 budget, so with "
                "deterministic kernels the runs should be bit-identical and the "
                "existing criterion passes as written. Under a relative criterion "
                "at the same 1e-6 strictness, ctformer passes while corediff "
                "(2.5e-05) and red_cnn (6.4e-05) still exceed it; those two are "
                "the genuine cuDNN non-determinism question."
            ),
            "unresolved": (
                "This audit deliberately does not change the verdict. Route (a), "
                "PREFERRED: re-run with deterministic kernels enabled "
                "(cudnn.deterministic=True, use_deterministic_algorithms(True)); "
                "the runs should be bit-identical and the pre-registered absolute "
                "1e-6 then passes untouched, with no amendment and no change to "
                "the kind of test. Route (b): amend the operator guide in writing, "
                "dated, to declare a relative tolerance for GPU inference paths, "
                "then re-run -- this changes the kind of test. Relaxing the "
                "threshold without (a) or (b) reproduces the prose PASS* as a "
                "script constant. Independently of the route, agreement should be "
                "declared per metric in that metric's own units."
            ),
            "per_model": models,
            "ladder": lad,
        }
        with open(COMPARISON, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
        print(f"\nwrote tolerance_audit block into {COMPARISON}")
        print("(status/overall fields left exactly as the recalculator shipped them)")


if __name__ == "__main__":
    main()
