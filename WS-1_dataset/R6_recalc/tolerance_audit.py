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

    psnr       ~ 5.2e+1     absolute 1e-6 => ~8 significant figures   (attainable)
    cnr_mean   ~ 5.2e+0     absolute 1e-6 => ~7 significant figures   (attainable)
    npwe_mean  ~ 1.56e+5    absolute 1e-6 => ~11 significant figures  (NOT attainable)

An absolute 1e-6 on a quantity near 156,001 demands agreement to roughly eleven
significant figures in a value accumulated over 764 slices.  Float64 carries
about 15-16 significant digits before accumulation; after a 764-term reduction
the achievable agreement is well short of eleven figures even with deterministic
kernels.  So the npwe_mean comparison cannot pass at absolute 1e-6 for reasons
that have nothing to do with cuDNN.  That is a units/scale defect in the
comparator, separable from the determinism question.

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

  (a) enable deterministic kernels (``torch.backends.cudnn.deterministic=True``,
      ``torch.use_deterministic_algorithms(True)``) and re-run, in which case the
      strict branch should pass on its own terms; or
  (b) amend the operator guide in writing, dated, to state that GPU inference
      paths compare at a relative 1e-4 -- and record *why* -- then re-run.

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
                "The shipped criterion applies an absolute tolerance of 1e-6 to "
                "metrics spanning five orders of magnitude. npwe_mean is ~1.56e5, "
                "where absolute 1e-6 demands ~11 significant figures from a "
                "764-term float64 reduction; that is unattainable regardless of "
                "cuDNN determinism, so ctformer's FAIL is an artifact of the "
                "criterion rather than evidence of a mismatch. Under a relative "
                "criterion at the same 1e-6 strictness, ctformer passes "
                "(4.4e-07) while corediff (2.5e-05) and red_cnn (6.4e-05) still "
                "exceed it. Those two are the genuine cuDNN non-determinism "
                "question."
            ),
            "unresolved": (
                "This audit deliberately does not change the verdict. Resolve by "
                "either (a) re-running with deterministic kernels enabled, or "
                "(b) amending the operator guide in writing, dated, to declare a "
                "relative tolerance for GPU inference paths, then re-running. "
                "Relaxing the threshold without (a) or (b) reproduces the prose "
                "PASS* as a script constant."
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
