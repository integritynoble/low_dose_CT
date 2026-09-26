"""WS-4 leaderboard model: seed entries, paired submissions, permanent blur trap.

The leaderboard is *detectability-first* (Rung 1): entries sort by the declared
discriminating index (``task_spec.DISCRIMINATING_FIELDS``, i.e. ROI BandER),
then by the transparency observers CNR and CHO-AUC, then PSNR. A submission
without detectability never reaches the board
(:func:`pwm_ldct_recon.verify.check_paired_submission` gate).

Ranking led with CNR until 2026-09-05. That was the same defect as the gate's
missing discriminating field, one layer up: Rung 1 records CNR as
non-discriminative on real anatomy, and on the simulated arm the permanent blur
trap's CNR *exceeds* RED-CNN, CoreDiff and CTformer at every dose. A CNR-led
board therefore displayed the trap above real methods while every gate passed.

The **permanent Gaussian blur trap** (Rung 1.3 / §4) is a seed entry marked
``permanent=True``: it can never be removed or overwritten, every new submission is
ranked against it, and the listing always shows each entry's gap vs the blur trap.
Its purpose is to keep the board honest, so the board records where the trap
actually sits: :func:`trap_rank_report` is computed on every mutation and stored
under ``board["trap_rank"]``, so the verdict lives in the artifact rather than in
prose. :func:`assert_trap_ranks_last` is the hard gate for a publishing path.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .task_spec import (BLUR_SPEC, DISCRIMINATING_FIELDS, REQUIRED_VENDOR_GROUPS,
                        SCHEMA_VERSION, TASK_LABEL, TASK_SPEC)
from .binding import _collect_patient_ids as _collect_patient_ids_from_result
from .verify import (check_claim_bound_provenance, check_input_bound_provenance,
                     check_paired_submission, extract_paired_methods,
                     provenance_sha256)

BLUR_ENTRY_ID = "seed-blur"
REFERENCE_ENTRY_ID = "seed-ws3-reference"

#: Verdicts for the trap-rank gate. INDETERMINATE is distinct from FAIL on
#: purpose: "the board cannot be checked" must never be recorded as "the board
#: is sound", or omitting the trap's number becomes the way to evade the gate.
TRAP_RANK_PASS = "PASS"
TRAP_RANK_FAIL = "FAIL"
TRAP_RANK_INDETERMINATE = "INDETERMINATE"
#: A board with nothing to rank the trap against makes no detectability claim
#: and must not be recorded as PASS (no claim is not a pass).
TRAP_RANK_NO_CLAIM = "NO_CLAIM"
#: The required vendor strata (REQUIRED_VENDOR_GROUPS) are not all covered by
#: submissions; the per-group claim cannot be certified.
TRAP_RANK_MISSING_STRATUM = "MISSING_STRATUM"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


#: Provenance of the permanent trap's measured numbers. Every metric in
#: :func:`seed_blur_entry` is the per-patient mean over this one run; nothing is
#: mixed across protocols. ``tests/test_trap_numbers.py`` re-reads the file and
#: fails if the literals drift from it, so a re-run cannot silently move the
#: board's trap. Hashes use LF-normalized source bytes; CRLF checkout conversion
#: is not a new measurement. All other byte changes still require review.
TRAP_SOURCE = {
    "file": "WS-1_dataset/output/aapm_r3_roi_detectability.json",
    "schema": "aapm-r3-roi-detectability/v1",
    "sha256": "9987864a1d60bed445ba6f1a4c08a344e8ba5217666e954f6a544557a32d55fc",
    "generated_at": "2026-08-22T19:36:01",
    "corpus": ("AAPM 2016 LDCT grand challenge, held-out test (4 patients), 1mm B30, "
               "FD vs QD real pairing"),
    "patients": ["aapm-0003", "aapm-0005", "aapm-0006", "aapm-0009"],
    "protocol": ("detectability-freq-v1 on find_tissue_roi patches (HU band [10,120], low "
                 "Sobel gradient, low internal std, seed 42, 32x32 px), 48 ROIs per patient"),
    "aggregation": "per-patient mean over the 4 held-out test patients",
    "refreshed_at": "2026-09-05",
}


def seed_blur_entry() -> Dict:
    """The permanent blur trap, with its measured numbers from the held-out run.

    Refreshed 2026-09-05 from :data:`TRAP_SOURCE`, replacing the synthetic
    self-test placeholders. The refresh was not cosmetic: the trap-rank gate
    reads INDETERMINATE, not PASS, once a real submission sits beside a trap
    carrying no ``bander_roi``, so the board could not be checked until this
    landed.

    Every field is the per-patient mean from one run of one protocol. That
    matters more than it sounds: the project holds two different band-energy
    measurements, the Rung 1 whole-slice ``band_energy_ratio`` (blur 0.247) and
    the Rung 3 ROI ``roi_band_energy_ratio`` (blur 0.432). The leaderboard's
    discriminating field is ``bander_roi`` and its task specification carries
    ``noise_roi_hu_band``, so the ROI protocol is the matching one. Taking the
    fidelity numbers from one file and the ROI band energy from the other would
    have produced an entry no run ever measured.

    These numbers are the trap's whole point, stated as data rather than prose:
    on this held-out test the blur takes the **highest** SSIM (0.965), the
    **highest** PSNR (41.6) and the **highest** CNR (0.171) of the four methods
    on the board, while ranking **last** on ROI band energy by 8.9x to 15.6x.
    High fidelity does not imply detectability, and three of the four indices a
    reader would reach for first rank the deliberate cheat top of the board.

    ``vendor`` and ``dose`` stay None, and the measurement's real context lives
    in ``source`` instead. These numbers *are* Siemens real quarter-dose, so
    that looks like an omission and it is not: those two fields are the grouping
    keys for :func:`compute_spread`, whose population is the submissions whose
    variability is being characterised. The trap is the control against which a
    group is judged, not a member of it, and putting a deliberate cheat inside
    the span would change what the span measures. Rung 5 uses the trap as a
    per-group separation check, which is a different operation from spread.

    The per-vendor requirement of Rung 5 is served separately, by
    :func:`seed_vendor_trap_entries` and :func:`trap_rank_by_group`: those
    traps *do* carry a vendor, because they exist to be judged inside a group,
    and :func:`compute_spread` keeps every trap out of the span. This entry
    stays the method-level trap the global :func:`trap_rank_report` uses.
    """
    return {
        "id": BLUR_ENTRY_ID,
        "method": "gaussian-blur",
        "kind": "seed-trap",
        "permanent": True,
        "trap": True,
        "placeholder": False,
        "vendor": None,
        "dose": None,
        "config": dict(BLUR_SPEC),
        "source": dict(TRAP_SOURCE),
        "metrics": {
            "psnr_db": 41.62701493902994,
            "ssim": 0.9653218340698881,
            "cnr_mean": 0.17063560072817718,
            "cho_auc_mean": 1.0,
            "npwe_mean": 220804.5630688496,
            "bander_roi": 0.4315421991344855,
            "bander_full": 0.42997330961502483,
            "roi_tm_auc": 0.9895833333333334,
            "task": TASK_SPEC["label"],
        },
        "submitted_at": _utcnow(),
        "notes": ("Permanent Gaussian blur trap (sigma=1.0 px, 5x5), measured on the AAPM "
                  "held-out test (4 patients, Siemens, real QD pairing) under "
                  "detectability-freq-v1; see `source` for the file and its hash. Highest "
                  "SSIM, highest PSNR and highest CNR on that run, last on ROI band energy "
                  "by 8.9-15.6x: high fidelity does not imply detectability."),
    }


#: Provenance of the per-vendor trap measurements. A different run from
#: :data:`TRAP_SOURCE`, on the same task and the same ROI protocol, covering the
#: four LIDC vendors at simulated r=0.25 plus AAPM Siemens at real quarter dose.
VENDOR_TRAP_SOURCE = {
    "file": "WS-1_dataset/output/aapm_lidc_cross_vendor_spread.json",
    "schema": "aapm-lidc-cross-vendor-spread/v1",
    "sha256": "c436407412c6e419745bddf23aa10a0b8466015dd12a4ad104299c3aabe4f086",
    "generated_at": "2026-08-22T21:01:52",
    "dose_points": {"LIDC_sim": "r=0.25 (lowdose_sim projection-domain, seed 42)",
                    "AAPM_real": "r=0.25 official real QD"},
    "protocol": ("detectability-freq-v1 on find_tissue_roi patches (HU band [10,120], low "
                 "Sobel gradient, low internal std, seed 42, 32x32 px)"),
    "aggregation": "per-patient mean within each vendor group",
    "added_at": "2026-09-05",
}

#: The permanent trap as measured in each vendor group, so Rung 5's requirement
#: that it separate in **every** group is checkable from the board rather than
#: only from a WS-1 output file. ``separation_ratio`` is the source file's own
#: min-model-over-blur ratio, kept for cross-checking against what the board
#: computes; the gate recomputes it rather than trusting it.
#:
#: The groups are not one corpus. GE, Philips, Siemens and Toshiba are LIDC at
#: simulated quarter dose; AAPM-Siemens-real is AAPM at real quarter dose, and
#: its numbers are the same measurement as :func:`seed_blur_entry`'s. Rung 6
#: forbids averaging across these groups for exactly this reason, and the trap
#: illustrates why: its own band energy ranges over an order of magnitude
#: between vendors, 0.045 on GE to 0.432 on AAPM, while separating cleanly
#: inside every one of them.
VENDOR_TRAP_MEASUREMENTS = {
    "GE": {
        "corpus": "LIDC lowdose_sim r=0.25 (seed 42)", "n_patients": 2,
        "separation_ratio": 9.674255870751027,
        "metrics": {"psnr_db": 40.68572623027117, "ssim": 0.9209226369857788,
                    "cnr_mean": 4.8088624181101896, "cho_auc_mean": 1.0,
                    "bander_roi": 0.045245933213797, "bander_full": 0.2509224449453622,
                    "roi_tm_auc": 0.9895833333333334},
    },
    "Philips": {
        "corpus": "LIDC lowdose_sim r=0.25 (seed 42)", "n_patients": 2,
        "separation_ratio": 12.803654465402388,
        "metrics": {"psnr_db": 43.581771895681854, "ssim": 0.9869370975842078,
                    "cnr_mean": 0.20756659662744237, "cho_auc_mean": 1.0,
                    "bander_roi": 0.24936490377459875, "bander_full": 0.4166925496969569,
                    "roi_tm_auc": 0.9895833333333334},
    },
    "Siemens": {
        "corpus": "LIDC lowdose_sim r=0.25 (seed 42)", "n_patients": 2,
        "separation_ratio": 9.461958071041304,
        "metrics": {"psnr_db": 36.93872655591893, "ssim": 0.8405405518909295,
                    "cnr_mean": 0.09848642185169176, "cho_auc_mean": 1.0,
                    "bander_roi": 0.1223033657914374, "bander_full": 0.1914244989515192,
                    "roi_tm_auc": 0.9895833333333334},
    },
    "Toshiba": {
        "corpus": "LIDC lowdose_sim r=0.25 (seed 42)", "n_patients": 2,
        "separation_ratio": 18.962875643689227,
        "metrics": {"psnr_db": 40.36947279508346, "ssim": 0.9115665163844824,
                    "cnr_mean": 3.459680516229598, "cho_auc_mean": 1.0,
                    "bander_roi": 0.05920958469662685, "bander_full": 0.22311928788604293,
                    "roi_tm_auc": 0.9895833333333334},
    },
    "AAPM-Siemens-real": {
        "corpus": "AAPM 2016 real QD pairing", "n_patients": 4,
        "separation_ratio": 8.930558159281748,
        "metrics": {"psnr_db": 41.62701493902994, "ssim": 0.9653218340698881,
                    "cnr_mean": 0.17063560072817718, "cho_auc_mean": 1.0,
                    "bander_roi": 0.4315421991344855, "bander_full": 0.42997330961502483,
                    "roi_tm_auc": 0.9895833333333334},
    },
}


def vendor_trap_entry_id(vendor: str) -> str:
    return "%s:%s" % (BLUR_ENTRY_ID, vendor)


def seed_vendor_trap_entries() -> List[Dict]:
    """One permanent trap per vendor group, from :data:`VENDOR_TRAP_SOURCE`.

    These carry a ``vendor``, unlike the method-level :func:`seed_blur_entry`,
    because they exist precisely to be judged inside a group. They are safe to
    give a grouping key because :func:`compute_spread` excludes traps from the
    population whose span it measures: the trap is the control for a group, not
    a member of it.
    """
    entries = []
    for vendor, block in VENDOR_TRAP_MEASUREMENTS.items():
        metrics = dict(block["metrics"])
        metrics["task"] = TASK_SPEC["label"]
        entries.append({
            "id": vendor_trap_entry_id(vendor),
            "method": "gaussian-blur [%s]" % vendor,
            "kind": "seed-trap",
            "permanent": True,
            "trap": True,
            "placeholder": False,
            "vendor": vendor,
            "dose": "0.25",
            "config": dict(BLUR_SPEC),
            "source": dict(VENDOR_TRAP_SOURCE, corpus=block["corpus"],
                           n_patients=block["n_patients"],
                           reported_separation_ratio=block["separation_ratio"]),
            "metrics": metrics,
            "submitted_at": _utcnow(),
            "notes": ("Permanent Gaussian blur trap as measured in the %s group (%s, %d "
                      "patients). Present so the Rung 5 requirement that the trap separate "
                      "in every vendor group can be checked from the board."
                      % (vendor, block["corpus"], block["n_patients"])),
        })
    return entries


def seed_reference_entry() -> Dict:
    """WS-3 reference method v1 seed (placeholder numbers until WS-3's real run)."""
    return {
        "id": REFERENCE_ENTRY_ID,
        "method": "WS-3 reference (unrolled + deep-ensemble)",
        "kind": "seed-reference",
        "permanent": False,
        "trap": False,
        "placeholder": True,
        "vendor": None,
        "dose": None,
        "metrics": {
            "psnr_db": 8.495,
            "ssim": 5.1e-05,
            "cnr_mean": None,       # undefined on synthetic noise-free patches
            "cho_auc_mean": 0.5,
            "npwe_mean": 0.0,
            "task": TASK_SPEC["label"],
        },
        "submitted_at": _utcnow(),
        "notes": ("Seed entry from WS-3 reference method v1. Placeholder numbers from "
                  "WS-3 self-test; refresh from the pinned RunBundle before launch."),
    }


def new_leaderboard() -> Dict:
    """Initialise the leaderboard with both seed entries (blur trap is permanent)."""
    entries = [seed_blur_entry()] + seed_vendor_trap_entries() + [seed_reference_entry()]
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_SPEC,
        "entries": entries,
        "trap_rank": trap_rank_report(entries),
        "trap_rank_by_vendor": trap_rank_by_group(entries, by="vendor"),
        "spread": {},
    }


