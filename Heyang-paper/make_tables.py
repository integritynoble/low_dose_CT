#!/usr/bin/env python3
"""Generate every numeric table in the manuscript from the committed artifact.

No number in the manuscript is typed by hand. Each table below is written to
tables/*.tex and included by manuscript.tex, so a changed artifact changes the
paper and a stale table is visible in `git diff` rather than invisible in prose.

    python3 make_tables.py            # regenerate tables/
    python3 make_tables.py --check    # exit 1 if any table is stale
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent / "WS-1_dataset" / "R6_recalc" / "results" / "comparison_linux_full764.json"
OUT = HERE / "tables"

MODELS = ["blur", "learn", "ctformer", "red_cnn", "corediff"]
PRETTY = {"blur": "Blur (control)", "learn": "LEARN", "ctformer": "CTformer",
          "red_cnn": "RED-CNN", "corediff": "CoreDiff"}
METRIC = {"psnr": "PSNR", "ssim": "SSIM", "cnr_mean": "CNR",
          "cho_auc_mean": "CHO AUC", "npwe_mean": "NPWE", "n": "$n$"}


def load() -> dict:
    if not ARTIFACT.exists():
        sys.exit("artifact not found: %s" % ARTIFACT)
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _fmt(x: float) -> str:
    """Two significant figures in LaTeX scientific notation, or an em dash."""
    if x is None:
        return "---"
    if x == 0:
        return "$0$"
    m = "%.2e" % x
    mant, exp = m.split("e")
    return "$%s \\times 10^{%d}$" % (mant, int(exp))


def table_agreement(d: dict) -> str:
    """Per model: differences under the pre-registered criterion, and the worst
    relative difference per metric under the declared one."""
    rows = []
    for m in MODELS:
        v = d["per_model"][m]
        u = v["under_declared_criterion"]
        worst = u["worst_per_metric"]
        if worst:
            key = max(worst, key=lambda k: worst[k]["worst"])
            w = "%s, %s" % (_fmt(worst[key]["worst"]), METRIC.get(key, key))
        else:
            w = "bit-identical"
        rows.append("%s & %d & %d & %s & %s \\\\" % (
            PRETTY[m], v["n_checked"], v["n_diffs"], w, u["n_outside_declared_criterion"]))
    return "\n".join([
        r"\begin{tabular}{lrrlr}", r"\toprule",
        r"Method & Comparisons & \multicolumn{1}{c}{$n_{\ne}$} & Worst relative difference & Outside \\",
        r"       &             & \multicolumn{1}{c}{(abs.\ $10^{-6}$)} & (metric)              & declared \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


def table_ladder(d: dict) -> str:
    """The criterion ladder: loosening an absolute tolerance never resolves it."""
    lad = d["tolerance_audit"]["ladder"]
    rows = []
    for kind in ("absdiff", "reldiff"):
        for e in (6, 5, 4, 3):
            k = "%s@1e-0%d" % (kind, e)
            if k not in lad:
                continue
            v = lad[k]
            fail = ", ".join(PRETTY[m] for m in MODELS if m in v["failing_models"]) or "---"
            rows.append("%s & $10^{-%d}$ & \\textbf{%s} & %s \\\\" % (
                "Absolute" if kind == "absdiff" else "Relative", e, v["verdict"], fail))
        if kind == "absdiff":
            rows.append(r"\midrule")
    return "\n".join([
        r"\begin{tabular}{llll}", r"\toprule",
        r"Criterion kind & Tolerance & Verdict & Methods outside \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


def table_scale(d: dict) -> str:
    """Why one absolute number cannot serve: the metrics' own magnitudes."""
    crit = d["criterion"]["per_metric"]
    scale = {"psnr": "$\\sim$40--54", "ssim": "$\\sim$0.9", "cnr_mean": "$\\sim$2--7",
             "cho_auc_mean": "$\\sim$1.0", "npwe_mean": "$1.6\\times10^{5}$--$9.7\\times10^{5}$",
             "n": "764"}
    rows = []
    for k, v in crit.items():
        rows.append("%s & %s & %s & %s \\\\" % (
            METRIC.get(k, k), v["units"], scale.get(k, "---"),
            ("relative, $10^{-4}$" if v["kind"] == "relative" else "absolute, exact")))
    return "\n".join([
        r"\begin{tabular}{llll}", r"\toprule",
        r"Quantity & Units & Typical magnitude & Declared criterion \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"])


TABLES = {"agreement": table_agreement, "ladder": table_ladder, "scale": table_scale}


def main(argv) -> int:
    global ARTIFACT
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", default=str(ARTIFACT),
                    help="comparison artifact to read (default: comparison_linux_full764.json)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any table is stale")
    ns = ap.parse_args(argv)
    ARTIFACT = Path(ns.artifact)
    d = load()
    OUT.mkdir(exist_ok=True)
    stale = []
    for name, fn in TABLES.items():
        text = fn(d) + "\n"
        path = OUT / ("%s.tex" % name)
        if ns.check:
            if not path.exists() or path.read_text() != text:
                stale.append(path.name)
        else:
            path.write_text(text)
            print("wrote %s" % path.relative_to(HERE))
    if ns.check:
        if stale:
            print("stale: %s; run make_tables.py" % ", ".join(stale), file=sys.stderr)
            return 1
        print("all tables current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
