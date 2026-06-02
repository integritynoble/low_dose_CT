"""SHA-256 content-addressing of the framework definition.

The framework is versioned by a stable specification string that captures the
minimal information a verifier needs to re-run the bootstrap. The
:py:data:`FRAMEWORK_SPEC` constant is the v0.2 specification; its SHA-256 hash
is exposed via :py:func:`framework_hash` and embedded in every credential.

A future :py:mod:`pwm_dose_equivalence` release with a breaking change to the
estimator semantics or the credential schema must bump ``FRAMEWORK_SPEC`` and
will produce a new hash; credentials issued under the old hash continue to
resolve to the old specification.
"""

from __future__ import annotations

import hashlib

#: Canonical specification string for v0.2 of the framework.
#:
#: Editing this string is the *only* supported way to bump the framework
#: version. A credential's ``framework_hash`` field is the SHA-256 of this
#: string; changing the string changes the hash. The string is deliberately
#: short — it pins the credential to a specific framework-paper section and
#: estimator defaults, while the substantive definition lives in the linked
#: theory document.
FRAMEWORK_SPEC = (
    "pwm-signal-equivalence/v0.2\n"
    "definition: M is signal-equivalent to M_ref at (r, T, epsilon, alpha) over Pi "
    "iff |E_Pi[E[P(T(M(T_r(S_ref(x)))), g(x))]] - E_Pi[E[P(T(M_ref(S_ref(x))), g(x))]]| < epsilon "
    "with confidence >= 1 - alpha under the paired-bootstrap estimator.\n"
    "estimator-defaults: percentile (general); delong (task.metric == auc); bca opt-in.\n"
    "Pi-carries: acquisition-protocol metadata (CT vendor/kVp; MRI mask_family; PET tracer/scanner).\n"
    "composition: not derivable; each credential is point-evaluated.\n"
    "ref: theory/dose-equivalence-framework.md @ v0.1 (manuscript v0.2 supersedes for "
    "estimator-defaults, Pi-as-metadata, point-evaluated-by-design; see paper_draft/CHANGELOG.md)."
)


def framework_hash(spec: str = FRAMEWORK_SPEC) -> str:
    """Return ``sha256:<hex>`` of the framework specification string."""
    digest = hashlib.sha256(spec.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