def _cnr_sort_key(entry: Dict) -> float:
    cnr = entry.get("metrics", {}).get("cnr_mean")
    return cnr if isinstance(cnr, (int, float)) else float("-inf")


def discriminating_value(entry: Dict) -> Optional[float]:
    """The entry's value on the declared discriminating index, or None.

    Reads ``task_spec.DISCRIMINATING_FIELDS`` in order rather than naming a
    metric here, so that changing what counts as discriminating is a single
    edit to the task specification and not a search through the leaderboard.
    """
    metrics = entry.get("metrics", {})
    for field in DISCRIMINATING_FIELDS:
        value = metrics.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def sort_entries(entries: List[Dict]) -> List[Dict]:
    """Detectability-first ranking: discriminating index desc, then CNR, CHO-AUC, PSNR.

    The discriminating index leads. An entry that does not report it sorts below
    every entry that does, rather than being silently ranked on a transparency
    observer the blur trap can win.
    """
    def key(e: Dict):
        m = e.get("metrics", {})
        disc = discriminating_value(e)
        auc = m.get("cho_auc_mean")
        psnr = m.get("psnr_db")
        return (disc if disc is not None else float("-inf"),
                _cnr_sort_key(e),
                auc if isinstance(auc, (int, float)) else float("-inf"),
                psnr if isinstance(psnr, (int, float)) else float("-inf"))
    return sorted(entries, key=key, reverse=True)


