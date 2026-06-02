"""Public API: ``signal_equivalence_credential``.

This is the single entry point the manuscript Results section advertises.
It computes a credential under the canonical estimator default
(``delong`` for AUC; ``percentile`` otherwise) and packages the verdict
with the framework hash so a third party can verify the credential by
recomputing the bootstrap.
"""

from __future__ import annotations

import warnings
from typing import Literal

import numpy as np

from pwm_dose_equivalence.credential import (
    Credential,
    Modality,
    SignalEquivalenceCredential,
    Task,
    Verdict,
)
from pwm_dose_equivalence.estimator import (
    delong_ci,
    percentile_ci,
    verdict_from_ci,
)
from pwm_dose_equivalence.framework_hash import framework_hash
from pwm_dose_equivalence.sample_size import (
    required_n_auc,
    required_n_bernstein,
    required_n_general,
)

_SCHEMA_VERSION = "pwm-signal-equivalence/v0.2"


def signal_equivalence_credential(
    *,
    # Estimator inputs — supply either (paired_a, paired_b) for general metrics
    # or (a_pos, a_neg, b_pos, b_neg) for AUC. Mutually exclusive.
    paired_a: np.ndarray | None = None,
    paired_b: np.ndarray | None = None,
    a_pos: np.ndarray | None = None,
    a_neg: np.ndarray | None = None,
    b_pos: np.ndarray | None = None,
    b_neg: np.ndarray | None = None,
    # Credential fields
    signal_ratio: float,
    modality: Modality,
    task: Task,
    subpopulation: str,
    epsilon: float,
    alpha: float = 0.05,
    # Identification
    method: str = "M",
    reference_method: str = "M_ref",
    # Estimator config
    estimator: Literal["auto", "percentile", "delong"] = "auto",
    n_bootstrap: int = 10_000,
    seed: int = 42,
    # Optional sample-size pre-flight
    sigma_delta_hint: float | None = None,
    placement_sd_hint: float | None = None,
) -> SignalEquivalenceCredential:
    """Compute a signal-equivalence credential.

    For non-AUC tasks pass ``paired_a`` and ``paired_b`` (per-patient score
    arrays of equal length). For AUC tasks pass ``a_pos / a_neg / b_pos /
    b_neg`` (paired-on-case positive/negative score arrays).

    ``estimator = "auto"`` (default) selects ``delong`` when ``task.metric ==
    "auc"`` and the AUC-style arguments are provided, otherwise ``percentile``.
    """
    rng = np.random.default_rng(seed)

    # Dispatch on what was passed
    auc_mode = (a_pos is not None or a_neg is not None
                or b_pos is not None or b_neg is not None)
    general_mode = (paired_a is not None or paired_b is not None)

    if auc_mode and general_mode:
        raise ValueError(
            "Pass either (paired_a, paired_b) for general metrics or "
            "(a_pos, a_neg, b_pos, b_neg) for AUC, not both."
        )
    if not (auc_mode or general_mode):
        raise ValueError(
            "Must pass (paired_a, paired_b) or (a_pos, a_neg, b_pos, b_neg)."
        )

    chosen = estimator
    if chosen == "auto":
        if auc_mode and task.metric == "auc":
            chosen = "delong"
        else:
            chosen = "percentile"

    sample_check: dict = {}

    if chosen == "delong":
        if not auc_mode:
            raise ValueError(
                "estimator='delong' requires (a_pos, a_neg, b_pos, b_neg) "
                "AUC-style inputs."
            )
        delta_mean, ci_low, ci_high = delong_ci(
            a_pos=np.asarray(a_pos),
            a_neg=np.asarray(a_neg),
            b_pos=np.asarray(b_pos),
            b_neg=np.asarray(b_neg),
            alpha=alpha,
        )
        n_test = len(a_pos) + len(a_neg)
        # DeLong is closed-form; record n_bootstrap as 0 for provenance honesty
        n_bootstrap_used = 0
        if placement_sd_hint is not None:
            n_required = required_n_auc(
                epsilon=epsilon, alpha=alpha,
                placement_sd=placement_sd_hint,
            )
            sample_check = {
                "rule": "S3-auc-clt",
                "placement_sd_hint": placement_sd_hint,
                "n_required": n_required,
                "n_actual": n_test,
                "ok": n_test >= n_required,
            }
            if n_test < n_required:
                warnings.warn(
                    f"Sample size {n_test} below S3 prescription "
                    f"({n_required}) at epsilon={epsilon}, alpha={alpha}. "
                    "Credential will likely be INDETERMINATE.",
                    UserWarning, stacklevel=2,
                )

    elif chosen == "percentile":
        if auc_mode:
            raise ValueError(
                "estimator='percentile' expects (paired_a, paired_b) "
                "per-patient score arrays."
            )
        a = np.asarray(paired_a, dtype=np.float64)
        b = np.asarray(paired_b, dtype=np.float64)
        if a.shape != b.shape:
            raise ValueError(
                f"paired_a shape {a.shape} != paired_b shape {b.shape}"
            )
        deltas = a - b
        delta_mean, ci_low, ci_high, _boots = percentile_ci(
            deltas, alpha=alpha, n_bootstrap=n_bootstrap, rng=rng,
        )
        n_test = len(deltas)
        n_bootstrap_used = n_bootstrap
        if sigma_delta_hint is not None:
            n_required = required_n_general(
                epsilon=epsilon, alpha=alpha,
                sigma_delta=sigma_delta_hint,
            )
            n_required_b = required_n_bernstein(
                epsilon=epsilon, alpha=alpha,
                sigma_delta=sigma_delta_hint,
            )
            sample_check = {
                "rule": "S1-clt",
                "sigma_delta_hint": sigma_delta_hint,
                "n_required_clt": n_required,
                "n_required_bernstein": n_required_b,
                "n_actual": n_test,
                "ok": n_test >= n_required,
            }
            if n_test < n_required:
                warnings.warn(
                    f"Sample size {n_test} below S1 prescription "
                    f"({n_required}) at epsilon={epsilon}, alpha={alpha}, "
                    f"sigma_delta={sigma_delta_hint}.",
                    UserWarning, stacklevel=2,
                )

    else:
        raise ValueError(f"Unknown estimator: {chosen}")

    verdict_str = verdict_from_ci(ci_low, ci_high, epsilon)

    cred = Credential(
        method=method,
        reference_method=reference_method,
        signal_ratio=signal_ratio,
        modality=modality,
        task=task,
        subpopulation=subpopulation,
        epsilon=epsilon,
        alpha=alpha,
        estimator=chosen,
        n_test=n_test,
        n_bootstrap=n_bootstrap_used,
        seed=seed,
        delta_mean=float(delta_mean),
        delta_ci_low=float(ci_low),
        delta_ci_high=float(ci_high),
        verdict=Verdict(verdict_str),
        sample_size_check=sample_check,
    )

    return SignalEquivalenceCredential(
        schema_version=_SCHEMA_VERSION,
        framework_hash=framework_hash(),
        credential=cred,
    )
