"""Credential audit — check a published credential's *internal* consistency.

A credential is the wire-format output of
:func:`signal_equivalence_credential`. A third party can audit a credential
*without* re-running the bootstrap by checking three things:

1.  **Schema validity** — the JSON matches
    :data:`CREDENTIAL_JSON_SCHEMA` (required fields, types, enums, patterns).
2.  **Framework-hash recognition** — the credential's ``framework_hash``
    matches the currently-installed library's
    :func:`framework_hash` output. A mismatch is not an error
    (credentials issued under earlier framework versions stay valid against
    their own hash) but it is recorded as a warning so the auditor knows to
    resolve the hash against the appropriate version of the framework
    specification.
3.  **Verdict self-consistency** — re-derive the verdict from the credential's
    own ``(delta_ci_low, delta_ci_high, epsilon)`` and check it matches the
    stored ``verdict`` field. A mismatch is a hard issue: the credential's
    verdict is not what its CI implies.

This audit does *not* re-run the bootstrap (that would require the original
test-set scores). For full reproduction, see ``paper_draft/reproduction_guide.md``.
For non-coder credential interpretation, see
``paper_draft/credential_reading_guide.md``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA
from pwm_dose_equivalence.estimator import verdict_from_ci
from pwm_dose_equivalence.framework_hash import framework_hash

__all__ = ["CredentialAudit", "audit_credential"]


@dataclass
class CredentialAudit:
    """The result of auditing a published credential.

    ``ok`` is ``True`` iff every hard check passed (``schema_valid``,
    ``verdict_self_consistent``, no items in ``issues``). Soft signals
    (``framework_hash_known = False``, ``sample_size_check_ok = False``
    with a PASS verdict, BCa as headline) are recorded in ``warnings``
    but do not flip ``ok``.
    """

    ok: bool
    schema_valid: bool
    framework_hash_known: bool
    verdict_self_consistent: bool
    sample_size_check_ok: bool | None
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_SCHEMA_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


def _compile_pattern(pattern: str) -> re.Pattern[str]:
    if pattern not in _SCHEMA_PATTERN_CACHE:
        _SCHEMA_PATTERN_CACHE[pattern] = re.compile(pattern)
    return _SCHEMA_PATTERN_CACHE[pattern]


def _check_type(value: Any, json_type: str | list[str]) -> bool:
    if isinstance(json_type, list):
        return any(_check_type(value, t) for t in json_type)
    if json_type == "string":
        return isinstance(value, str)
    if json_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if json_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if json_type == "object":
        return isinstance(value, dict)
    if json_type == "null":
        return value is None
    raise ValueError(f"_check_type: unsupported JSON type {json_type!r}")


def _validate_against_schema(
    instance: Any, schema: dict[str, Any], path: str, issues: list[str]
) -> None:
    expected_type = schema.get("type")
    if expected_type is not None and not _check_type(instance, expected_type):
        issues.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
        return

    if "enum" in schema and instance not in schema["enum"]:
        issues.append(f"{path}: value {instance!r} not in enum {schema['enum']}")

    if isinstance(instance, str) and "pattern" in schema:
        if not _compile_pattern(schema["pattern"]).match(instance):
            issues.append(f"{path}: value {instance!r} does not match pattern {schema['pattern']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            issues.append(f"{path}: value {instance} < minimum {schema['minimum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            issues.append(
                f"{path}: value {instance} <= exclusiveMinimum {schema['exclusiveMinimum']}"
            )
        if "maximum" in schema and instance > schema["maximum"]:
            issues.append(f"{path}: value {instance} > maximum {schema['maximum']}")
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            issues.append(
                f"{path}: value {instance} >= exclusiveMaximum {schema['exclusiveMaximum']}"
            )

    if isinstance(instance, dict) and expected_type == "object":
        for required in schema.get("required", []):
            if required not in instance:
                issues.append(f"{path}: missing required field {required!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    issues.append(f"{path}: unexpected field {key!r}")
        for key, sub_schema in properties.items():
            if key in instance:
                _validate_against_schema(
                    instance[key], sub_schema, f"{path}.{key}", issues
                )


def audit_credential(credential: dict[str, Any] | str) -> CredentialAudit:
    """Audit a published credential's internal consistency.

    Accepts either a JSON string or a parsed dict. Returns a
    :class:`CredentialAudit` recording the results of every check.

    The audit does not require the original test-set scores; it inspects
    only the published credential itself. For full bootstrap reproduction
    use ``paper_draft/reproduction_guide.md``.
    """
    issues: list[str] = []
    warnings: list[str] = []

    if isinstance(credential, str):
        try:
            parsed = json.loads(credential)
        except json.JSONDecodeError as exc:
            return CredentialAudit(
                ok=False,
                schema_valid=False,
                framework_hash_known=False,
                verdict_self_consistent=False,
                sample_size_check_ok=None,
                issues=[f"top: not valid JSON ({exc.msg} at pos {exc.pos})"],
                warnings=[],
            )
    else:
        parsed = credential

    if not isinstance(parsed, dict):
        return CredentialAudit(
            ok=False,
            schema_valid=False,
            framework_hash_known=False,
            verdict_self_consistent=False,
            sample_size_check_ok=None,
            issues=[f"top: expected object, got {type(parsed).__name__}"],
            warnings=[],
        )

    _validate_against_schema(parsed, CREDENTIAL_JSON_SCHEMA, "$", issues)
    schema_valid = not issues

    framework_hash_known = False
    verdict_self_consistent = False
    sample_size_check_ok: bool | None = None

    if schema_valid:
        framework_hash_known = parsed["framework_hash"] == framework_hash()
        if not framework_hash_known:
            warnings.append(
                f"framework_hash {parsed['framework_hash']} does not match the "
                f"currently-installed library's {framework_hash()}. The credential "
                "was likely issued under an earlier framework version; resolve "
                "the hash against the matching FRAMEWORK_SPEC string."
            )

        cred = parsed["credential"]

        if cred["delta_ci_low"] > cred["delta_ci_high"]:
            issues.append(
                "$.credential: delta_ci_low > delta_ci_high "
                "(empty CI is impossible)"
            )
        elif not (cred["delta_ci_low"] <= cred["delta_mean"] <= cred["delta_ci_high"]):
            issues.append(
                "$.credential: delta_mean falls outside [delta_ci_low, delta_ci_high]"
            )

        expected_verdict = verdict_from_ci(
            cred["delta_ci_low"], cred["delta_ci_high"], cred["epsilon"]
        )
        verdict_self_consistent = expected_verdict == cred["verdict"]
        if not verdict_self_consistent:
            issues.append(
                f"$.credential.verdict: stored {cred['verdict']!r} but "
                f"({cred['delta_ci_low']}, {cred['delta_ci_high']}) vs "
                f"epsilon={cred['epsilon']} implies {expected_verdict!r}"
            )

        if cred["estimator"] == "delong" and cred["n_bootstrap"] != 0:
            warnings.append(
                "$.credential: estimator='delong' is closed-form; n_bootstrap "
                f"should be 0 but is {cred['n_bootstrap']}"
            )

        if cred["estimator"] == "bca":
            warnings.append(
                "$.credential.estimator: BCa is opt-in only per "
                "theory/proofs/estimator.md §4 — does not robustly "
                "outperform percentile under the null. Confirm a percentile "
                "companion exists."
            )

        ssc = cred.get("sample_size_check") or {}
        if "ok" in ssc:
            sample_size_check_ok = bool(ssc["ok"])
            if not ssc["ok"] and cred["verdict"] == "PASS":
                warnings.append(
                    "$.credential: PASS verdict issued on a cohort below the "
                    "formula prescription (sample_size_check.ok=False). The "
                    "verdict may be a fluke; treat with caution."
                )

    ok = schema_valid and verdict_self_consistent and not issues

    return CredentialAudit(
        ok=ok,
        schema_valid=schema_valid,
        framework_hash_known=framework_hash_known,
        verdict_self_consistent=verdict_self_consistent,
        sample_size_check_ok=sample_size_check_ok,
        issues=issues,
        warnings=warnings,
    )