def blur_entry(entries: List[Dict]) -> Optional[Dict]:
    for e in entries:
        if e.get("id") == BLUR_ENTRY_ID:
            return e
    return None


def _trap_in(entries: List[Dict]) -> Optional[Dict]:
    """The trap governing this list: the canonical seed, else any permanent trap.

    The fallback is what lets a single vendor group be checked on its own, since
    a group holds ``seed-blur:<vendor>`` rather than ``seed-blur``.
    """
    exact = blur_entry(entries)
    if exact is not None:
        return exact
    for e in entries:
        if e.get("trap") and e.get("permanent"):
            return e
    return None


def assert_trap_present(entries: List[Dict]) -> None:
    """The blur trap must always be on the board (Rung 1.3: it never leaves)."""
    if not any(e.get("id") == BLUR_ENTRY_ID and e.get("permanent") for e in entries):
        raise ValueError("permanent Gaussian blur trap missing from leaderboard")


def trap_rank_report(entries: List[Dict], *, min_ratio: Optional[float] = None) -> Dict:
    """Where the permanent blur trap sits on the declared discriminating index.

    The trap is a deliberate cheat: it destroys the high-frequency anatomy the
    detectability protocol measures while scoring the highest SSIM on the board.
    Rung 1, 3, 5 and 6 all rest on it ranking **last** on the discriminating
    index (measured 8.9-19.0x separation, blur last 4/4 in every vendor group).
    If it does not, one of two things is true, and neither may be published: an
    entry smooths harder than a plain Gaussian blur, or the index has stopped
    discriminating on this board. Which of the two it is, is a judgement for a
    person; that the board is not publishable as it stands, is not.

    Placeholder entries are excluded from the comparison: they carry
    ``placeholder=True`` and are marked non-scientific at the point of creation.

    Returns a verdict block; it never raises. ``verdict`` is one of PASS, FAIL,
    INDETERMINATE. INDETERMINATE means the board could not be checked, which is
    reported as its own state so that a missing trap number cannot be mistaken
    for a sound board.
    """
    index = DISCRIMINATING_FIELDS[0] if DISCRIMINATING_FIELDS else None
    report: Dict[str, Any] = {
        "index": index,
        "verdict": TRAP_RANK_PASS,
        "trap_value": None,
        "n_compared": 0,
        "min_ratio_required": min_ratio,
        "min_ratio_observed": None,
        "ranked": [],
        "violations": [],
        "note": "",
        "checked_at": _utcnow(),
    }
    if index is None:
        report["verdict"] = TRAP_RANK_INDETERMINATE
        report["violations"].append(
            "no discriminating index is declared in task_spec.DISCRIMINATING_FIELDS; "
            "the trap cannot be ranked")
        return report

    trap = _trap_in(entries)
    if trap is None or not trap.get("permanent"):
        report["verdict"] = TRAP_RANK_FAIL
        report["violations"].append("permanent Gaussian blur trap missing from leaderboard")
        return report

    comparable = []
    for e in entries:
        if e.get("id") == BLUR_ENTRY_ID or e.get("trap") or e.get("placeholder"):
            continue
        value = discriminating_value(e)
        if value is not None:
            comparable.append((e, value))

    trap_value = discriminating_value(trap)
    report["trap_value"] = trap_value
    report["n_compared"] = len(comparable)
    report["ranked"] = [{"id": e.get("id"), "method": e.get("method"), index: v}
                        for e, v in sorted(comparable, key=lambda p: p[1])]

    if not comparable:
        report["verdict"] = TRAP_RANK_NO_CLAIM
        report["note"] = ("no non-placeholder entry reports %s; there is nothing to rank "
                          "the trap against and the board makes no detectability claim" % index)
        return report

    if trap_value is None:
        report["verdict"] = TRAP_RANK_INDETERMINATE
        report["violations"].append(
            "the permanent blur trap reports no %s while %d entr%s do; the board cannot be "
            "checked. Refresh the trap's numbers from the WS-3 run before publishing: a trap "
            "with no discriminating number would otherwise let any board pass."
            % (index, len(comparable), "y does" if len(comparable) == 1 else "ies do"))
        return report

    offenders = [(e, v) for e, v in comparable if v <= trap_value]
    for e, v in sorted(offenders, key=lambda p: p[1]):
        report["violations"].append(
            "entry '%s' scores %s=%.6g, at or below the permanent blur trap (%.6g), so the "
            "trap is not last. Either that entry smooths beyond a plain Gaussian blur, or %s "
            "has stopped discriminating on this board; the board is not publishable either way."
            % (e.get("id"), index, v, trap_value, index))
    if offenders:
        report["verdict"] = TRAP_RANK_FAIL

    if trap_value > 0:
        report["min_ratio_observed"] = min(v / trap_value for _, v in comparable)
    else:
        report["note"] = ("trap %s is %.6g, so no separation ratio is defined; rank is still "
                          "checked" % (index, trap_value))

    if min_ratio is not None and report["min_ratio_observed"] is not None:
        if report["min_ratio_observed"] < min_ratio:
            report["verdict"] = TRAP_RANK_FAIL
            report["violations"].append(
                "smallest trap separation is %.3gx, below the required %.3gx (Rung 5/6 uses "
                "3x); the trap is not separated widely enough to certify the index"
                % (report["min_ratio_observed"], min_ratio))
    return report


