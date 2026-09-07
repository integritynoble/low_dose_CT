#!/usr/bin/env python3
"""Slice-level bootstrap CIs for the LIDC simulated dose-detectability curve.

Regenerates ``output/lidc_simulated_bootstrap_stats_full764.json`` and the
report table from the committed per-model result JSONs.  Previously only the
*outputs* of this computation were committed; the generator was not, so the
numbers could not be re-derived.  This script closes that gap.

Why the ``--pooling`` flag exists
---------------------------------
The published run resampled a pool of 3,820 slices per dose level, described as
"764 slices/seed pooled over the fixed 5-seed grid".  The five seeds do not
vary anything: for every model and every dose the per-slice CNR/PSNR/SSIM
vectors are byte-identical across seeds 42/2023/7/12345/999 (inference is
deterministic given the checkpoint; the seed never reaches a stochastic
component).  The pool is therefore five exact copies of the same 764 slices,
which inflates n by 5x and shrinks every percentile CI by roughly sqrt(5).

``--pooling seed_pooled`` reproduces the published (inflated) numbers so this
implementation can be checked against them.  ``--pooling distinct`` is the
correct one and resamples the 764 distinct slices.  ``distinct`` is the default.

The degeneracy is verified, not assumed: ``--pooling seed_pooled`` refuses to
run if the seeds ever stop being identical, since the inflation argument would
no longer hold and the pooled run would become legitimate.

Note on the remaining caveat: slice-level resampling characterises
slice-sampling uncertainty only.  Slices within a patient are correlated, so
even the corrected CI is optimistic with respect to inter-patient
heterogeneity.  Since §B, eval.py emits a per-slice ``patient_id`` vector
(same order/length as the CNR vector), so this script can now resample whole
patients as blocks: ``--unit patient`` performs a patient-level block
bootstrap (draw patients with replacement, keep every slice of a drawn
patient).  ``--unit slice`` (default) preserves the published slice-level
behaviour exactly.  Files produced by an eval.py without the patient_id
vector cannot be used with ``--unit patient`` (the script refuses rather than
guessing); the AAPM analysis reports the patient-level bootstrap separately.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from typing import Dict, List, Sequence

import numpy as np

ROSE = 3.0
DOSES = ("sim_r010", "sim_r025", "sim_r050")
DOSE_RATIO = {"sim_r010": 0.10, "sim_r025": 0.25, "sim_r050": 0.50}
DEFAULT_B = 4000
DEFAULT_SEED = 20260831
# LEARN's slice-wise CNR mean is undefined (some slices have zero local noise
# variance -> division by zero), so it is represented by the slice median.
MEDIAN_MODELS = {"learn"}

HERE = os.path.dirname(os.path.abspath(__file__))
WS1 = os.path.dirname(HERE)


def _per_slice_cnr(model_doc: dict, seed: str, dose: str) -> List[float] | None:
    det = model_doc["per_seed"][seed]["per_dose"][dose].get("detectability")
    if det is None:
        return None
    return det["per_slice"]["cnr"]


def _per_slice_ids(model_doc: dict, seed: str, dose: str) -> List[str] | None:
    """per_slice patient_id vector (None when the JSON predates §B eval.py)."""
    det = model_doc["per_seed"][seed]["per_dose"][dose].get("detectability")
    if det is None:
        return None
    ps = det.get("per_slice")
    if ps is None:
        return None
    return ps.get("patient_id")


def patient_ids_for(model_doc: dict, seed: str, dose: str) -> np.ndarray:
    """Validated per-slice patient_id vector for a model/dose (patient unit only)."""
    vals = _per_slice_cnr(model_doc, seed, dose)
    ids = _per_slice_ids(model_doc, seed, dose)
    if vals is None or ids is None:
        raise SystemExit(
            f"model {model_doc['model']!r} dose {dose!r}: no per_slice.patient_id "
            f"in the result JSON (pre-§B eval.py output). Patient-level bootstrap "
            f"needs the patient_id vector; re-run eval.py §B and commit new JSONs "
            f"before using --unit patient."
        )
    if len(ids) != len(vals):
        raise SystemExit(
            f"model {model_doc['model']!r} dose {dose!r}: per_slice.patient_id "
            f"length {len(ids)} != per_slice.cnr length {len(vals)}; the vectors "
            f"must be aligned."
        )
    return np.asarray(ids)


def _patient_mask(ids: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Boolean mask selecting the slices of the patients drawn with replacement.

    Patient-level (block) bootstrap: draw ``n_patients`` patients with
    replacement and keep every slice of every drawn patient.  The mask is the
    same length as ``ids`` and can be applied to any aligned pool.
    """
    patients = np.unique(ids)
    chosen = rng.choice(patients, size=patients.size, replace=True)
    return np.isin(ids, chosen)


