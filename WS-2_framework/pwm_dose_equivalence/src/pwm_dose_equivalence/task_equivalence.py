"""Task-equivalence extension: observer-model detectability dimension.

P1-1 (low-dose-ct.md Rung 1.4 / §5 task detectability × dose-equivalence
calibration): upgrade the 5-tuple *signal* credential to a *task* credential
by adding an observer-model detectability dimension. A task-equivalence
credential asserts: at equivalent dose (same r, T, ε, α, Π), the
population-mean **observer detectability** of the candidate method on the
reduced-signal scans is within ε of the reference method on full-signal
scans — i.e. the equivalence is stated at the level of a clinically meaningful
task, not merely of a signal-intensity statistic.

The observer specification is borrowed verbatim from the shared WS-1 / WS-3
task (see ``WS-1_dataset/baselines/task_spec.json`` and
``WS-3_reference_method/method/src/pwm_ldct_recon/observers.py``):
SKE-Gaussian 20 HU / σ = 2 px, location known, tissue-only noise ROI
(HU band + low gradient), fixed observer parameters. PET phantoms use the
contrast-recovery endpoint (NEMA NU-2 CRC) instead of a CT-style
detectability observer; the same credential shape holds because the observer
spec declares which endpoint is being measured.

This module is **strictly additive**: it does not modify the v0.2 credential
dataclasses or ``FRAMEWORK_SPEC``, so existing credentials and their
framework hashes are unaffected. The task dimension is carried as a
first-class field of :class:`TaskEquivalenceCredential` and validated by
:data:`TASK_EQUIVALENCE_JSON_SCHEMA`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import numpy as np
import numpy.typing as npt

from pwm_dose_equivalence.api import signal_equivalence_credential
from pwm_dose_equivalence.credential import (
    Credential,
    Modality,
    SignalEquivalenceCredential,
    Task,
    Verdict,
)
from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA
from pwm_dose_equivalence.framework_hash import framework_hash

#: Observer endpoint types. ``cho`` = channelized Hotelling observer AUC
#: (CT/MRI task detectability); ``cnr`` / ``npwe`` = single-slice
#: detectability surrogates (CT); ``contrast_recovery`` = NEMA NU-2 CRC
#: (PET phantom).
ObserverType = Literal["cho", "cnr", "npwe", "contrast_recovery"]

_SCHEMA_VERSION = "pwm-task-equivalence/v0.1"

#: Task-equivalence metrics map an observer endpoint to the underlying
#: credential ``Task.metric`` (used by the estimator to pick CI defaults and
#: by the JSON schema's existing enum).
_METRIC_BY_OBSERVER: dict[ObserverType, str] = {
    "cho": "auc",
    "cnr": "mae",
    "npwe": "mae",
    "contrast_recovery": "contrast_recovery",
}


@dataclass(frozen=True)
class ObserverSpec:
    """Declared observer-model task specification (Rung 1.1 / Rung 1.2).

    Field values mirror the WS-1 / WS-3 shared task specification exactly so
    a task-equivalence credential is numerically comparable across repos.
    For ``observer == "contrast_recovery"`` (PET phantom) the CT-style fields
    are retained for schema stability but the measured endpoint is the NEMA
    CRC against physical ground truth.
    """

    observer: ObserverType = "cho"
    signal_sigma_px: float = 2.0          # Gaussian lesion sigma (px)
    peak_contrast_hu: float = 20.0        # peak contrast above background (HU)
    location_known: bool = True           # SKE (signal-known-exactly)
    noise_roi_hu_band: tuple[float, float] = (10.0, 120.0)  # tissue ROI HU band
    n_trials: int = 64                    # trials for CHO / CNR estimate
    label: str = "SKE-Gaussian20HU-s2px"

    @property
    def task_metric(self) -> str:
        """Credential-level metric slug for this observer endpoint."""
        return _METRIC_BY_OBSERVER[self.observer]


@dataclass
class TaskEquivalenceCredential:
    """A task-equivalence credential: 5-tuple + observer detectability.

    Wraps the signal-equivalence credential produced for the detectability
    endpoint, adds the full observer specification and a per-cohort
    detectability summary (reduced vs full means and difference), and pins
    the same framework hash. Serialise via :meth:`to_json` / :meth:`to_dict`.
    """

    schema_version: str
    framework_hash: str
    credential: Credential
    observer_spec: ObserverSpec
    detectability_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["credential"]["verdict"] = (
            self.credential.verdict.value
            if isinstance(self.credential.verdict, Verdict)
            else self.credential.verdict
        )
        return d

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TaskEquivalenceCredential:
        base = SignalEquivalenceCredential.from_dict(d)
        spec_d = d["observer_spec"]
        observer_spec = ObserverSpec(
            observer=spec_d["observer"],
            signal_sigma_px=spec_d.get("signal_sigma_px", 2.0),
            peak_contrast_hu=spec_d.get("peak_contrast_hu", 20.0),
            location_known=spec_d.get("location_known", True),
            noise_roi_hu_band=tuple(spec_d.get("noise_roi_hu_band", [10.0, 120.0])),
            n_trials=spec_d.get("n_trials", 64),
            label=spec_d.get("label", "SKE-Gaussian20HU-s2px"),
        )
        return cls(
            schema_version=d["schema_version"],
            framework_hash=d["framework_hash"],
            credential=base.credential,
            observer_spec=observer_spec,
            detectability_summary=d.get("detectability_summary", {}),
        )

    @classmethod
    def from_json(cls, s: str) -> TaskEquivalenceCredential:
        return cls.from_dict(json.loads(s))


def task_equivalence_credential(
    *,
    # Paired per-slice observer-detectability measurements.
    # detectability_reduced : candidate method M on reduced-signal scans
    # detectability_full     : reference method M_ref on full-signal scans
    detectability_reduced: npt.NDArray[Any],
    detectability_full: npt.NDArray[Any],
    observer_spec: ObserverSpec,
    # Credential fields
    signal_ratio: float,
    modality: Modality,
    subpopulation: str,
    epsilon: float,
    alpha: float = 0.05,
    # Identification
    method: str = "M",
    reference_method: str = "M_ref",
    # Estimator config
    estimator: Literal["auto", "percentile", "delong", "bca"] = "auto",
    n_bootstrap: int = 10_000,
    seed: int = 42,
    # Optional sample-size pre-flight
    sigma_delta_hint: float | None = None,
    placement_sd_hint: float | None = None,
    bound_M: float = 1.0,
) -> TaskEquivalenceCredential:
    """Issue a task-equivalence credential on the detectability dimension.

    ``detectability_reduced`` and ``detectability_full`` are paired per-slice
    (or per-patient) observer-detectability measurements — e.g. per-slice CHO
    AUC, CNR, NPWE score, or NEMA CRC — of the same cohort. The credential
    asserts that the population-mean detectability difference is within
    ``epsilon`` at confidence ``1 - alpha`` under the paired-bootstrap
    estimator, with the observer specification published verbatim.

    For ``observer_spec.observer == "cho"`` the recommended estimator is
    ``percentile`` over per-slice AUC values (the default when passing
    paired arrays); DeLong on paired AUC differences is not available because
    per-slice AUC is already an aggregate.
    """
    metric = observer_spec.task_metric
    task = Task(
        name=observer_spec.label,
        metric=metric,  # type: ignore[arg-type]
        target=None,
        ground_truth_protocol="ws1_task_spec_v0.5",
    )
    base = signal_equivalence_credential(
        paired_a=np.asarray(detectability_reduced, dtype=np.float64),
        paired_b=np.asarray(detectability_full, dtype=np.float64),
        signal_ratio=signal_ratio,
        modality=modality,
        task=task,
        subpopulation=subpopulation,
        epsilon=epsilon,
        alpha=alpha,
        method=method,
        reference_method=reference_method,
        estimator=estimator,
        n_bootstrap=n_bootstrap,
        seed=seed,
        sigma_delta_hint=sigma_delta_hint,
        placement_sd_hint=placement_sd_hint,
        bound_M=bound_M,
    )
    a = np.asarray(detectability_reduced, dtype=np.float64)
    b = np.asarray(detectability_full, dtype=np.float64)
    summary = {
        "detectability_reduced_mean": float(np.mean(a)),
        "detectability_full_mean": float(np.mean(b)),
        "detectability_diff_mean": float(np.mean(a - b)),
        "n_slices": int(len(a)),
        "observer": observer_spec.observer,
        "observer_label": observer_spec.label,
    }
    return TaskEquivalenceCredential(
        schema_version=_SCHEMA_VERSION,
        framework_hash=framework_hash(),
        credential=base.credential,
        observer_spec=observer_spec,
        detectability_summary=summary,
    )


#: JSON Schema (draft-07-compatible) for a task-equivalence credential.
#: Extends :data:`CREDENTIAL_JSON_SCHEMA` with the ``observer_spec`` object
#: and the ``detectability_summary`` block; the inner credential object is
#: otherwise unchanged so a signal-equivalence validator keeps working.
TASK_EQUIVALENCE_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "pwm-task-equivalence credential",
    "description": (
        "A task-equivalence credential — a signal-equivalence credential "
        "upgraded with an observer-model detectability dimension: at "
        "equivalent dose, the population-mean observer detectability of M on "
        "reduced-signal scans is within epsilon of M_ref on full-signal scans."
    ),
    "type": "object",
    "required": [
        "schema_version",
        "framework_hash",
        "credential",
        "observer_spec",
        "detectability_summary",
    ],
    "additionalProperties": False,
    "properties": {
        "schema_version": {
            "type": "string",
            "description": "Stable slug. Current value: 'pwm-task-equivalence/v0.1'.",
            "pattern": r"^pwm-task-equivalence/v\d+\.\d+$",
        },
        "framework_hash": CREDENTIAL_JSON_SCHEMA["properties"]["framework_hash"],
        "credential": CREDENTIAL_JSON_SCHEMA["properties"]["credential"],
        "observer_spec": {
            "type": "object",
            "required": ["observer", "label"],
            "additionalProperties": False,
            "properties": {
                "observer": {
                    "type": "string",
                    "enum": ["cho", "cnr", "npwe", "contrast_recovery"],
                },
                "signal_sigma_px": {"type": "number"},
                "peak_contrast_hu": {"type": "number"},
                "location_known": {"type": "boolean"},
                "noise_roi_hu_band": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "n_trials": {"type": "integer", "minimum": 1},
                "label": {"type": "string"},
            },
        },
        "detectability_summary": {
            "type": "object",
            "required": [
                "detectability_reduced_mean",
                "detectability_full_mean",
                "detectability_diff_mean",
                "n_slices",
                "observer",
                "observer_label",
            ],
            "additionalProperties": True,
        },
    },
}