def check_trap_rank(entries: List[Dict], *, min_ratio: Optional[float] = None) -> List[str]:
    """Violations of the trap-rank gate; an empty list means the board is sound."""
    return list(trap_rank_report(entries, min_ratio=min_ratio)["violations"])


def assert_trap_ranks_last(entries: List[Dict], *, min_ratio: Optional[float] = None) -> None:
    """Hard gate: raise unless the permanent trap ranks last on the discriminating index.

    Use this on a publishing path. Ordinary mutation records the verdict on the
    board instead of raising, so that a board which fails this check is still
    written down with its failure attached rather than discarded.
    """
    violations = check_trap_rank(entries, min_ratio=min_ratio)
    if violations:
        raise ValueError("trap-rank gate: " + "; ".join(violations))


def trap_rank_by_group(entries: List[Dict], *, by: str = "vendor",
                       min_ratio: Optional[float] = None) -> Dict:
    """Rung 5/6: the trap must separate **inside every group**, never averaged across.

    A global rank check is weaker than what Rung 5 claims. The trap's own band
    energy ranges over an order of magnitude between vendors (0.045 on GE to
    0.432 on AAPM), so a board could rank the trap last overall while a single
    vendor group had it above a real method. This checks each group on its own
    terms and never compares a value in one group against a value in another,
    which is the same constraint Rung 6 puts on spread.

    A group holding real entries but no trap measurement is INDETERMINATE, not
    FAIL: nothing is demonstrably wrong, the group simply cannot be certified.
    A group with a trap and nothing to rank it against passes vacuously and says
    so. The overall verdict is the worst across groups, FAIL over INDETERMINATE
    over PASS.
    """
    groups: Dict[str, List[Dict]] = {}
    for e in entries:
        key = e.get(by)
        if isinstance(key, str):
            groups.setdefault(key, []).append(e)

    report: Dict[str, Any] = {
        "by": by,
        "verdict": TRAP_RANK_PASS,
        "min_ratio_required": min_ratio,
        "n_groups": len(groups),
        "groups": {},
        "violations": [],
        "note": "",
        "checked_at": _utcnow(),
    }
    if not groups:
        report["note"] = "no entry carries a %s, so there is nothing to check per group" % by
        return report

    rank = {TRAP_RANK_NO_CLAIM: -1, TRAP_RANK_PASS: 0,
            TRAP_RANK_MISSING_STRATUM: 1, TRAP_RANK_INDETERMINATE: 2,
            TRAP_RANK_FAIL: 3}
    worst = TRAP_RANK_NO_CLAIM
    for key in sorted(groups):
        members = groups[key]
        if _trap_in(members) is None:
            comparable = [e for e in members
                          if not e.get("trap") and not e.get("placeholder")
                          and discriminating_value(e) is not None]
            block: Dict[str, Any] = {
                "verdict": TRAP_RANK_INDETERMINATE if comparable else TRAP_RANK_NO_CLAIM,
                "trap_value": None,
                "n_compared": len(comparable),
                "min_ratio_observed": None,
                "violations": [],
                "note": "",
            }
            if comparable:
                block["violations"].append(
                    "no trap measured in this group, so its %d entr%s cannot be certified; "
                    "add the trap's measurement for this %s"
                    % (len(comparable), "y" if len(comparable) == 1 else "ies", by))
            else:
                block["note"] = "no trap and nothing to rank; the group makes no claim"
            report["groups"][key] = block
        else:
            report["groups"][key] = trap_rank_report(members, min_ratio=min_ratio)

        block = report["groups"][key]
        for v in block["violations"]:
            report["violations"].append("%s=%s: %s" % (by, key, v))
        if rank[block["verdict"]] > rank[worst]:
            worst = block["verdict"]

    # Required strata (§2-B): the per-vendor claim may only be certified when
    # every REQUIRED_VENDOR_GROUPS stratum is covered by **submissions**. A
    # group that exists only as a seed trap is not covered: an absent real
    # submission is not evidence that the trap separates in it. Zero covered
    # strata is NO_CLAIM (nothing is claimed), partial coverage is
    # MISSING_STRATUM (the claim is not certified), never PASS.
    if by == "vendor":
        covered = [required for required in REQUIRED_VENDOR_GROUPS
                   if any(not e.get("trap") and not e.get("placeholder")
                          for e in groups.get(required, []))]
        missing = [required for required in REQUIRED_VENDOR_GROUPS
                   if required not in covered]
        if missing:
            if not covered:
                # Zero covered strata: no per-vendor claim is being made. NO_CLAIM
                # is the floor, but a group-level FAIL / INDETERMINATE already
                # recorded above still stands (a board with a real failure is not
                # rescued by having no claim).
                report["violations"].append(
                    "no required vendor stratum (REQUIRED_VENDOR_GROUPS) carries a "
                    "submission; there is no per-vendor claim to certify")
                report["note"] = ("no required vendor stratum carries a submission; "
                                  "the board makes no per-vendor detectability claim")
            else:
                report["violations"].append(
                    "missing required vendor stratum: %s; the per-group claim cannot be "
                    "certified until every REQUIRED_VENDOR_GROUPS group carries a submission"
                    % ", ".join(missing))
                report["note"] = "required vendor strata not fully covered: %s" % ", ".join(missing)
                if rank[worst] < rank[TRAP_RANK_MISSING_STRATUM]:
                    worst = TRAP_RANK_MISSING_STRATUM

    report["verdict"] = worst
    checked = [k for k, b in report["groups"].items() if b["n_compared"]]
    report["note"] = report["note"] or (
        "%d of %d %s groups had entries to rank the trap against"
        % (len(checked), len(groups), by))
    return report


