"""Executable gates for Rungs 2, 3 and 4 (P3-6b, 2026-09-05).

The registry named these rungs' gates as artifacts and prose: a pairing script
"run on AAPM 10", a task-spec constant, a curve image. A rung-7 audit on
2026-09-05 found that three of six rungs marked done therefore had no gate that
could be executed, let alone exercised in both directions. Rung 1 had already
shown what that costs: it read done for months while the verifier it named
admitted submissions that never reported the index its own reason called
discriminative.

Each gate here reads the artifact the rung already cites and asserts the
claim the rung's own reason makes. Each returns a list of violations, empty
when the claim holds, in the style of ``verify.check_paired_submission``. And
each ships its own **probes**: a payload that must pass and one that must be
refused, so an audit can exercise the gate in both directions without knowing
its semantics. A gate that only ever refuses passes a rejection-only test and
fails the project; the probes make that impossible to miss.

Numbers asserted are the registry's, not chosen here:
  Rung 2  10 patients, geometry correlation >= 0.99 (the file's own target),
          0 unpaired slices, 0 tolerance violations, every patient passed.
  Rung 3  the run's task is the WS-4 task (label, noise-ROI HU band, ROI size),
          48 ROIs per patient per model, and on real tissue the blur trap is
          last on ROI BandER by >= 3x while scoring the highest SSIM.
  Rung 4  at least three dose points, every model measured at every one, a
          knee named per model (a dose ratio, or null for "not reached"), the
          trap's knee not reached, and the trap lowest on ROI BandER at every
          dose point.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .task_spec import TASK_SPEC

#: WS-1 outputs, relative to the repository root (this file is WS-4/scoring/gates.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
WS1_OUTPUT = REPO_ROOT / "WS-1_dataset" / "output"
PAIRING_VALIDATION = WS1_OUTPUT / "aapm_pairing_validation.json"
R3_ROI_DETECTABILITY = WS1_OUTPUT / "aapm_r3_roi_detectability.json"
DOSE_DETECTABILITY = WS1_OUTPUT / "aapm_dose_detectability.json"

#: Rung 5/6's separation criterion, reused for Rung 3's real-tissue claim.
MIN_TRAP_SEPARATION = 3.0
#: Rung 2's pairing target, as the file itself declares it.
MIN_GEOMETRY_CORRELATION = 0.99
#: Rung 2's cohort.
AAPM_PATIENTS = 10

Doc = Dict[str, Any]


def _load(doc_or_path: Union[Doc, str, Path]) -> Doc:
    if isinstance(doc_or_path, dict):
        return doc_or_path
    return json.loads(Path(doc_or_path).read_text())


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ------------------------------------------------------------------ Rung 2

def check_pairing_validation(doc_or_path: Union[Doc, str, Path] = PAIRING_VALIDATION) -> List[str]:
    """Rung 2: real paired low-dose data, geometric pairing validated.

    The rung's reason: "10/10 geometric pairing validated (Pearson=1.0, 0
    unmatched, 0 violations)". Asserted per patient, not from the summary
    block alone, so a summary that disagrees with its rows is itself a
    violation.
    """
    doc = _load(doc_or_path)
    v: List[str] = []
    overall = doc.get("overall", {})
    rows = doc.get("per_patient", [])
    target = overall.get("min_correlation_target", MIN_GEOMETRY_CORRELATION)
    if not _num(target) or target < MIN_GEOMETRY_CORRELATION:
        v.append("correlation target %r is below the registry's %.2f" % (target, MIN_GEOMETRY_CORRELATION))
    if len(rows) != AAPM_PATIENTS:
        v.append("%d patients validated; the rung claims %d" % (len(rows), AAPM_PATIENTS))
    seen = set()
    for r in rows:
        pid = r.get("patient", "?")
        if pid in seen:
            v.append("patient %s appears twice" % pid)
        seen.add(pid)
        if not r.get("passed"):
            v.append("patient %s did not pass: %s" % (pid, r.get("reason")))
        corr = r.get("geometry_correlation")
        if not _num(corr) or corr < target:
            v.append("patient %s geometry correlation %r below target %s" % (pid, corr, target))
        for key in ("n_unpaired_fd", "n_unpaired_ld", "n_violations"):
            if r.get(key) != 0:
                v.append("patient %s %s = %r, not 0" % (pid, key, r.get(key)))
        if not (_num(r.get("n_paired")) and r["n_paired"] > 0 and r.get("n_fd") == r.get("n_ld") == r["n_paired"]):
            v.append("patient %s: n_fd %r, n_ld %r, n_paired %r are not one matched count"
                     % (pid, r.get("n_fd"), r.get("n_ld"), r.get("n_paired")))
    if overall.get("n_passed") != len([r for r in rows if r.get("passed")]) or overall.get("n_failed", 0) != 0:
        v.append("summary block (n_passed %r, n_failed %r) disagrees with the rows"
                 % (overall.get("n_passed"), overall.get("n_failed")))
    if not overall.get("all_passed") and not v:
        v.append("summary says all_passed is false while every row passed")
    return v


# ------------------------------------------------------------------ Rung 3

def check_roi_protocol(doc_or_path: Union[Doc, str, Path] = R3_ROI_DETECTABILITY,
                       min_ratio: float = MIN_TRAP_SEPARATION) -> List[str]:
    """Rung 3: lesion model + noise-ROI protocol on real tissue.

    The rung's gate named ``TASK_SPEC.noise_roi_hu_band``, a constant, which
    cannot be exercised. This asserts that the run actually used that task
    (label, HU band, ROI size), that 48 ROIs were drawn per patient per model,
    and the rung's own separation claim: blur last on ROI BandER by >= 3x while
    scoring the highest SSIM on the same run.
    """
    doc = _load(doc_or_path)
    v: List[str] = []
    task = doc.get("task", {})
    if task.get("task") != TASK_SPEC["label"]:
        v.append("run task %r is not the WS-4 task %r" % (task.get("task"), TASK_SPEC["label"]))
    if list(task.get("noise_roi_hu_band", [])) != list(TASK_SPEC["noise_roi_hu_band"]):
        v.append("noise-ROI HU band %r is not the task spec's %r"
                 % (task.get("noise_roi_hu_band"), TASK_SPEC["noise_roi_hu_band"]))
    if task.get("signal_sigma_px") != TASK_SPEC["signal"]["sigma_px"] or \
            task.get("peak_contrast_hu") != TASK_SPEC["signal"]["peak_contrast_hu"]:
        v.append("signal (sigma %r px, %r HU) is not the task spec's" % (task.get("signal_sigma_px"), task.get("peak_contrast_hu")))
    models = doc.get("models", [])
    if "blur" not in models:
        v.append("the blur trap is not among the models run")
        return v
    by = doc.get("by_split", {})
    for pid, block in doc.get("per_patient", {}).items():
        for m in models:
            n_roi = block.get("models", {}).get(m, {}).get("freq_roi", {}).get("n_roi")
            if n_roi != 48:
                v.append("patient %s model %s: %r ROIs, protocol says 48" % (pid, m, n_roi))
    def band(m):
        return by.get(m, {}).get("freq_roi", {}).get("roi_band_energy_ratio", {}).get("mean")
    def ssim(m):
        return by.get(m, {}).get("fidelity", {}).get("ssim", {}).get("mean")
    trap = band("blur")
    if not _num(trap):
        v.append("no ROI BandER for the blur trap in the split aggregate")
        return v
    others = {m: band(m) for m in models if m != "blur"}
    if any(not _num(x) for x in others.values()):
        v.append("a model has no ROI BandER: %s" % [m for m, x in others.items() if not _num(x)])
        return v
    worst = min(others.values())
    if worst <= trap:
        v.append("the trap is not last on ROI BandER: blur %.4f, weakest model %.4f" % (trap, worst))
    elif trap > 0 and worst / trap < min_ratio:
        v.append("trap separation %.2fx is below the %.0fx the rung claims" % (worst / trap, min_ratio))
    s_trap = ssim("blur")
    if _num(s_trap) and any(_num(ssim(m)) and ssim(m) > s_trap for m in others):
        v.append("the trap does not score the highest SSIM on this run, which the rung's reason states")
    return v


# ------------------------------------------------------------------ Rung 4

def check_dose_curve(doc_or_path: Union[Doc, str, Path] = DOSE_DETECTABILITY) -> List[str]:
    """Rung 4: dose-detectability curve, multi-dose, knee named.

    The rung's gate was a PNG, a JSON and a summary. This asserts what the
    reason claims: at least three dose points, every model measured at each,
    a knee entry per model (a dose ratio inside the measured range, or null
    for not reached), the trap's knee not reached, and the trap lowest on ROI
    BandER at every dose point.
    """
    doc = _load(doc_or_path)
    v: List[str] = []
    points = doc.get("dose_points", [])
    ratios = [p.get("ratio") for p in points]
    if len(points) < 3:
        v.append("%d dose points; the rung claims a multi-dose curve of at least 3" % len(points))
    if any(not _num(r) for r in ratios) or ratios != sorted(ratios):
        v.append("dose ratios %r are not numeric and increasing" % ratios)
    if doc.get("task", {}).get("task") != TASK_SPEC["label"]:
        v.append("run task %r is not the WS-4 task" % doc.get("task", {}).get("task"))
    by = doc.get("by_model", {})
    models = doc.get("models", [])
    if "blur" not in models or "blur" not in by:
        v.append("the blur trap is not on the curve")
        return v
    series: Dict[str, List[float]] = {}
    for m in models:
        block = by.get(m, {})
        doses = block.get("doses", {})
        missing = [p["key"] for p in points if p.get("key") not in doses]
        if missing:
            v.append("model %s has no measurement at dose point(s) %s" % (m, missing))
        knee = block.get("knee", {})
        if "bander_roi_knee_tau50" not in knee:
            v.append("model %s names no knee (bander_roi_knee_tau50 absent)" % m)
        else:
            k = knee["bander_roi_knee_tau50"]
            if k is not None and (not _num(k) or ratios and not (min(ratios) <= k <= max(ratios))):
                v.append("model %s knee %r is not a dose ratio inside the measured range %r" % (m, k, ratios))
        s = knee.get("bander_roi_series")
        if not isinstance(s, list) or len(s) != len(points) or any(not _num(x) for x in s):
            v.append("model %s ROI BandER series %r does not cover the %d dose points" % (m, s, len(points)))
        else:
            series[m] = s
    if by.get("blur", {}).get("knee", {}).get("bander_roi_knee_tau50") is not None:
        v.append("the trap's knee is reported as reached; the rung states it is not")
    if "blur" in series:
        for i, p in enumerate(points):
            trap = series["blur"][i]
            below = [m for m, s in series.items() if m != "blur" and s[i] <= trap]
            if below:
                v.append("at dose %s the trap (%.4f) is not lowest on ROI BandER: %s" % (p.get("key"), trap, below))
    return v


# ------------------------------------------------------------------ probes

def _pairing_reject() -> Doc:
    d = copy.deepcopy(_load(PAIRING_VALIDATION))
    d["per_patient"][3]["n_violations"] = 2
    d["per_patient"][3]["geometry_correlation"] = 0.97
    return d


def _roi_reject() -> Doc:
    d = copy.deepcopy(_load(R3_ROI_DETECTABILITY))
    # a trap that no longer separates: put it level with the weakest model
    weakest = min(d["by_split"][m]["freq_roi"]["roi_band_energy_ratio"]["mean"]
                  for m in d["models"] if m != "blur")
    d["by_split"]["blur"]["freq_roi"]["roi_band_energy_ratio"]["mean"] = weakest
    return d


def _dose_reject() -> Doc:
    d = copy.deepcopy(_load(DOSE_DETECTABILITY))
    d["by_model"]["blur"]["knee"]["bander_roi_knee_tau50"] = 0.25     # the trap "reaches" a knee
    d["by_model"]["blur"]["knee"]["bander_roi_series"][1] = 99.0        # and tops the board at one dose
    return d


#: gate name -> (accept payload factory, reject payload factory). An auditor
#: that finds this table can exercise a gate in both directions without
#: knowing what it checks. Factories load the real artifact so the accept
#: case is the field's own evidence, not a fixture; they raise FileNotFoundError
#: when WS-1 is absent, which the auditor should report as "not exercisable
#: here", never as a pass.
PROBES: Dict[str, Tuple[Callable[[], Doc], Callable[[], Doc]]] = {
    "check_pairing_validation": (lambda: _load(PAIRING_VALIDATION), _pairing_reject),
    "check_roi_protocol": (lambda: _load(R3_ROI_DETECTABILITY), _roi_reject),
    "check_dose_curve": (lambda: _load(DOSE_DETECTABILITY), _dose_reject),
}


def exercise(name: str) -> Dict[str, Any]:
    """Run one gate on its own probes. ``ok`` means it accepted what it should
    and refused what it should; anything else names which direction failed."""
    fn = globals()[name]
    accept, reject = PROBES[name]
    accepted = fn(accept())
    refused = fn(reject())
    return {"gate": name, "accepts": accepted == [], "rejects": bool(refused),
            "ok": accepted == [] and bool(refused),
            "accept_violations": accepted, "reject_violations": refused}
