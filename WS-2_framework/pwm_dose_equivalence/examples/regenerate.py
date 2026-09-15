"""Regenerate every example credential under this directory.

Idempotent: running this script overwrites the on-disk JSON files with the
output of a fixed-seed ``signal_equivalence_credential`` call (for the clean
example) and a deterministic set of tampered variants (for the failure
examples). The intent is that
``examples/`` is *generated* — never hand-edited — so a reviewer can audit
the file against this script.

Run::

    python3 examples/regenerate.py

The ``tests/test_examples.py`` suite catches drift between this script's
output and the on-disk JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pwm_dose_equivalence import (
    Task,
    signal_equivalence_credential,
)

HERE = Path(__file__).parent
FAILURES = HERE / "failures"


def _issue_clean_ct_lung_nodule_credential() -> dict:
    """A clean PASS credential — paired AUC at the WS-1 1.0 lung-nodule
    operating point. Seed is fixed; n_test is set to 500 (above the formula
    prescription) so the verdict lands cleanly on PASS rather than
    INDETERMINATE.

    The candidate has a small bias (+0.01 on positive scores, -0.01 on
    negative scores — slightly *better* AUC than the reference) and added
    per-case noise, so the paired AUC difference is non-degenerate and the
    DeLong CI has positive width.
    """
    rng = np.random.default_rng(42)
    n_pos = 250
    n_neg = 250

    # Reference scores — partial overlap so DeLong has variance to estimate.
    # Mean separation 0.20 with std 0.10 yields target AUC ≈ 0.92 (the
    # typical lung-nodule operating point) while leaving enough overlap that
    # per-case rankings differ between candidate and reference. Without that
    # overlap every (pos, neg) pair is correctly ranked, both AUCs are 1.0,
    # and the paired delta is degenerately zero.
    ref_pos = rng.normal(0.60, 0.10, size=n_pos)
    ref_neg = rng.normal(0.40, 0.10, size=n_neg)

    # Candidate scores — small per-case noise on top of the reference. The
    # noise std (0.02) is tight enough that the paired AUC delta lands
    # comfortably inside (-epsilon, +epsilon) for epsilon = 0.05 — clean
    # PASS verdict. Increasing the noise to 0.05 would push the credential
    # into the INDETERMINATE regime the WS-1 1.0 cohort lives in.
    cand_pos = ref_pos + rng.normal(0.0, 0.02, size=n_pos)
    cand_neg = ref_neg + rng.normal(0.0, 0.02, size=n_neg)

    cred = signal_equivalence_credential(
        a_pos=cand_pos,
        a_neg=cand_neg,
        b_pos=ref_pos,
        b_neg=ref_neg,
        signal_ratio=0.25,
        modality="CT",
        task=Task(
            "lung_nodule_5mm",
            metric="auc",
            ground_truth_protocol="pwm-ldct/annotation-qa/v0.5#sha256:...",
        ),
        subpopulation="adult_chest_pwm_l3_test_v1",
        epsilon=0.05,
        alpha=0.05,
        method="example_candidate",
        reference_method="FBP_full_dose",
        seed=42,
        placement_sd_hint=0.15,
    )
    return cred.to_dict()


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def regenerate() -> None:
    """Write all examples to disk under ``examples/``."""
    clean = _issue_clean_ct_lung_nodule_credential()
    _write_json(HERE / "valid_ct_lung_nodule.json", clean)

    # 1. Tampered verdict — flip PASS <-> FAIL on an otherwise valid CI.
    tampered = json.loads(json.dumps(clean))
    original = tampered["credential"]["verdict"]
    tampered["credential"]["verdict"] = "FAIL" if original == "PASS" else "PASS"
    _write_json(FAILURES / "tampered_verdict.json", tampered)

    # 2. Inverted CI — delta_ci_low > delta_ci_high.
    inverted = json.loads(json.dumps(clean))
    lo = inverted["credential"]["delta_ci_low"]
    hi = inverted["credential"]["delta_ci_high"]
    inverted["credential"]["delta_ci_low"] = hi
    inverted["credential"]["delta_ci_high"] = lo
    _write_json(FAILURES / "inverted_ci.json", inverted)

    # 3. Missing required field — drop verdict from the inner credential.
    missing = json.loads(json.dumps(clean))
    del missing["credential"]["verdict"]
    _write_json(FAILURES / "missing_field.json", missing)

    # 4. Unknown framework_hash — credential issued under a different
    #    framework specification. This is a WARNING, not a hard issue
    #    (the audit still reports ok=True for the verdict checks).
    stale = json.loads(json.dumps(clean))
    stale["framework_hash"] = "sha256:" + "0" * 64
    _write_json(FAILURES / "unknown_framework_hash.json", stale)

    # 5. Undersized PASS — sample_size_check.ok = False but verdict = PASS.
    #    WARNING, not a hard issue.
    undersized = json.loads(json.dumps(clean))
    undersized["credential"]["sample_size_check"] = {
        "rule": "S3-auc-clt",
        "placement_sd_hint": 0.15,
        "n_required": 99_999,
        "n_actual": undersized["credential"]["n_test"],
        "ok": False,
    }
    # Force PASS so the undersized warning is the interesting signal.
    undersized["credential"]["delta_ci_low"] = -0.01
    undersized["credential"]["delta_ci_high"] = 0.01
    undersized["credential"]["delta_mean"] = 0.0
    undersized["credential"]["verdict"] = "PASS"
    _write_json(FAILURES / "undersized_pass.json", undersized)

    # 6. BCa headline — estimator='bca' as the published estimator.
    #    WARNING; opt-in only per theory/proofs/estimator.md §4.
    bca = json.loads(json.dumps(clean))
    bca["credential"]["estimator"] = "bca"
    # BCa is a bootstrap estimator, so n_bootstrap should be > 0; set to a
    # plausible value to keep the JSON internally coherent.
    bca["credential"]["n_bootstrap"] = 10_000
    _write_json(FAILURES / "bca_headline.json", bca)


if __name__ == "__main__":  # pragma: no cover
    regenerate()
    print(f"Regenerated {sum(1 for _ in HERE.rglob('*.json'))} JSON examples.")