def assert_trap_separates_in_every_group(entries: List[Dict], *, by: str = "vendor",
                                         min_ratio: Optional[float] = None) -> None:
    """Hard gate for the Rung 5/6 per-group requirement."""
    report = trap_rank_by_group(entries, by=by, min_ratio=min_ratio)
    if report["violations"]:
        raise ValueError("trap-rank gate (%s): " % by + "; ".join(report["violations"]))


def add_submission(leaderboard: Dict, result: Dict, method: str,
                   submitted_at: Optional[str] = None,
                   vendor: Optional[str] = None,
                   dose: Optional[str] = None,
                   binding_context: Optional[Dict] = None) -> List[Dict]:
    """Gate a submission and append it to the leaderboard.

    Returns the list of created entries (one per paired method block in ``result``).
    Raises ``ValueError`` for the submission as a whole if it carries no paired block,
    or for a specific method if that method's block violates the §4 paired rule
    (fidelity without detectability is not publishable).

    ``vendor`` / ``dose`` are the measurement context of the submission; they are kept
    per-entry so rankings can report spread without averaging across vendors (Rung 6).

    ``binding_context`` (Task 4, optional) forwards the runtime binding probe
    locations (keys: ``bundle_dir`` / ``checkpoint_dir`` / ``manifest_path`` /
    ``splits_dir``). When omitted the repository defaults are probed, so the
    binding snapshot is still computed from runtime filesystem facts rather than
    from self-reported JSON.
    """
    methods = extract_paired_methods(result)
    if not methods:
        raise ValueError("submission contains no paired fidelity+detectability block")

    # Validate the complete submission before appending any method. A later
    # invalid block must not leave earlier blocks in the caller's board.
    for name, m in methods.items():
        violations = check_paired_submission(m)
        if violations:
            raise ValueError(f"method '{name}' not publishable: {'; '.join(violations)}")

    # Claim-bound provenance (§2-D): the numbers must be bound to the evidence
    # they claim. A submission with no claim, a claim pointing at a different
    # task/protocol, or hashes that do not match its evidence is refused as a
    # whole -- after the numeric gate, so a numerically invalid method is still
    # named first.
    claim_violations = check_claim_bound_provenance(result)
    if claim_violations:
        raise ValueError("submission claim provenance: " + "; ".join(claim_violations))

    created: List[Dict] = []
    now = submitted_at or _utcnow()
    # Task 4: snapshot the claim/evidence and the runtime input-binding verdict
    # at submission time. The snapshot is written into each created entry so a
    # later direct save can re-verify it instead of trusting a self-reported
    # "verified" flag; a board entry that carries a claim must carry this
    # evaluator-owned evidence. Missing external files (checkpoints / manifest /
    # split source) produce UNVERIFIED states, never certified ones, and do not
    # block an otherwise valid submission (the numeric gates already ran).
    binding = check_input_bound_provenance(
        result, method=method, vendor=vendor, dose=dose,
        **(dict(binding_context or {})))
    binding_dict = binding["binding"] if isinstance(binding, dict) else {}
    claim_snapshot = result.get("claim") if isinstance(result.get("claim"), dict) else {}
    evidence_snapshot = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    # Task 4: the result-level patient ids are snapshotted next to the claim so a
    # later save-time recompute can re-run patient-mapping binding without having
    # to trust the board entry's metrics block.
    snap_patient_ids: Set[str] = set()
    _collect_patient_ids_from_result(result, snap_patient_ids)
    for name, m in methods.items():
        metrics = {k: m[k] for k in ("psnr_db", "ssim", "cnr_mean", "cho_auc_mean",
                                     "npwe_mean", "task") if k in m}
        # frequency-domain detectability (detectability-freq-v1) is carried when
        # present; on real anatomy it is the discriminative dimension (R3/R5)
        for k in ("bander_roi", "bander_full", "roi_tm_auc"):
            if k in m:
                metrics[k] = m[k]
        entry = {
            "id": f"sub-{len(leaderboard['entries']) + 1}-{name}",
            "method": method if len(methods) == 1 else f"{method} [{name}]",
            "kind": "submission",
            "permanent": False,
            "trap": False,
            "placeholder": False,
            "vendor": vendor,
            "dose": dose,
            "metrics": metrics,
            "submitted_at": now,
            "notes": "Paired submission accepted by WS-4 gate (§4 both-or-neither).",
            # Task 4 (2026-09-21): evaluator-owned provenance snapshot. A hash of
            # the shipped JSON proves internal consistency only; the runtime
            # binding verdict records what could actually be verified against the
            # filesystem at submission time. "ok" without "unverified" is the only
            # state that certifies inputs; anything else stays unverified/pending.
            "provenance": {
                "schema": "ws4-provenance-binding/v1",
                "claim": claim_snapshot,
                "evidence": evidence_snapshot,
                "claim_bound_sha256": provenance_sha256(claim_snapshot),
                "patient_ids": sorted(snap_patient_ids),
                "input_binding": binding_dict,
            },
        }
        leaderboard["entries"].append(entry)
        created.append(entry)

    leaderboard["entries"] = sort_entries(leaderboard["entries"])
    leaderboard["spread"] = compute_spread(leaderboard["entries"])
    # The trap-rank verdict is recorded, not raised: a board on which the trap is
    # not last is evidence, and discarding it would let the board hide a failure
    # of its own index. `assert_trap_ranks_last` is the gate for publishing.
    leaderboard["trap_rank"] = trap_rank_report(leaderboard["entries"])
    leaderboard["trap_rank_by_vendor"] = trap_rank_by_group(leaderboard["entries"], by="vendor")
    return created