def _resample_rep(pool: np.ndarray, ids: np.ndarray | None, use_median: bool,
                  rng: np.random.Generator, unit: str) -> float:
    """One bootstrap draw -> representative CNR for the resampled unit.

    unit=slice keeps the published behaviour: ``pool.size`` independent draws
    with replacement from the individual slices.  unit=patient draws whole
    patients with replacement and pools all their slices (block bootstrap).
    """
    if unit == "slice":
        idx = rng.integers(0, pool.size, pool.size)
        return representative(pool[idx], use_median)
    if ids is None:
        raise SystemExit("--unit patient requires per_slice.patient_id vectors")
    return representative(pool[_patient_mask(ids, rng)], use_median)


def _seed_hashes(model_doc: dict, dose: str) -> set[str]:
    out = set()
    for seed in model_doc["per_seed"]:
        vec = _per_slice_cnr(model_doc, seed, dose)
        blob = json.dumps(vec, sort_keys=True).encode()
        out.add(hashlib.sha256(blob).hexdigest())
    return out


def build_pool(model_doc: dict, dose: str, pooling: str) -> tuple[np.ndarray, bool]:
    """Return (pool, seeds_identical) for one model/dose."""
    seeds = list(model_doc["per_seed"])
    identical = len(_seed_hashes(model_doc, dose)) == 1

    if pooling == "seed_pooled":
        if not identical:
            raise SystemExit(
                f"--pooling seed_pooled is only meaningful as a reproduction of the "
                f"published run, which assumed the 5-seed grid was degenerate. For "
                f"model {model_doc['model']!r} dose {dose!r} the seeds now differ, so "
                f"pooling them is legitimate and this reproduction mode no longer "
                f"applies. Re-run with --pooling distinct."
            )
        vals: List[float] = []
        for seed in seeds:
            vals.extend(_per_slice_cnr(model_doc, seed, dose))
        return np.asarray(vals, dtype=float), identical

    # distinct: the seed grid contributes one copy of the slice set.
    if not identical:
        raise SystemExit(
            f"model {model_doc['model']!r} dose {dose!r}: seeds are no longer "
            f"identical. Deduplication by first-seed is unsafe; the seed grid now "
            f"carries real variance and this script needs updating to combine it."
        )
    return np.asarray(_per_slice_cnr(model_doc, seeds[0], dose), dtype=float), identical


def representative(vals: np.ndarray, use_median: bool) -> float:
    """Representative CNR for a dose level.

    Non-finite slices (zero local noise variance -> division by zero) are
    dropped before either statistic, matching the published run.  For the mean
    models no slice is non-finite, so this only bites for LEARN, which is
    represented by the median precisely because of those slices.
    """
    finite = vals[np.isfinite(vals)]
    if finite.size == 0:
        return float("nan")
    return float(np.median(finite) if use_median else np.mean(finite))


def knee(rep: Dict[str, float]) -> tuple[float | None, str]:
    """Dose ratio at which the interpolated CNR crosses the Rose criterion.

    Grid is {0.10, 0.25, 0.50}; no extrapolation outside the measured range.
    """
    r010 = rep["sim_r010"]
    if not np.isfinite(r010):
        return None, "nan"
    if r010 >= ROSE:
        return DOSE_RATIO["sim_r010"], "below_r010"
    for lo, hi in zip(DOSES, DOSES[1:]):
        a, b = rep[lo], rep[hi]
        if not (np.isfinite(a) and np.isfinite(b)):
            return None, "nan"
        if a < ROSE <= b:
            x0, x1 = DOSE_RATIO[lo], DOSE_RATIO[hi]
            return float(x0 + (ROSE - a) / (b - a) * (x1 - x0)), "interp"
    return None, "not_reached"


