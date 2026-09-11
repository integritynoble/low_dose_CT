"""Regenerate the manuscript baseline-fidelity and detectability tables from the GPU runs.

Reads ``baselines/results/<model>_results_det_full764.json`` -- the 5-seed, n = 764
full-test-split GPU evaluation (fixed seed set 42/2023/7/12345/999, one aggregate per
simulated dose level) -- and emits ``tables/baselines.{json,tex}`` plus
``tables/detectability.{json,tex}``.

Every printed cell therefore comes from a committed artifact, mirroring
``extract_demographics.py`` / ``extract_acquisition.py``; the emitted captions carry
the file-count + combined-SHA-256 provenance of the result files they were built from.
No number is asserted by hand.

CNR convention: the 5-seed mean of the per-seed slice-wise CNR mean; where that mean is
undefined (LEARN: some output slices have zero local noise variance -> division by zero,
identical across the seed grid) the 5-seed mean of the per-seed slice median is reported
instead and the row is dagger-flagged, matching tab:detectability_v05.

Usage:
    python extract_baselines_tables.py --results ../baselines/results --out tables
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Optional

from common import inputs_fingerprint, write_outputs

MODELS: List[str] = ["red_cnn", "learn", "ctformer", "corediff", "blur"]
DISPLAY: Dict[str, str] = {
    "red_cnn": "RED-CNN",
    "learn": "LEARN",
    "ctformer": "CTformer",
    "corediff": "CoreDiff",
    "blur": "Gaussian blur (trap)",
}
DOSES: List[str] = ["sim_r010", "sim_r025", "sim_r050"]
# tab:baselines_v05 lists the four methods; the blur control lives in the task table.
FIDELITY_ROWS: List[str] = ["red_cnn", "learn", "ctformer", "corediff"]
DETECT_ROWS: List[str] = ["red_cnn", "learn", "ctformer", "corediff", "blur"]


def _load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _mean(node: Any) -> Optional[float]:
    """Pull ``.mean`` out of an aggregate statistic block (Infinity stays Infinity)."""
    if isinstance(node, dict):
        return node.get("mean")
    return node


def _seed_mean(doc: Dict[str, Any], dose: str, field: str) -> Optional[float]:
    """5-seed mean of a per-seed detectability field (used when the aggregate block
    does not carry that statistic, e.g. ``cnr_median`` for the LEARN fallback)."""
    vals = []
    for seed in sorted((doc.get("per_seed") or {}).keys()):
        det = ((doc["per_seed"][seed].get("per_dose") or {}).get(dose) or {}).get("detectability") or {}
        v = det.get(field)
        if isinstance(v, (int, float)):
            vals.append(float(v))
    if not vals:
        return None
    return sum(vals) / len(vals)


def _finite(v: Optional[float]) -> bool:
    return isinstance(v, (int, float)) and v not in (float("inf"), float("-inf"))


def collect(results_dir: str) -> Dict[str, Any]:
    per_model: Dict[str, Any] = {}
    paths: List[str] = []
    for m in MODELS:
        path = os.path.join(results_dir, f"{m}_results_det_full764.json")
        if not os.path.isfile(path):
            raise SystemExit(f"missing result file: {path}")
        paths.append(path)
        doc = _load(path)
        agg = doc.get("aggregate") or {}
        seeds = sorted((doc.get("per_seed") or {}).keys())
        rows: Dict[str, Any] = {}
        for dose in DOSES:
            block = agg.get(dose) or {}
            cnr_mean = _mean(block.get("cnr_mean"))
            cnr_median = _mean(block.get("cnr_median"))
            if cnr_median is None:
                cnr_median = _seed_mean(doc, dose, "cnr_median")
            # LEARN: slice-wise CNR mean is undefined (inf) -> report the slice median.
            use_median = not _finite(cnr_mean)
            cnr = cnr_median if use_median else cnr_mean
            if not _finite(cnr):
                raise SystemExit(f"{m}/{dose}: no finite CNR statistic available")
            rows[dose] = {
                "psnr": _mean(block.get("psnr")),
                "ssim": _mean(block.get("ssim")),
                "lpips": _mean(block.get("lpips")),
                "cnr": cnr,
                "cnr_statistic": "slice_median" if use_median else "slice_mean",
                "cho_auc": _mean(block.get("cho_auc_mean")),
                "n": (block.get("psnr") or {}).get("n_seeds"),
            }
        per_model[m] = {
            "display": DISPLAY[m],
            "seeds": seeds,
            "rule": doc.get("rule"),
            "split": doc.get("split"),
            "per_dose": rows,
        }
    return {
        "per_model": per_model,
        "provenance": inputs_fingerprint(sorted(paths)),
        "source_files": [os.path.basename(p) for p in sorted(paths)],
    }


def _f(v: Optional[float], nd: int) -> str:
    return "N/A" if v is None else f"{v:.{nd}f}"


def _cnr_cell(row: Dict[str, Any]) -> str:
    txt = _f(row["cnr"], 2)
    return txt + ("$^{\\dagger}$" if row["cnr_statistic"] == "slice_median" else "")


def fidelity_latex(table: Dict[str, Any]) -> str:
    head = ("\\textbf{Model} & \\multicolumn{3}{c}{\\textbf{r010}} & "
            "\\multicolumn{3}{c}{\\textbf{r025}} & \\multicolumn{3}{c}{\\textbf{r050}} \\\\")
    sub = ("& \\textbf{PSNR (dB)} & \\textbf{SSIM} & \\textbf{LPIPS} & "
           "\\textbf{PSNR (dB)} & \\textbf{SSIM} & \\textbf{LPIPS} & "
           "\\textbf{PSNR (dB)} & \\textbf{SSIM} & \\textbf{LPIPS} \\\\")
    lines = [head, sub, "\\midrule"]
    for m in FIDELITY_ROWS:
        cells: List[str] = []
        for dose in DOSES:
            r = table["per_model"][m]["per_dose"][dose]
            cells += [_f(r["psnr"], 2), _f(r["ssim"], 4), _f(r["lpips"], 4)]
        lines.append(f"{table['per_model'][m]['display']} & " + " & ".join(cells) + " \\\\")
    return "% auto-generated by extract_baselines_tables.py -- do not hand-edit\n" + "\n".join(lines) + "\n"


def detectability_latex(table: Dict[str, Any]) -> str:
    head = ("\\textbf{Model} & \\multicolumn{2}{c}{\\textbf{r010}} & "
            "\\multicolumn{2}{c}{\\textbf{r025}} & \\multicolumn{2}{c}{\\textbf{r050}} \\\\")
    sub = ("& \\textbf{PSNR} & \\textbf{CNR} & \\textbf{PSNR} & \\textbf{CNR} & "
           "\\textbf{PSNR} & \\textbf{CNR} \\\\")
    lines = [head, sub, "\\midrule"]
    for m in DETECT_ROWS:
        cells: List[str] = []
        for dose in DOSES:
            r = table["per_model"][m]["per_dose"][dose]
            cells += [_f(r["psnr"], 2), _cnr_cell(r)]
        name = table["per_model"][m]["display"]
        if m == "blur":
            name = "\\textbf{" + name + "}"
        lines.append(f"{name} & " + " & ".join(cells) + " \\\\")
    return "% auto-generated by extract_baselines_tables.py -- do not hand-edit\n" + "\n".join(lines) + "\n"


def _sanitize(node: Any) -> Any:
    """Replace non-finite floats with None so the emitted JSON is standard-compliant
    (LEARN's slice-wise CNR mean is legitimately +inf)."""
    if isinstance(node, float):
        return node if _finite(node) else None
    if isinstance(node, dict):
        return {k: _sanitize(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_sanitize(v) for v in node]
    return node


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True,
                    help="directory holding <model>_results_det_full764.json")
    ap.add_argument("--out", default="tables")
    args = ap.parse_args()

    table = collect(args.results)
    prov = table["provenance"]

    fid = {"per_model": {m: table["per_model"][m] for m in FIDELITY_ROWS},
           "provenance": prov, "source_files": table["source_files"]}
    det = {"per_model": {m: table["per_model"][m] for m in DETECT_ROWS},
           "provenance": prov, "source_files": table["source_files"]}

    write_outputs("baselines", _sanitize(fid), fidelity_latex(table), args.out)
    write_outputs("detectability", _sanitize(det), detectability_latex(table), args.out)

    print(f"baselines/detectability: n_fidelity={len(FIDELITY_ROWS)} "
          f"n_detectability={len(DETECT_ROWS)} "
          f"(provenance: {prov['n_files']} files, SHA {prov['combined_sha256'][:12]}...)")
    for m in DETECT_ROWS:
        r = table["per_model"][m]
        cells = " | ".join(
            f"{r['per_dose'][d]['psnr']:.2f}/{r['per_dose'][d]['cnr']:.2f}"
            f"{'*' if r['per_dose'][d]['cnr_statistic'] == 'slice_median' else ''}"
            for d in DOSES)
        print(f"  {r['display']:22s} seeds={len(r['seeds'])}  {cells}")
    print(f"  provenance over: {', '.join(table['source_files'])}")


if __name__ == "__main__":
    main()