def _numeric(values: List[Any]) -> List[float]:
    return [v for v in values if isinstance(v, (int, float)) and v is not None]


def _span_std(name: str, values: List[Any]) -> Dict:
    nums = _numeric(values)
    block: Dict[str, Any] = {"n": len(nums)}
    if nums:
        block[f"{name}_span"] = max(nums) - min(nums)
        if len(nums) > 1:
            block[f"{name}_std"] = statistics.pstdev(nums)
    return block


def compute_spread(entries: List[Dict], by: str = "vendor") -> Dict:
    """Per-group dual-metric spread (Rung 5/6: never average across vendors/doses).

    R5 method adjustment (2026-08-22): the original R5 design required **external
    multi-vendor submissions** on the board before spread could be computed. No
    external multi-vendor submissions exist, so the project's own held-out
    AAPM/LIDC multi-vendor + multi-dose results are treated as the on-board
    submission set (proxy for external submissions; see WS-1
    ``output/aapm_per_dose_spread.json`` + ``_summary.md``). Constraints
    unchanged: per-vendor / per-dose grouping, never average across groups, and
    the permanent blur trap must separate in every group (checked by the R5/R6
    gate, not by this report function).

    Groups entries by the given context key (``vendor`` or ``dose``) and reports the
    span/std of fidelity (psnr_db), detectability (bander_roi when present --
    frequency-domain detectability-freq-v1 ROI BandER, the discriminative
    dimension on real anatomy) and transparency (cnr_mean) within each group.
    Groups with no measured value are reported as empty. Returns
    ``{group: {n, psnr_db_span, psnr_db_std?, bander_roi_span?, bander_roi_std?,
    cnr_mean_span, cnr_mean_std?}}``.
    """
    groups: Dict[str, List[Dict]] = {}
    for e in entries:
        key = e.get(by)
        if key is None or not isinstance(key, str):
            continue
        # The permanent trap is the control a group is judged against, not a
        # member of the population whose variability the span describes. It
        # carries a vendor so `trap_rank_by_group` can find it; including it
        # here would let a deliberate cheat set the span.
        if e.get("trap"):
            continue
        groups.setdefault(key, []).append(e)

    spread: Dict[str, Any] = {}
    for key in sorted(groups):
        members = groups[key]
        psnr = [m.get("metrics", {}).get("psnr_db") for m in members]
        ber = [m.get("metrics", {}).get("bander_roi") for m in members]
        cnr = [m.get("metrics", {}).get("cnr_mean") for m in members]
        block = _span_std("psnr_db", psnr)
        block.update(_span_std("bander_roi", ber))  # detectability (freq-v1) if present
        block.update(_span_std("cnr_mean", cnr))
        block["n_entries"] = len(members)
        spread[key] = block
    return spread