def bootstrap_model(
    model_doc: dict, pooling: str, B: int, rng: np.random.Generator,
    unit: str = "slice",
) -> dict:
    name = model_doc["model"]
    use_median = any(name.startswith(m) for m in MEDIAN_MODELS)

    pools: Dict[str, np.ndarray] = {}
    ids: Dict[str, np.ndarray] = {}
    identical = True
    for dose in DOSES:
        pools[dose], ident = build_pool(model_doc, dose, pooling)
        identical = identical and ident
        if unit == "patient":
            # first seed == the slice set used for the distinct pool; its
            # patient_id vector is the aligned block map.
            ids[dose] = patient_ids_for(model_doc, list(model_doc["per_seed"])[0], dose)

    observed_rep = {d: representative(pools[d], use_median) for d in DOSES}
    obs_knee, obs_kind = knee(observed_rep)

    draws: Dict[str, List[float]] = {d: [] for d in DOSES}
    knees: List[float] = []
    kinds = {"below_r010": 0, "interp": 0, "not_reached": 0, "nan": 0}

    for _ in range(B):
        rep = {}
        for dose in DOSES:
            pool = pools[dose]
            r = _resample_rep(pool, ids.get(dose), use_median, rng, unit)
            rep[dose] = r
            draws[dose].append(r)
        k, kind = knee(rep)
        kinds[kind] += 1
        if k is not None:
            knees.append(k)

    def ci(vals: Sequence[float]) -> List[float] | None:
        arr = np.asarray([v for v in vals if np.isfinite(v)], dtype=float)
        if arr.size == 0:
            return None
        return [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))]

    return {
        "use_median": use_median,
        "n_per_dose": int(pools[DOSES[0]].size),
        "n_distinct_slices": int(
            build_pool(model_doc, DOSES[0], "distinct")[0].size
        ),
        "seeds_identical": identical,
        "observed_rep_cnr": observed_rep,
        "observed_knee": obs_knee,
        "observed_kind": obs_kind,
        "knee_95ci": ci(knees) if obs_kind == "interp" else [obs_knee, obs_knee],
        "draw_kinds": kinds,
        "per_dose_rep_95ci": {d: ci(draws[d]) for d in DOSES},
    }


