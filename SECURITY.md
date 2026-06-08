# Security policy

This document describes how to report security vulnerabilities in any
workstream of the `low_dose_CT` repository. The primary security surface
is the **WS-2 signal-equivalence framework**
([`WS-2_framework/pwm_dose_equivalence/`](WS-2_framework/pwm_dose_equivalence/));
the WS-1 dataset pipeline, the WS-3 reference method, and the WS-4
leaderboard each have their own narrower surfaces and are covered below.

If you are looking for *contribution guidelines* (sign-off tiers, code
style, schema-mutation discipline), see
[`WS-2_framework/pwm_dose_equivalence/CONTRIBUTING.md`](WS-2_framework/pwm_dose_equivalence/CONTRIBUTING.md).
If you are looking for *credential interpretation* without writing code,
see
[`WS-2_framework/paper_draft/credential_reading_guide.md`](WS-2_framework/paper_draft/credential_reading_guide.md).
This file is about *reporting vulnerabilities* in either.

---

## Supported versions

| Workstream | Version | Status |
|---|---|---|
| WS-2 `pwm_dose_equivalence` library | `0.2.x` | Supported (alpha) |
| WS-2 `pwm_dose_equivalence` library | `< 0.2.0` | Unsupported — please upgrade |
| WS-2 manuscript (`paper_draft/manuscript.tex`) | v0.3 working draft | Supported |
| WS-1 dataset pipeline (`WS-1_dataset/pipelines/`) | v0.5 | Supported |
| WS-3 reference method | — | Pre-release; not yet covered |
| WS-4 leaderboard | — | Pre-release; not yet covered |

We commit to support the WS-2 `0.2.x` series with security fixes through
the v1.0.0 release (target: alongside *Nature Methods* manuscript
acceptance) and the v1.0.x series for five years thereafter.

---

## What counts as a security issue

### WS-2 library — critical

The library is intended to be cited as a methodological standard. The
load-bearing security property is that **a credential's audit verdict
must be reproducible**: a third party running `audit_credential` on the
same JSON, with the same `FRAMEWORK_SPEC`, must compute the same
`CredentialAudit`. Anything that breaks this property is a critical
vulnerability:

* **Credential forgery.** A credential JSON that `audit_credential`
  reports as `ok=True` but whose stored verdict does not match what
  `verdict_from_ci(delta_ci_low, delta_ci_high, epsilon)` returns.
* **Hash collision.** A `FRAMEWORK_SPEC` string $s' \neq s$ for which
  `framework_hash(s') == framework_hash(s)`. Extremely unlikely with
  SHA-256, but please report if you have a construction.
* **Schema-validation bypass.** A credential JSON that violates the
  `CREDENTIAL_JSON_SCHEMA` (missing required field, out-of-range
  numeric, wrong enum) but that `audit_credential` reports as
  `schema_valid=True`.
* **Audit-state injection.** Calling `audit_credential` with one
  credential and getting a `CredentialAudit` whose state depends on a
  *different* credential previously audited (state leakage between
  calls — none should exist; the function is pure).

### WS-2 library — non-critical

These are still security-relevant but do not break the reproducibility
guarantee:

* Denial-of-service via a maliciously crafted credential JSON (e.g., a
  pathological string that makes the validator hang).
* Information disclosure (e.g., a stack trace that reveals a file path
  the user didn't intend to expose). Note: the library reads only the
  files explicitly passed to it; it does not auto-discover.

### WS-1 dataset pipeline

* Adapter code paths that execute attacker-controlled DICOM tag values
  as code or shell commands.
* Manifest hashes that can be silently changed without invalidating
  downstream consumers' integrity checks.
* Patient-identifier leakage through filenames, logs, or commit history.

### WS-3 / WS-4

Pre-release; not yet covered. We will add explicit policy when these
workstreams enter beta.

### Out of scope

* Bugs in NumPy, SciPy, or other upstream dependencies. Report those
  to the upstream projects directly. We will accept reports of
  *exploitable* combinations of upstream bugs that affect us, but we
  will redirect generic upstream-bug reports.
* Bugs in the *manuscript prose* (typos, inaccurate citations, unclear
  argument). Those are correctness issues, not security issues; use
  the bug-report issue template.
* The current *placeholder* in `CONTRIBUTING.md` `Maintainers` section
  (`TBA at v0.3 → v0.4 manuscript revision`) is a documentation gap,
  not a security issue.

---

## How to report

**Do not open a public GitHub issue for security-class problems.**

Until the v1.0.0 release names persistent maintainers, please contact
the PWM Protocol Foundation via the contact listed in
[`WS-2_framework/pwm_dose_equivalence/CITATION.cff`](WS-2_framework/pwm_dose_equivalence/CITATION.cff)
(`authors[].website`) with the subject line `[security] low_dose_CT —
<short description>`. Include:

1. A description of the issue and its expected impact.
2. A minimal reproducer (a small Python script, a malformed credential
   JSON, a DICOM tag value, etc.).
3. The library / repository commit hash you observed it on.
4. Your suggested disclosure timeline if you have one (otherwise the
   default below applies).

We will acknowledge receipt within **5 business days** and provide an
initial assessment within **15 business days**.

### Coordinated-disclosure window

Default: **90 days** from initial report. We will:

1. Confirm or refute the vulnerability internally.
2. If confirmed, develop a fix and a release plan.
3. Cut a patch release (or a minor / major release if the fix
   requires a `FRAMEWORK_SPEC` bump per
   [`CONTRIBUTING.md`](WS-2_framework/pwm_dose_equivalence/CONTRIBUTING.md)
   "Schema mutation discipline").
4. Publish a public advisory crediting the reporter (unless they
   request anonymity).

If 90 days proves insufficient (e.g., the fix requires a coordinated
upstream change in NumPy / SciPy), we will propose an extension to the
reporter in writing rather than silently pass the deadline.

We do **not** offer monetary bug bounties at this stage. We do offer
public acknowledgment in the relevant CHANGELOG entry, and (for
substantive findings) a named acknowledgment in the next manuscript
revision's `\section*{Acknowledgments}`.

---

## What we will not do

* We will not silently land a security fix without a CHANGELOG entry.
  Every fix is recorded in [`WS-2_framework/paper_draft/CHANGELOG.md`](WS-2_framework/paper_draft/CHANGELOG.md)
  with the issue ID and the disclosure window.
* We will not retroactively edit the `FRAMEWORK_SPEC` to "fix" an
  in-the-wild credential. If a credential issued under an
  earlier `FRAMEWORK_SPEC` is affected by a vulnerability, the fix
  bumps the spec (and therefore the hash); old credentials remain
  resolvable against the old hash, with a known-vulnerability
  annotation in the public advisory.
* We will not accept reports submitted via social media, public
  forums, or comments on unrelated PRs. The private channel above is
  the only intake.

---

## Acknowledgments

This document was added on 2026-06-08 (D9 + 19) alongside the WS-2
v0.2.2 library and the manuscript v0.3 working draft. We will list
acknowledgment of confirmed reporters here as advisories are published.

*No advisories issued to date.*