def load(path: str | Path) -> Dict:
    with open(path, encoding="utf-8") as f:
        board = json.load(f)
    assert_trap_present(board.get("entries", []))
    return board


def _save_gate_violations(board: Dict) -> List[str]:
    """§2-C: the full gate chain a direct ``save()`` must run before writing.

    Applies the same gates a CLI submission runs, so a direct write cannot bypass
    them: entry-wise ``check_paired_submission`` (paired rule + §2-A task
    identity), the global trap-rank gate, and the per-required-stratum gate
    (§2-B). A board with nothing to rank (NO_CLAIM) is writable but makes no
    publishable claim; FAIL / INDETERMINATE / MISSING_STRATUM block the write.
    """
    violations: List[str] = []
    entries = board.get("entries", [])
    assert_trap_present(entries)
    for e in entries:
        if e.get("trap") or e.get("placeholder"):
            continue
        method_errors = check_paired_submission(e.get("metrics", {}))
        for err in method_errors:
            violations.append("entry '%s': %s" % (e.get("id"), err))
        # Task 4 (2026-09-21): a direct save must not be able to smuggle in a
        # forged provenance snapshot. An entry that carries a claim snapshot
        # (only ``add_submission`` legitimately creates one) is re-verified here:
        # the snapshot must be internally consistent, bound to this task, and the
        # identity fields must agree with the entry's own method/vendor/dose. A
        # forged or self-certifying snapshot is refused instead of being written
        # as if the gate had seen it.
        prov = e.get("provenance")
        if isinstance(prov, dict) and isinstance(prov.get("claim"), dict):
            claim_snap = prov["claim"]
            evidence_snap = prov.get("evidence") if isinstance(prov.get("evidence"), dict) else {}
            snap_result = {"claim": claim_snap, "evidence": evidence_snap}
            snap_pids = prov.get("patient_ids")
            if isinstance(snap_pids, list):
                snap_result["patient_ids"] = snap_pids
            claim_errors = check_claim_bound_provenance(snap_result)
            for err in claim_errors:
                violations.append("entry '%s': provenance claim snapshot is not "
                                  "internally consistent: %s" % (e.get("id"), err))
            if claim_snap.get("task_id") not in (None, TASK_LABEL):
                violations.append("entry '%s': provenance claim names task_id %r, "
                                  "not this board's %r"
                                  % (e.get("id"), claim_snap.get("task_id"),
                                     TASK_LABEL))
            claim_method = claim_snap.get("method_name")
            if claim_method and str(claim_method) != str(e.get("method")):
                violations.append("entry '%s': provenance claim names method %r "
                                  "but the entry is %r"
                                  % (e.get("id"), claim_method, e.get("method")))
            # Task 4: a claim that declares vendor/dose must agree with the
            # entry's own measurement context, otherwise a direct board edit
            # could rebind the numbers to a different stratum.
            claim_vendor = claim_snap.get("vendor")
            if claim_vendor and str(claim_vendor) != str(e.get("vendor")):
                violations.append("entry '%s': provenance claim names vendor %r "
                                  "but the entry is %r"
                                  % (e.get("id"), claim_vendor, e.get("vendor")))
            claim_dose = claim_snap.get("dose") or claim_snap.get("dose_level")
            if claim_dose and str(claim_dose) != str(e.get("dose")):
                violations.append("entry '%s': provenance claim names dose %r "
                                  "but the entry is %r"
                                  % (e.get("id"), claim_dose, e.get("dose")))
            binding = prov.get("input_binding")
            if isinstance(binding, dict) and binding.get("ok") is True:
                # "ok" alone never certifies; a FAIL snapshot is refused. An
                # UNVERIFIED snapshot is not a violation: per task book 4,
                # "when trusted evidence is absent, keep the result
                # unverified/pending instead of certifying it", so it stays
                # writable as pending and is only never certified.
                if binding.get("violations"):
                    violations.append("entry '%s': provenance snapshot carries "
                                      "binding violations (%d); cannot be ok"
                                      % (e.get("id"), len(binding.get("violations"))))
    tr = trap_rank_report(entries)
    if tr["verdict"] in (TRAP_RANK_FAIL, TRAP_RANK_INDETERMINATE):
        for v in tr["violations"]:
            violations.append("trap-rank: " + v)
    bg = trap_rank_by_group(entries, by="vendor")
    if bg["verdict"] in (TRAP_RANK_FAIL, TRAP_RANK_INDETERMINATE):
        for v in bg["violations"]:
            violations.append("strata: " + v)
    # MISSING_STRATUM / NO_CLAIM are recorded states, not invalid evidence: a
    # board whose required strata are not all covered is writable with
    # receipt.gate.strata != PASS and publication left pending, so the absence
    # of coverage is visible in the artifact instead of being silently refused
    # out of existence. Publishing gates (assert_trap_separates_in_every_group)
    # still refuse.
    return violations