def bootstrap_separation(
    docs: Dict[str, dict], pooling: str, B: int, rng: np.random.Generator,
    unit: str = "slice",
) -> dict:
    """Paired blur-vs-model CNR separation ratios with bootstrap CIs.

    Paired resampling: the same resampling unit is drawn for blur and for the
    comparison model at each draw, matching the deterministic test-slice order
    the eval pipeline emits.  unit=slice draws the same slice indices for both;
    unit=patient draws the same patients (blocks) for both, which requires blur
    and the comparison model to expose identical patient_id vectors.  Ratio is
    blur_rep / model_rep, so >1 means the smoothing-only trap out-scores the
    learned method on CNR.
    """
    blur = next((d for n, d in docs.items() if n == "blur"), None)
    if blur is None:
        return {}
    out: dict = {}
    for name, doc in docs.items():
        if name == "blur":
            continue
        use_median = any(name.startswith(m) for m in MEDIAN_MODELS)
        per_dose = {}
        for dose in DOSES:
            bp, _ = build_pool(blur, dose, pooling)
            mp, _ = build_pool(doc, dose, pooling)
            n = min(bp.size, mp.size)
            obs = representative(bp[:n], False) / representative(mp[:n], use_median)
            if unit == "patient":
                ids_b = patient_ids_for(blur, list(blur["per_seed"])[0], dose)
                ids_m = patient_ids_for(doc, list(doc["per_seed"])[0], dose)
                if not np.array_equal(ids_b[:n], ids_m[:n]):
                    raise SystemExit(
                        f"blur vs {name!r} dose {dose!r}: patient_id vectors differ "
                        f"between paired models; patient-level paired bootstrap needs "
                        f"identical slice->patient maps."
                    )
            ratios = []
            for _ in range(B):
                if unit == "patient":
                    mask = _patient_mask(ids_b[:n], rng)
                    den = representative(mp[:n][mask], use_median)
                    if not np.isfinite(den) or den == 0:
                        continue
                    ratios.append(representative(bp[:n][mask], False) / den)
                else:
                    idx = rng.integers(0, n, n)
                    den = representative(mp[idx], use_median)
                    if not np.isfinite(den) or den == 0:
                        continue
                    ratios.append(representative(bp[idx], False) / den)
            arr = np.asarray([r for r in ratios if np.isfinite(r)], dtype=float)
            per_dose[dose] = {
                "observed_ratio": float(obs),
                "ci95": [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))]
                if arr.size
                else None,
                "n_pairs": int(n),
            }
        out[f"blur_vs_{name}"] = per_dose
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pooling",
        choices=("distinct", "seed_pooled"),
        default="distinct",
        help="distinct (correct, default) resamples the 764 distinct slices; "
        "seed_pooled reproduces the published 3,820-slice run for comparison.",
    )
    ap.add_argument(
        "--unit",
        choices=("slice", "patient"),
        default="slice",
        help="resampling unit. slice (default) preserves the published "
        "slice-level bootstrap (independent per-slice draws). patient performs "
        "a patient-level block bootstrap (whole patients drawn with "
        "replacement), which requires per_slice.patient_id in the result JSONs "
        "and forces --pooling distinct (patient ids only exist per distinct "
        "slice, not per seed copy).",
    )
    ap.add_argument("--results-glob", default=os.path.join(WS1, "baselines", "results", "*_results_det_full764.json"))
    ap.add_argument("--B", type=int, default=DEFAULT_B)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", default=None, help="output JSON path")
    args = ap.parse_args()

    if args.unit == "patient" and args.pooling != "distinct":
        raise SystemExit(
            "--unit patient requires --pooling distinct: the patient_id vector "
            "is per distinct slice; the seed_pooled pool repeats the same "
            "patients 5x and must not be block-resampled."
        )

    files = sorted(glob.glob(args.results_glob))
    if not files:
        raise SystemExit(f"no result files matched {args.results_glob!r}")

    rng = np.random.default_rng(args.seed)
    docs = {}
    for path in files:
        doc = json.load(open(path))
        docs[doc["model"]] = doc
    models = {n: bootstrap_model(d, args.pooling, args.B, rng, unit=args.unit)
              for n, d in docs.items()}
    separation = bootstrap_separation(docs, args.pooling, args.B, rng, unit=args.unit)

    n_pooled = next(iter(models.values()))["n_per_dose"]
    out = {
        "rose": ROSE,
        "doses": list(DOSES),
        "pooling": args.pooling,
        "n_per_dose": n_pooled,
        "B": args.B,
        "seed": args.seed,
        "seed_grid_is_degenerate": all(m["seeds_identical"] for m in models.values()),
        "note": (
            "The fixed 5-seed set {42,2023,7,12345,999} produces byte-identical "
            "per-slice vectors for every model and dose, so it contributes no "
            "variance. pooling=distinct resamples the 764 distinct slices; "
            "pooling=seed_pooled reproduces the earlier 3,820-slice run, whose "
            "CIs are narrowed by roughly sqrt(5) by the replication. Slice-level "
            "resampling covers slice-sampling uncertainty only, not "
            "inter-patient heterogeneity."
        ),
        "models": models,
        "separation_blur_vs_model": separation,
    }
    if args.unit == "patient":
        out["unit"] = "patient"
        out["note"] = (
            "Patient-level block bootstrap: patients are drawn with replacement "
            "and every slice of a drawn patient enters the resampled pool "
            "(blocks = patients), characterising inter-patient heterogeneity. "
            "Requires per_slice.patient_id emitted by the §B eval.py; pooling "
            "is fixed to distinct. unit=slice remains the published "
            "slice-level bootstrap."
        )

    # pooling=distinct writes the canonical stats file the manuscript cites;
    # pooling=seed_pooled writes a suffixed file kept only for comparison with
    # the superseded published run.  unit=patient writes its own suffixed file
    # so the canonical slice-level file is never overwritten by a different
    # resampling unit.
    if args.out:
        dest = args.out
    elif args.unit == "patient":
        dest = os.path.join(
            WS1, "output", "lidc_simulated_bootstrap_stats_full764_patient.json"
        )
    elif args.pooling == "distinct":
        dest = os.path.join(WS1, "output", "lidc_simulated_bootstrap_stats_full764.json")
    else:
        dest = os.path.join(
            WS1, "output", "lidc_simulated_bootstrap_stats_full764_seed_pooled.json"
        )
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"wrote {dest}  (pooling={args.pooling}, unit={args.unit}, "
          f"n_per_dose={n_pooled}, B={args.B})")

    for name, m in models.items():
        k = m["observed_knee"]
        kc = m["knee_95ci"]
        ks = f"{k:.3f} {kc}" if m["observed_kind"] == "interp" else f"<={k:.2f}"
        print(f"  {name:16s} knee {ks}")
        for d in DOSES:
            lo, hi = m["per_dose_rep_95ci"][d]
            print(
                f"      {d:10s} rep={m['observed_rep_cnr'][d]:8.3f} "
                f"CI=[{lo:.3f}, {hi:.3f}] width={hi - lo:.4f}"
            )


if __name__ == "__main__":
    main()
