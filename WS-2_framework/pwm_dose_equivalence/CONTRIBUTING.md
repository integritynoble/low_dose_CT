# Contributing to `pwm_dose_equivalence`

Thank you for considering a contribution. This library is the reference
implementation of the **signal-equivalence framework** described in the
*Nature Methods* manuscript [`paper_draft/manuscript.tex`](../paper_draft/manuscript.tex)
(v0.3 working draft, 24 pp). Because the library is intended to be cited as a
*methodological standard*, the contribution rules are tighter than for an
ordinary research codebase: a published credential is only as trustworthy as
the version of this library that issued it.

If you are looking for *how to use* the library, see
[`README.md`](README.md). If you are auditing a published credential, see
[`../paper_draft/credential_reading_guide.md`](../paper_draft/credential_reading_guide.md).
This file is about *how to change* the library.

---

## Quick links

* Issues: [github.com/integritynoble/low_dose_CT/issues](https://github.com/integritynoble/low_dose_CT/issues)
* CI matrix: Python 3.10 / 3.11 / 3.12 on Linux (macOS / Windows runners scheduled at v1.0.0)
* License: Apache 2.0 ([LICENSE](LICENSE))
* Governance: PWM Protocol Foundation
* Citation: [CITATION.cff](CITATION.cff)

---

## Development environment

```bash
git clone https://github.com/integritynoble/low_dose_CT
cd low_dose_CT/WS-2_framework/pwm_dose_equivalence
pip install -e ".[test]"
pytest                               # expect: 139 passed, 100% coverage
```

The library requires Python ≥ 3.10, NumPy ≥ 1.24, SciPy ≥ 1.10. No
mandatory runtime dependencies beyond NumPy / SciPy; test extras add
`pytest` and `pytest-cov` only.

---

## What you can change without a PR

Nothing. Every change goes through a pull request, even one-line typo fixes.
The reason is the library's content-addressed framework hash: if a commit
silently lands on `main` without a maintainer reviewing the credential
schema and `FRAMEWORK_SPEC` for unintended changes, a downstream credential
could be issued under an undocumented framework version.

---

## How to make a PR

1. **Fork & branch.** Branch from `main`; name the branch with the issue
   number if one exists (e.g. `42-fix-delong-edge-case`).
2. **Run the test suite locally.** `pytest --cov=pwm_dose_equivalence`. The
   ship floor is **90 % line coverage** (manuscript §software_rigor
   pre-registered floor); the current library ships at **100 %** on 437
   statements and we expect new PRs to preserve that.
3. **Add tests for new behaviour.** A PR adding new public API without
   tests will be asked to add them before review.
4. **Update documentation.** If your PR changes user-facing behaviour, update
   the relevant section of `README.md`, the manuscript draft, and / or
   `../paper_draft/credential_reading_guide.md`.
5. **Open the PR.** Use a descriptive title; link the issue if one exists.
   The PR template will prompt you for the sign-off tier (below).
6. **CI must pass.** All checks green is a prerequisite for review.

---

## Sign-off tiers

Different parts of the library carry different change risk. The tier
determines how many maintainer sign-offs are required.

### Tier A — two of three maintainer sign-offs

Changes that affect the *methodological substance* of the framework:

* `src/pwm_dose_equivalence/framework_hash.py` — the `FRAMEWORK_SPEC`
  string and `framework_hash` function. Editing the spec string changes
  the hash and is the **only** supported way to bump the framework
  version. A Tier-A change here is a **MAJOR** version bump.
* `src/pwm_dose_equivalence/credential.py` and
  `src/pwm_dose_equivalence/credential_schema.py` — the credential
  wire format. Any field addition / removal / type change is **MAJOR**
  (breaks credential reproducibility).
* `src/pwm_dose_equivalence/estimator.py` — the percentile / DeLong /
  BCa estimators and `verdict_from_ci`. Any change to the verdict
  logic, the CI computation, or the estimator defaults is
  methodologically load-bearing.
* `src/pwm_dose_equivalence/sample_size.py` — the (S1) / (S3) / (S4)
  formulas. Any change must come with an updated derivation in
  `../theory/proofs/sample_size.md` and the corresponding numerical
  table values.
* `src/pwm_dose_equivalence/operators.py` — the per-modality `T_r`
  operators. Adding a new modality is a Tier-A **MINOR** bump
  (non-breaking); changing the canonical reduction operator for an
  existing modality is a **MAJOR** bump.

### Tier B — one maintainer sign-off

Changes that do not affect the methodological substance:

* `src/pwm_dose_equivalence/api.py` — *if* the change is API-additive
  (new optional kwargs with defaults that preserve existing behaviour).
  Breaking changes to `signal_equivalence_credential` are Tier A.
* `src/pwm_dose_equivalence/audit.py` and
  `src/pwm_dose_equivalence/cli.py` — the audit and CLI surfaces.
  Adding checks is non-breaking; tightening an existing check that
  would flip an `ok=True` credential to `ok=False` is Tier A.
* `tests/` — adding tests, refactoring tests, fixing flaky tests.
* `notebooks/` — adding tutorial notebooks, fixing notebook bugs.
* `examples/` — adding worked-example credentials, updating
  `regenerate.py`. The `tests/test_examples.py` drift checks must
  continue to pass.
* `README.md`, `CONTRIBUTING.md`, `CITATION.cff`, in-code docstrings —
  documentation-only changes.
* `paper_draft/` markdown files (`credential_reading_guide.md`,
  `reproduction_guide.md`, `CHANGELOG.md`) when the change is purely
  documentary.

If you are unsure which tier applies, default to Tier A and flag the
ambiguity in the PR description; a maintainer will reclassify if needed.

---

## Versioning policy

Semantic versioning (`MAJOR.MINOR.PATCH`):

* **MAJOR** — bumps `FRAMEWORK_SPEC`. Breaks credential JSON schema or
  estimator semantics. Old credentials remain valid against the old
  framework hash; new credentials are issued under the new hash.
* **MINOR** — adds a modality, estimator, task type, or audit check.
  Non-breaking; existing credentials remain valid under the same
  framework hash.
* **PATCH** — bug fixes that preserve credential reproducibility.

A PR proposing a MAJOR bump must also update the manuscript draft, the
relevant `../theory/proofs/` document, and the CHANGELOG `Schema unchanged`
sections (which become `Schema bumped` sections).

The current version is `0.2.2`. We target `1.0.0` at *Nature Methods*
paper acceptance with a five-year support commitment.

---

## Schema mutation discipline

Any PR that touches `framework_hash.py`, `credential.py`, or
`credential_schema.py` must:

1. Update `FRAMEWORK_SPEC` (only if the change is methodological — pure
   docstring changes do not require a hash bump).
2. Re-run `python3 scripts/dump_schema.py` to refresh
   `credential_schema.json` so the standalone artifact stays in sync.
3. Re-run `python3 examples/regenerate.py` if the schema change affects
   any example credential.
4. Bump `__version__` in `__init__.py` and `version` in `pyproject.toml`
   per the versioning policy above.
5. Add a CHANGELOG entry in `../paper_draft/CHANGELOG.md`.
6. Two maintainer sign-offs (Tier A).

If you forget step 2, `tests/test_examples.py::test_schema_json_matches_python_dict`
will catch it.

---

## Code style

* PEP 8 with `ruff` defaults; line length 100. Configured in
  [`pyproject.toml`](pyproject.toml) `[tool.ruff]` (line-length = 100;
  target-version = py310) and `[tool.ruff.lint]` (select = E, F, I, UP).
  Install via `pip install -e ".[lint]"` and run with `ruff check src/
  tests/`. All currently-committed code passes cleanly.
* PEP 484 type annotations on every public function; `mypy --strict`
  should pass on the `src/` tree. Configured in [`pyproject.toml`](pyproject.toml)
  `[tool.mypy]` (strict = true; python_version = 3.10) with a single
  `[[tool.mypy.overrides]]` entry for `scipy.*` (SciPy does not publish
  type stubs as of 2026). Run with `mypy`. All currently-committed code
  passes cleanly.
* Docstrings: short imperative first line; reST or plain prose body;
  cite the corresponding manuscript section / proofs document where
  the implementation choice is justified.
* No emojis in code or commit messages.
* Comments only when the *why* is non-obvious — no comments that
  restate what the code does.

> **The `FRAMEWORK_SPEC` exception.** `src/pwm_dose_equivalence/framework_hash.py`
> carries one `# noqa: E501` per long-line literal. The literals are part
> of the SHA-256-hashed content that anchors every issued credential;
> reformatting them (including any whitespace change) would change the
> framework hash and silently invalidate every credential issued under
> the current `FRAMEWORK_SPEC`. The `noqa` is deliberate and load-bearing.
> A PR that removes it without bumping the framework spec is Tier A and
> will not be accepted.

---

## Testing

* Every new public function should have at least one test exercising
  its happy path and one exercising a failure mode.
* `pytest --cov=pwm_dose_equivalence --cov-report=term-missing`
  should report 100 % line coverage on the `src/` tree. If your PR
  introduces an unreachable defensive branch, mark it
  `# pragma: no cover` (with a one-line justification comment) rather
  than padding the test suite.
* End-to-end / integration tests (`tests/test_integration.py`,
  `tests/test_cli.py`, `tests/test_examples.py`) must continue to pass.
  Adding a new public-API method should add a corresponding
  integration test row.

---

## Reporting bugs

* Open an issue at
  [github.com/integritynoble/low_dose_CT/issues](https://github.com/integritynoble/low_dose_CT/issues)
  using the appropriate template:
  * **Bug report** (`.github/ISSUE_TEMPLATE/bug_report.md`) — for general
    library / data / documentation defects.
  * **Credential audit issue** (`.github/ISSUE_TEMPLATE/credential_audit_issue.md`)
    — when you believe `audit_credential` or `pwm-audit` returned the
    wrong verdict on a credential.
  * **Feature request** (`.github/ISSUE_TEMPLATE/feature_request.md`) —
    for new functionality or methodological extensions; includes a
    sign-off-tier checkbox so reviewers know what level of review the
    proposal will need.
* The templates pre-fill the environment information we need (library
  version, Python / NumPy / SciPy versions, OS) so we do not have to
  ask for it as a follow-up.
* GitHub's "blank issue" option is disabled (via
  `.github/ISSUE_TEMPLATE/config.yml`) so reporters land in one of the
  three templates by default. The `config.yml` also lists four
  contact-link shortcuts: reading guide, reproduction guide, security
  channel, contribution policy.

---

## Security

Security issues — including credential forgery (a credential that
audits as `ok=True` but does not match its CI), framework-hash
collision, schema-validation bypass, and audit-state injection — are
covered by the repository-root [`SECURITY.md`](../../SECURITY.md). The
short version: **do not open a public GitHub issue**. Use the private
channel listed in `SECURITY.md`. The default coordinated-disclosure
window is 90 days; the policy describes acknowledgment, advisory
publication, and the `FRAMEWORK_SPEC`-bump procedure when a fix
requires a schema change.

`SECURITY.md` also explicitly enumerates what is and is not in scope
(in: credential reproducibility breaks; out: upstream NumPy/SciPy
bugs, manuscript typos, the placeholder maintainer list).

---

## Maintainers

The three named maintainers are placeholders until the library's first
external contributor PR lands; the manuscript draft's `\todo{author
list}` populates at submission.

* Maintainer A — *TBA at v0.3 → v0.4 manuscript revision*
* Maintainer B — *TBA at v0.3 → v0.4 manuscript revision*
* Maintainer C — *TBA at v0.3 → v0.4 manuscript revision*

Until then, the PWM Protocol Foundation (`maintainers@pwm-protocol.org`,
placeholder) is the single sign-off authority for both tiers.

---

## License

By contributing, you agree that your contributions will be licensed
under the Apache License 2.0 (see [LICENSE](LICENSE)). You retain
copyright in your contributions.