def save(board: Dict, path: str | Path, *,
         binding_context: Optional[Dict] = None) -> None:
    """Run the full gate chain, write the board, and attach a receipt.

    §2-C: a direct save must not bypass the submission gates. This function
    refuses to write a board that fails the paired gate, the task-identity gate,
    the trap-rank gate, or the required-strata gate, and keeps a failed
    diagnostic record at ``<path>.failed.json`` when it does. A board that
    passes is written together with a **receipt** (submitted_at, gate results,
    the SHA-256 of the input board, and the failed-diagnostics path, which is
    null on success) and a separate ``publication`` field that defaults to
    ``pending``: a receipt is evidence that the board was written, not that it
    was released.

    ``binding_context`` (Task 4, optional) forwards the runtime binding probe
    locations to the save-time recompute (keys: ``bundle_dir`` /
    ``checkpoint_dir`` / ``manifest_path`` / ``splits_dir``). When omitted the
    repository defaults are probed. Every claim-carrying entry's input-binding
    snapshot is **recomputed from the filesystem at save time**; a hand-edited
    snapshot that claims ``ok`` while the runtime facts contradict it is refused
    (runtime violations) or downgraded to UNVERIFIED (runtime fact unavailable),
    so a direct-save edit cannot smuggle in a self-certified binding.
    """
    assert_trap_present(board.get("entries", []))
    input_sha256 = provenance_sha256(board)
    violations = _save_gate_violations(board)

    # Task 4 (2026-09-21): recompute every claim-carrying entry's input binding
    # from the runtime filesystem. A snapshot written by ``add_submission`` is
    # re-derived here so bytes changed between submission and save are caught; a
    # forged snapshot added by a direct board edit is refused when the runtime
    # facts contradict it. Entries without a claim snapshot keep historical
    # behaviour and are not touched. The identity context is taken from the
    # entry's own vendor/dose so a legitimate add_submission snapshot stays at
    # its original PASS state; the claim/method identity itself was already
    # checked in ``_save_gate_violations``.
    binding_context = dict(binding_context or {})
    for e in board.get("entries", []):
        prov = e.get("provenance") if isinstance(e.get("provenance"), dict) else None
        if not prov or not isinstance(prov.get("claim"), dict):
            continue
        claim_snap = prov["claim"]
        evidence_snap = prov.get("evidence") if isinstance(prov.get("evidence"), dict) else {}
        snap_result: Dict[str, Any] = {"claim": claim_snap, "evidence": evidence_snap}
        snap_pids = prov.get("patient_ids")
        if isinstance(snap_pids, list):
            snap_result["patient_ids"] = snap_pids
        recomputed = check_input_bound_provenance(
            snap_result,
            vendor=e.get("vendor") if isinstance(e.get("vendor"), str) else None,
            dose=e.get("dose") if isinstance(e.get("dose"), str) else None,
            **binding_context)
        recomputed_claim = recomputed.get("claim") or []
        recomputed_binding = recomputed.get("binding") or {}
        rb_violations = recomputed_binding.get("violations") or []
        if recomputed_claim:
            for err in recomputed_claim:
                violations.append("entry '%s': provenance claim snapshot is not "
                                  "internally consistent at save: %s"
                                  % (e.get("id"), err))
        if rb_violations:
            for err in rb_violations:
                violations.append("entry '%s': runtime input binding contradicts "
                                  "the provenance snapshot: %s" % (e.get("id"), err))
        else:
            # Replace the stored snapshot with the runtime recompute so a
            # hand-edited "ok" cannot outlive the filesystem facts.
            prov["input_binding"] = recomputed_binding

    if violations:
        failed_path = Path(str(path) + ".failed.json")
        failed = {
            "schema": "ws4-save-failed/v1",
            "saved_path": str(Path(path)),
            "submitted_at": _utcnow(),
            "input_sha256": input_sha256,
            "gate_violations": violations,
        }
        failed_path.write_text(json.dumps(failed, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        raise ValueError("board not publishable: " + "; ".join(violations)
                         + " (failed diagnostic: %s)" % failed_path)

    board["trap_rank"] = trap_rank_report(board.get("entries", []))
    board["trap_rank_by_vendor"] = trap_rank_by_group(board.get("entries", []), by="vendor")
    # Task 4 (2026-09-21): every claim-carrying entry must be input-bound or
    # marked UNVERIFIED at save time. The summary below is derived from the
    # entry-level provenance snapshots; a direct save that hand-edits a snapshot
    # is refused earlier in ``_save_gate_violations``.
    prov_summary: Dict[str, Any] = {"entries": 0, "pass": 0, "unverified": 0, "fail": 0}
    for e in board.get("entries", []):
        prov = e.get("provenance") if isinstance(e.get("provenance"), dict) else None
        if not prov:
            continue
        prov_summary["entries"] += 1
        binding = prov.get("input_binding") if isinstance(prov.get("input_binding"), dict) else {}
        status = binding.get("status", "UNVERIFIED")
        prov_summary[status.lower()] = prov_summary.get(status.lower(), 0) + 1
    board["receipt"] = {
        "schema": "ws4-save-receipt/v2",
        "submitted_at": _utcnow(),
        "input_sha256": input_sha256,
        "gate": {
            "check_submission_result": "ok",
            "task_identity": "ok",
            "trap_rank": board["trap_rank"]["verdict"],
            "strata": board["trap_rank_by_vendor"]["verdict"],
        },
        "input_binding": prov_summary,
        "failed_diagnostics": None,
    }
    board["publication"] = {
        "schema": "ws4-publication/v1",
        "status": "pending",
        "published_at": None,
        "note": ("A receipt is not a publication: this board has been written but "
                 "has not been released."),
    }
    Path(path).write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
