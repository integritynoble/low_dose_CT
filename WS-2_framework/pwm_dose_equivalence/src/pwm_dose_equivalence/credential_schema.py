"""Explicit JSON Schema for the signal-equivalence credential.

The credential's wire format is defined by :class:`SignalEquivalenceCredential`
in :mod:`pwm_dose_equivalence.credential`; this module exposes that format as
an explicit JSON-Schema-compatible dictionary so a third party can validate
a published credential against a machine-readable schema *without* importing
the Python library.

The schema is deliberately permissive about the ``modality`` field: the v0.3
manuscript validates CT / MRI / PET, but the public API (per the R3-3
modality-extension tutorial) accepts arbitrary modality strings, so the
schema enumerates the validated three and accepts any other string as
``user-implemented``.

The framework specification this schema commits to is pinned by
:data:`pwm_dose_equivalence.framework_hash.FRAMEWORK_SPEC`; a credential
issued under a future ``FRAMEWORK_SPEC`` would carry a different
``framework_hash`` field and would be flagged by :func:`audit_credential`
as ``framework_hash_known = False``.
"""

from __future__ import annotations

from typing import Any

#: JSON Schema (draft-07-compatible) for a published credential.
#:
#: The schema is exposed as a Python ``dict`` rather than a separate
#: ``credential_schema.json`` file so callers can do
#: ``json.dumps(CREDENTIAL_JSON_SCHEMA)`` if they want the on-disk artifact
#: and so the schema travels with the library install (no MANIFEST.in
#: hassle). The shape matches exactly what
#: :meth:`SignalEquivalenceCredential.to_dict` emits.
CREDENTIAL_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "pwm-signal-equivalence credential",
    "description": (
        "A signal-equivalence credential — a testable assertion that a "
        "reconstruction method M is signal-equivalent to a reference method "
        "M_ref at level (r, T, epsilon, alpha) over subpopulation Pi."
    ),
    "type": "object",
    "required": ["schema_version", "framework_hash", "credential"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {
            "type": "string",
            "description": (
                "Stable slug identifying the credential schema version. "
                "Current value: 'pwm-signal-equivalence/v0.2'."
            ),
            "pattern": r"^pwm-signal-equivalence/v\d+\.\d+$",
        },
        "framework_hash": {
            "type": "string",
            "description": (
                "SHA-256 of the framework specification document this "
                "credential commits to. Format: 'sha256:<64-hex-chars>'."
            ),
            "pattern": r"^sha256:[0-9a-f]{64}$",
        },
        "credential": {
            "type": "object",
            "required": [
                "method",
                "reference_method",
                "signal_ratio",
                "modality",
                "task",
                "subpopulation",
                "epsilon",
                "alpha",
                "estimator",
                "n_test",
                "n_bootstrap",
                "seed",
                "delta_mean",
                "delta_ci_low",
                "delta_ci_high",
                "verdict",
            ],
            "additionalProperties": False,
            "properties": {
                "method": {
                    "type": "string",
                    "description": (
                        "Candidate method slug. v0.2 carries a bare string; "
                        "v1.0 of the schema will add an optional "
                        "method.code_hash field for full provenance."
                    ),
                },
                "reference_method": {
                    "type": "string",
                    "description": "Reference method slug (e.g. 'FBP_full_dose').",
                },
                "signal_ratio": {
                    "type": "number",
                    "exclusiveMinimum": 0.0,
                    "maximum": 1.0,
                    "description": (
                        "Reduction ratio r. r=0.25 means the candidate uses "
                        "25 % of the reference's signal."
                    ),
                },
                "modality": {
                    "type": "string",
                    "description": (
                        "Modality tag. CT / MRI / PET are validated in the "
                        "v0.3 manuscript; arbitrary strings are accepted for "
                        "user-implemented modalities (see R3-3 tutorial)."
                    ),
                },
                "task": {
                    "type": "object",
                    "required": ["name", "metric"],
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "metric": {
                            "type": "string",
                            "enum": ["auc", "dice", "mae", "contrast_recovery"],
                        },
                        "target": {"type": ["number", "null"]},
                        "ground_truth_protocol": {"type": ["string", "null"]},
                    },
                },
                "subpopulation": {"type": "string"},
                "epsilon": {
                    "type": "number",
                    "exclusiveMinimum": 0.0,
                    "description": "Equivalence margin.",
                },
                "alpha": {
                    "type": "number",
                    "exclusiveMinimum": 0.0,
                    "exclusiveMaximum": 1.0,
                    "description": "Significance level (typically 0.05).",
                },
                "estimator": {
                    "type": "string",
                    "enum": ["percentile", "delong", "bca"],
                },
                "n_test": {"type": "integer", "minimum": 1},
                "n_bootstrap": {"type": "integer", "minimum": 0},
                "seed": {"type": "integer"},
                "delta_mean": {"type": "number"},
                "delta_ci_low": {"type": "number"},
                "delta_ci_high": {"type": "number"},
                "verdict": {
                    "type": "string",
                    "enum": ["PASS", "FAIL", "INDETERMINATE"],
                },
                "sample_size_check": {
                    "type": "object",
                    "description": (
                        "Optional pre-flight sample-size check. Empty dict "
                        "if no sigma/placement hint was supplied at issue "
                        "time."
                    ),
                    "additionalProperties": True,
                },
            },
        },
    },
}
