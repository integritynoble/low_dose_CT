# `manuscript.tex` changelog

This file records substantive edits to the signal-equivalence framework
manuscript draft. Each entry lists the audit item it closed, the commit it
landed in, and what the change was for. Trivial typo and formatting fixes are
not logged here — see `git log -- manuscript.tex` for the full history.

The audit-item labels (A1–A6, B1–B5) refer to the Nature Methods
reviewer-readiness audit posted in the 2026-06-01 working session.

---

## `limitations_anchors.md` — D9 + 19 (2026-06-08)

Companion to the V3-12 manuscript §Discussion "Limitations of the present work" subsubsection. The reproduction guide §10 anchors every *positive* numerical claim in the manuscript; this new document anchors every *limitation* the manuscript explicitly acknowledges. A reviewer can use it to confirm that each acknowledged gap is honestly described, not hand-waved.

| ID | What landed | Commit |
|---|---|---|
| **R3-5** | **`paper_draft/limitations_anchors.md`** — 5-section anchor document, one section per V3-12 limitation paragraph. Each section verbatim-quotes the manuscript paragraph, then provides (a) an anchor table mapping the claim to specific repo files (proofs document + experiment + simulation `results.json` + reading-guide section), (b) a "Closes when" entry naming the roadmap milestone that would resolve the limitation, (c) a "Why this is the right framing" / "Practical implication" close that explains the substance. L-1: synthetic vs real-cohort (closes at Phase 1 / 3a / 3b data). L-2: three modalities validated; extension surface not (closes when an independent external group issues a credential under a user-implemented modality). L-3: schema does not pin `method.code_hash` (closes at v1.0 Tier-A schema bump). L-4: reader-variability ceiling on $\varepsilon$ (closes via the v1.0 per-task label-noise registry). L-5: WS-1 v0.5 INDETERMINATE-dominated regime (closes when prospective v1.0 cohort reaches n ≥ 500). | *(this commit)* |
| **R3-5-prop** | **Cross-link propagation.** `reproduction_guide.md` §10a expanded to a three-document table (positive-claim / non-coder / limitations). `credential_reading_guide.md` §8 cross-references gain a link to the new document. **Manuscript §Discussion intro to "Limitations of the present work" gains one sentence** pointing reviewers at `paper_draft/limitations_anchors.md` for the per-paragraph anchor / closure-milestone tables. PDF rebuilt at 24 pp (unchanged). | *(this commit)* |

### Why this is R3-5 (not V3-N)

The `R3-N` convention (introduced at R3-1) marks *reviewer-facing reproduction artifacts* — documents that sit alongside the manuscript but are not part of the manuscript's submitted text. R3-1 was the reproduction guide; R3-2 / R3-3 were the tutorial notebooks; R3-4 was the credential reading guide. R3-5 follows the same pattern: the manuscript prose is unchanged-modulo-one-sentence, and the substance lives in a companion document that a reviewer can pull alongside the PDF.

### The three-document reviewer surface

| Document | Audience | Question it answers |
|---|---|---|
| `reproduction_guide.md` (R3-1) | Code-savvy reviewer | *How do I re-derive the manuscript's positive numerical claims?* |
| `credential_reading_guide.md` (R3-4) | Non-coder reviewer / regulator / clinician | *How do I read a credential someone else published?* |
| `limitations_anchors.md` (R3-5, this commit) | Any reviewer | *Where is each manuscript-acknowledged limitation backed by evidence?* |

The three are deliberately disjoint and together cover the full review surface.

### Schema unchanged (a tenth time)

Pure documentation addition. No library code, no `FRAMEWORK_SPEC` edit, no test or schema change. The manuscript prose change is one sentence; the substance is in the companion document.

---

## Makefile + GitHub Actions CI + dependabot — D9 + 19 (2026-06-08)

Closes the last in-session-executable governance item: backs the manuscript §software_rigor "Continuous integration runs on every commit against Python 3.10, 3.11, and 3.12 on Linux runners" claim with an actual workflow file, and wraps every gate (ruff + mypy + pytest with coverage + framework-hash invariant) behind one local-runnable `make ci` command.

| ID | What landed | Commit |
|---|---|---|
| **ci-1** | **`pwm_dose_equivalence/Makefile`** with 11 targets: `install`, `lint`, `typecheck`, `test`, `coverage`, `regenerate-examples`, `regenerate-schema`, `regenerate-snapshots`, `regenerate` (composite), `ci` (= lint + typecheck + coverage; the one-command PR gate), `clean`. `make help` (also the default target) prints the list. Verified `make ci` runs to green on a fresh `pip install -e ".[test,lint]"`. | *(this commit)* |
| **ci-2** | **`.github/workflows/ci.yml`** at the repo root — GitHub Actions workflow that runs the same gates `make ci` runs, on the matrix `python-version: [3.10, 3.11, 3.12] / ubuntu-latest`. Triggers: push to `main` or `heyang`; PR targeting `main`. Steps: checkout, setup-python with pip cache, install with `.[test,lint]`, ruff, mypy, pytest with coverage, **plus a final framework-hash invariant check that fails CI if any commit edits `FRAMEWORK_SPEC` without a Tier-A MAJOR-version bump** (silent-schema-break protection). Backs the manuscript §software_rigor "CI runs on every commit against Python 3.10, 3.11, and 3.12 on Linux runners" claim. macOS / Windows runners are scheduled at v1.0.0. | *(this commit)* |
| **ci-3** | **`.github/dependabot.yml`** — passive dependency updates on monthly cadence. Two ecosystems: `pip` (the library's `pyproject.toml` dependencies, scoped to the WS-2 directory) and `github-actions` (the workflow's actions versions). Open-PR limit 5 per ecosystem. Commit-message prefixes `deps` and `deps(ci)`. Labels include `WS-2` so issue triage knows which workstream a dependency PR belongs to. Per CONTRIBUTING.md, Dependabot PRs touching `pyproject.toml` dependencies are Tier B by default unless they bump `numpy` or `scipy` major version, which is Tier A (both packages can move credential numerical reproducibility). | *(this commit)* |
| **ci-4** | **CONTRIBUTING.md "How to make a PR" section rewritten** — the previous 6-step list described what to do; the new 8-step list names the `make ci` command (step 2), the `make regenerate` command for generated artifacts (step 3), and the explicit 90 %-floor / 100 %-current coverage anchor (step 4). The PR-gate guidance is now actionable: a contributor knows exactly what `make` target to run before opening a PR. | *(this commit)* |

### Why the framework-hash invariant lives in CI

The schema-mutation discipline (CONTRIBUTING.md §"Schema mutation discipline") tells a contributor to bump `FRAMEWORK_SPEC` when changing the framework definition. But discipline is not enforcement. A contributor making a *unrelated* edit (e.g. a whitespace fix in `framework_hash.py`'s docstring) could silently change the bytes of `FRAMEWORK_SPEC` if the bytes happen to be in a string the contributor is editing. The CI step `Verify FRAMEWORK_SPEC hash is unchanged` runs `framework_hash()` on every commit and fails CI if the output does not match the recorded `sha256:b366f51c…` byte-for-byte. A real schema bump produces a new hash and is then a single 2-line update to the CI step (new expected hash + new CHANGELOG row) — explicit by design.

### What §software_rigor now backs (further updated)

| Claim in paragraph | Backing artifact |
|---|---|
| CI runs on every commit against Python 3.10 / 3.11 / 3.12 on Linux runners | `.github/workflows/ci.yml` (this commit) |
| macOS / Windows runners scheduled at v1.0.0 | `.github/workflows/ci.yml` `matrix: os: [ubuntu-latest]` (v1.0 will add `macos-latest`, `windows-latest`) |
| 90 % minimum line coverage | `pytest --cov=pwm_dose_equivalence` step in CI; currently 100 % on 439 statements |
| Contribution policy in `CONTRIBUTING.md` | Already backed by L0.2.2-gov-1; "How to make a PR" rewrite tightens it further |
| Issue template | Already backed by gov-issue-1..4 |
| Security disclosure | Already backed by gov-sec-1; `SECURITY.md` |
| Two-tier maintainer sign-off | Already backed; CONTRIBUTING.md "Sign-off tiers" |

Every concrete claim in §software_rigor now resolves to an artifact AND has a CI gate enforcing it.

### Schema unchanged (a ninth time)

`FRAMEWORK_SPEC` byte-for-byte identical (now actually checked by CI). No library code change. `make` is the only new external dependency; on systems without it, the CONTRIBUTING.md commands fall back to direct `pip` / `ruff` / `mypy` / `pytest` invocations as documented.

---

## ruff + mypy config + 4 type-safety fixes — D9 + 19 (2026-06-08)

Backs the CONTRIBUTING.md "PEP 8 with ruff defaults; line length 100" and "mypy --strict should pass on the src/ tree" claims with actual `[tool.ruff]` / `[tool.mypy]` config blocks in `pyproject.toml`. Previously those claims were narrative-only — there was nothing for `ruff check src/` or `mypy --strict src/` to consult, and four real mypy errors were silently shipping.

The four mypy errors are real type-safety bugs (not cosmetic): one would have silently corrupted a credential's `Estimator` literal at v0.2.0 when `bca` was added without updating the dataclass type annotation; one was an unguarded `len()` on a possibly-None ndarray; one was an untyped helper parameter; one was an untyped dict literal that masked downstream type information.

| ID | What landed | Commit |
|---|---|---|
| **lint-1** | **`pyproject.toml` `[tool.ruff]` + `[tool.ruff.lint]`**: `line-length = 100`; `target-version = "py310"`; `select = ["E", "F", "I", "UP"]` (pycodestyle errors + pyflakes + isort + pyupgrade — the minimal set that catches common style drift in a typed scientific Python package without adding maintenance noise). New `[project.optional-dependencies] lint = ["ruff>=0.5", "mypy>=1.8"]` extras so `pip install -e ".[lint]"` installs both pinned. | *(this commit)* |
| **lint-2** | **`pyproject.toml` `[tool.mypy]` + `[[tool.mypy.overrides]]`**: `strict = true`; `python_version = "3.10"`; `files = ["src/pwm_dose_equivalence"]`. Single override for `module = "scipy.*"` with `ignore_missing_imports = true` (SciPy does not publish type stubs as of 2026). | *(this commit)* |
| **lint-3** | **4 real mypy `--strict` errors fixed.** (a) `credential.py`: `Estimator = Literal["percentile", "delong"]` → `Literal["percentile", "delong", "bca"]` (v0.2.0 added BCa to the API but never updated the dataclass type annotation; would have allowed `Credential(estimator="invalid", ...)` to type-check). (b) `api.py:107`: `sample_check: dict = {}` → `sample_check: dict[str, Any] = {}` (untyped dict). (c) `api.py`: added `assert a_pos is not None and a_neg is not None` (and same for b_pos/b_neg) at the top of the `chosen == "delong"` branch, so the subsequent `len(a_pos) + len(a_neg)` is type-safe; the mode-dispatch logic already guarantees these are non-None but mypy could not deduce it. (d) `cli.py:_format_human`: untyped `report` parameter → `report: CredentialAudit`. | *(this commit)* |
| **lint-4** | **9 ruff auto-fixes** (6 in src/, 3 in tests/) — import-sort drift (`I001`), redundant quotes on self-referencing type annotations (`UP037`), an extraneous-parentheses idiom in `bca_ci`'s acceleration computation (`UP034`). All cosmetic. | *(this commit)* |
| **lint-5** | **`FRAMEWORK_SPEC` `# noqa: E501` exception** on the one line that exceeds 100 chars. The string content is part of the SHA-256-hashed framework specification; reformatting it (including any whitespace) would change `framework_hash()` and silently invalidate every credential issued under v0.2. Verified bit-identical: `framework_hash() == sha256:b366f51c...` before and after the noqa. CONTRIBUTING.md "Code style" section updated to call out the exception explicitly as Tier-A load-bearing. | *(this commit)* |
| **lint-6** | **CONTRIBUTING.md Code style section rewritten** to name the actual `[tool.ruff]` / `[tool.mypy]` config blocks, the install command (`pip install -e ".[lint]"`), the run commands (`ruff check src/ tests/` and `mypy`), and the `FRAMEWORK_SPEC` exception. Previously the section asserted the standards exist; now it points at where they live and how to run them. | *(this commit)* |

### Verification

* `ruff check src/ tests/ examples/ scripts/` — all clean.
* `mypy` (uses `[tool.mypy] files = ["src/pwm_dose_equivalence"]`) — `Success: no issues found in 10 source files`.
* `pytest -q` — 140 / 140 passed, 100 % coverage on 437 statements (unchanged).
* `framework_hash()` returns `sha256:b366f51c11a8fbdfc7b60f1f977d42a10a8bdaa55521b43de0c428afc289fb58` (unchanged from v0.2.x).

### Schema unchanged (an eighth time)

`FRAMEWORK_SPEC` byte-for-byte identical. The `Estimator` literal widening in `credential.py` is a pure type-annotation correction — `Credential(estimator="bca", ...)` already constructed successfully at runtime via the dataclass; we just fixed the static-type lie. Every v0.2.x credential is bit-identical under the same inputs.

---

## `examples/expected_audit_output.txt` snapshot — D9 + 19 (2026-06-08)

Closes the "show me what `pwm-audit` actually prints" gap with a literal `diff`-able ground-truth file. The R3-4 reading guide §7b table tells a reviewer what each example *should* produce; today's commit captures the concatenated `pwm-audit` output across all seven examples (clean + six failures) as a single text snapshot a reviewer can compare against their own runs. Tiny, self-contained, and closes a regression-testing gap that the per-check unit tests did not.

| ID | What landed | Commit |
|---|---|---|
| **gov-snap-1** | **`pwm_dose_equivalence/examples/regenerate_expected_outputs.py`** — runs `pwm-audit` (via in-process `cli.main` for deterministic output) on every JSON file under `examples/`, in a stable `EXAMPLE_ORDER` tuple, and writes the concatenated human-readable output to `examples/expected_audit_output.txt`. Each example is delimited by `=== <relpath> (exit=<code>) ===`. New examples should be appended to the end of `EXAMPLE_ORDER` so existing rows diff cleanly. | *(this commit)* |
| **gov-snap-2** | **`pwm_dose_equivalence/examples/expected_audit_output.txt`** — 109-line snapshot file. Seven sections (one per example) carrying the full `pwm-audit` output the user would see at the shell: header (`pwm-audit: OK` / `FAIL`), hard checks (schema_valid, verdict_self_consistent), soft signals (framework_hash_known, sample_size_check_ok), full issue list, full warning list. A reviewer can confirm bit-identical behaviour with `pwm-audit examples/<each> \| diff - <(grep -A 10 '<each>' examples/expected_audit_output.txt)`. | *(this commit)* |
| **gov-snap-3** | **New test `tests/test_examples.py::test_expected_audit_output_matches_snapshot`** — re-imports `examples/regenerate_expected_outputs.py` in-process, calls its `regenerate()` function, and asserts byte-identical match against the committed snapshot. Catches four classes of regression at once: (a) CLI output formatting change; (b) audit logic change; (c) example credential edit; (d) hand-edit of the snapshot. Test count 139 → 140 at 100 % coverage on unchanged 437 statements. | *(this commit)* |
| **gov-snap-4** | **`examples/README.md` + library README** updated to mention the snapshot as a verification surface alongside the existing `regenerate.py` and `credential_schema.json`. | *(this commit)* |

### Why this lands

The audit's *unit* tests (`tests/test_credential_audit.py`, 35 tests) prove that `audit_credential` returns the right `CredentialAudit` dataclass on each tampering. The CLI's *unit* tests (`tests/test_cli.py`, 12 tests) prove the formatter renders that dataclass into the expected shape. But neither tests the *concrete strings* a reviewer will see, which is what matters for the reading guide's §7b promise. A snapshot test does. If the next contributor adjusts the human-readable formatter (e.g., renames a soft-signal label), the snapshot test fails immediately and forces an explicit "yes I meant to change the user-facing output" PR moment.

The snapshot file is also a *documentation artifact*: a regulator reading the reading guide can open this file to see what the audit actually says, without installing Python. That parallels the standalone `credential_schema.json` for the schema side of the surface.

### Schema unchanged (a seventh time)

No library code, no `FRAMEWORK_SPEC` edit. The snapshot file is captured *from* the existing library; it does not change anything the library emits.

---

## Issue templates + SECURITY.md — D9 + 19 (2026-06-08)

Backs two CONTRIBUTING.md claims that were previously narrative-only: the "issue template" sentence in §Reporting bugs, and the "private channel for credential-forgery vulnerabilities" sentence in §Security. Both now resolve to concrete files. GitHub's "New issue" UI will render the three templates; the "Security" tab will render `SECURITY.md`.

Repo-root locality: GitHub looks for `.github/ISSUE_TEMPLATE/` and `SECURITY.md` at the repository root, not in sub-folders. The library will spawn its own repo at v1.0.0; until then these files live at the parent-repo root with workstream-aware content (a "Which workstream?" picker on the bug-report and feature-request templates).

| ID | What landed | Commit |
|---|---|---|
| **gov-issue-1** | **`.github/ISSUE_TEMPLATE/bug_report.md`** — workstream picker (WS-1 / WS-2 / WS-3 / WS-4 / Other); pre-fills environment fields (OS, Python, library version, NumPy, SciPy, commit hash); reproducer + expected + actual + additional-context structure; redirects credential-audit-specific reports to the dedicated template. | *(this commit)* |
| **gov-issue-2** | **`.github/ISSUE_TEMPLATE/feature_request.md`** — same workstream picker; problem / proposed solution / sign-off tier checkbox (Tier A / Tier B / Unsure) so the proposer knows what level of review their change will need; alternatives-considered field; schema-implications field (does this require a `FRAMEWORK_SPEC` bump?); additional-context field for citations to manuscript sections / proofs. | *(this commit)* |
| **gov-issue-3** | **`.github/ISSUE_TEMPLATE/credential_audit_issue.md`** — library-specific template for "the audit returned a verdict I disagree with" reports. Asks for library version + NumPy/SciPy/Python/OS, the credential JSON (with redaction guidance that keeps audit-relevant fields intact), the full `pwm-audit --json` and human-readable output, the specific check the reporter thinks misfired (with examples), and a suspected-severity checkbox (Critical / High / Medium / Low). Critical-class reports are redirected to the SECURITY.md private channel. | *(this commit)* |
| **gov-issue-4** | **`.github/ISSUE_TEMPLATE/config.yml`** — disables blank issues (so reporters land in one of the three templates by default) and lists four contact-link shortcuts: reading guide (for "is the audit behaving correctly?"), reproduction guide (for "I can't reproduce this number"), SECURITY.md (for "I think I found a forgery surface"), CONTRIBUTING.md (for "should this be a PR or an issue?"). | *(this commit)* |
| **gov-sec-1** | **`SECURITY.md`** at the repository root — full security policy. Sections: supported versions table (WS-2 0.2.x supported; <0.2.0 unsupported; WS-1 v0.5 supported; WS-3 / WS-4 pre-release / not yet covered); what counts as a security issue (critical: credential forgery, hash collision, schema bypass, audit-state injection; non-critical: DoS, info disclosure; explicit out-of-scope list); how to report (private channel via the CITATION.cff `authors[].website`; **NO public GitHub issues for security-class problems**); 90-day default coordinated-disclosure window with 5-day acknowledgment and 15-day initial-assessment SLAs; explicit "what we will not do" enumeration (no silent landings, no retroactive FRAMEWORK_SPEC edits, no intake via social media / forums); acknowledgments placeholder. Closes the CONTRIBUTING.md §Security "see SECURITY.md" claim. | *(this commit)* |
| **gov-sec-2** | **CONTRIBUTING.md §Reporting bugs + §Security rewrites.** §Reporting bugs now names all three issue templates and explains the workstream picker + sign-off-tier checkbox + environment pre-fill mechanics; references the `config.yml`'s four contact-link shortcuts. §Security now points at `../../SECURITY.md` by relative path instead of the prior generic "report privately to the maintainers" sentence; summarises the policy's coordinated-disclosure window, advisory publication, and `FRAMEWORK_SPEC`-bump procedure. | *(this commit)* |

### What §CONTRIBUTING.md now backs (updated mapping)

| Claim in CONTRIBUTING.md | Backing artifact |
|---|---|
| "every change goes through a PR" | Manuscript §software_rigor + this file's PR workflow |
| Tier A / Tier B sign-off rule | Manuscript §software_rigor + this file's "Sign-off tiers" |
| Schema-mutation discipline (6-step checklist) | `scripts/dump_schema.py` + `examples/regenerate.py` + `tests/test_examples.py` drift checks |
| 100 % coverage discipline | `tests/` suite (139 tests at 100 % coverage on 437 statements) |
| Bug reporting via issue templates | `.github/ISSUE_TEMPLATE/{bug_report,feature_request,credential_audit_issue}.md` (this commit) |
| Security disclosure window for credential-forgery vulnerabilities | `SECURITY.md` (this commit) |
| Maintainer list (placeholder) | CONTRIBUTING.md "Maintainers" section — `TBA` until v0.3 → v0.4 manuscript revision |
| Apache 2.0 contributor agreement | `LICENSE` |

### Schema unchanged (a sixth time)

Pure governance + issue-tracking artifacts. No library code, no `FRAMEWORK_SPEC` edit, no test or schema change. The v0.2.2 library is bit-identical to its previous state. The manuscript at 24 pp is unchanged from V3-12.

---

## Manuscript §Discussion "Limitations of the present work" — D9 + 19 (2026-06-08)

Adds an explicit limitations surface to the manuscript. The existing §Discussion "Failure modes of the framework" subsubsection covered *methodological* failure modes (INDETERMINATE, point-evaluated by design, estimator failure modes, subpopulation specificity, aggregate-vs-per-patient, reproducibility caveats); a new sibling "Limitations of the present work" subsubsection covers the *empirical-validation scope* — which is the harder thing for a reviewer to read out of the existing prose. Pure manuscript work; no library code change.

| ID | What landed | Commit |
|---|---|---|
| **V3-12** | **§Discussion new subsubsection: "Limitations of the present work"** with 5 paragraphs. (1) *Empirical validation is synthetic-anchored, not yet real-cohort.* Names the current evidence (cross-modality consistency table — 6 synthetic credentials; 93 simulated coverage cells across AUC + Dice + CR) and explicitly says the per-modality Results Tables 2 / 3 / 4 carry `\todo{}` placeholders gated on Phase 1 / Phase 3a / Phase 3b data integrations. (2) *Three modalities validated; extension surface is not.* Acknowledges that no independent research group has yet computed a credential under a user-implemented modality. (3) *Credential schema does not yet pin the method bundle.* Acknowledges the v0.2 schema's bare-string `method` / `reference_method` (the documentation-vs-implementation drift L0.2.1 caught) and points at the v1.0 widening to `{name, code_hash}`. (4) *Reader-variability is a hard ceiling on attainable ε.* Spells out that the framework's verdicts are conditional on adjudication-protocol noise; a credential at ε = 0.02 on a task with inter-reader Dice variance σ ≈ 0.05 is operating below the label-noise floor. (5) *The headline WS-1 v0.5 cohort sits in the INDETERMINATE-dominated regime for the recommended AUC default.* Surfaces the V3-9 power-sim finding into the manuscript prose itself (previously only documented in `proofs/estimator.md` §4a and the WS-1 cross-reference): at AUC ≈ 0.92 and ε = 0.05, P(`PASS`) under the null is ≈ 0.40 at n = 200 / 0.94 at n = 500; downstream users should expect `INDETERMINATE` verdicts on the v0.5 cohort for genuinely equivalent methods. PDF rebuilt at 24 pp (up from 22; +2 pages from the new subsubsection). | *(this commit)* |
| **V3-12-prop** | **Page-count propagation: 22 pp → 24 pp** across status pins and current-state references. Updates: WS-2 README status pin + Subfolders paper_draft row, CONTRIBUTING.md manuscript reference, CITATION.cff preferred-citation `notes`, `reproduction_guide.md` §0 intro. Historical CHANGELOG entries that recorded prior 22-pp landings are left intact (they are accurate records of those past landings). | *(this commit)* |

### Why this lands

Three reviewer-class concerns about the present manuscript draft were detectable from internal documentation (proofs files, reading guide, R3-1 reproduction guide) but not from the manuscript prose itself:

1. **Synthetic-only validation gap.** The Results section displays one synthetic table; the per-modality Tables 2 / 3 / 4 carry `\todo{}` placeholders that any careful reviewer would notice. The §Discussion previously did not acknowledge this scoping decision.
2. **WS-1 v0.5 INDETERMINATE regime.** The R3-4 reading guide and the WS-1 README cross-reference name this regime explicitly, but the manuscript itself did not. A reviewer reading only the manuscript could conclude an `INDETERMINATE` verdict on the v0.5 cohort was a negative finding about a method, rather than a sample-size limitation of the cohort.
3. **Reader-variability ceiling.** The §software_rigor paragraph mentioned the `ε / 2` adjudication-disagreement gate but did not draw out the practical implication (`ε` cannot be tighter than the label-noise floor).

The new subsubsection surfaces all three into the manuscript prose so a reviewer does not have to chase them across companion documents.

### Schema unchanged (a fifth time)

Pure manuscript prose addition; no library code, no `FRAMEWORK_SPEC` edit, no schema or test change. The v0.2.2 library is bit-identical to its previous state.

---

## Governance artifacts: CONTRIBUTING.md + CITATION.cff — D9 + 19 (2026-06-08)

Backs the manuscript §software_rigor "Release cadence and governance" paragraph claim — *"The contribution policy is published as `CONTRIBUTING.md` in the repository."* — with code. Adds a `CITATION.cff` (CFF v1.2.0) so GitHub renders a citation button and the library can be cited as software alongside the methodological paper.

No library version bump — pure governance artifacts.

| ID | What landed | Commit |
|---|---|---|
| **L0.2.2-gov-1** | **`pwm_dose_equivalence/CONTRIBUTING.md`** — full contribution policy. Sections: dev-env setup; "what you can change without a PR" (nothing — every change goes through a PR because of the framework-hash discipline); PR workflow (fork → branch → tests → docs → CI); **two-tier sign-off rule** (Tier A = two of three maintainers for `framework_hash.py` / `credential*.py` / `estimator.py` / `sample_size.py` / `operators.py`; Tier B = one maintainer for documentation / tests / tutorials / examples / API-additive); versioning policy (MAJOR = `FRAMEWORK_SPEC` bump; MINOR = additive; PATCH = bug fix); schema-mutation discipline (6-step checklist including `scripts/dump_schema.py` re-run and `examples/regenerate.py` re-run); code style (PEP 8 / mypy strict / 100-col / no comment-restate-code / no emojis); testing (100 % coverage discipline; happy-path + failure-mode for every new public function); bug reporting (issue template with version + reproducer); security disclosure (private channel for credential-forgery vulnerabilities); maintainers (placeholder TBA until v0.3 → v0.4 manuscript revision); license intent (Apache 2.0 contributor agreement). Closes the manuscript §software_rigor claim. | *(this commit)* |
| **L0.2.2-gov-2** | **`pwm_dose_equivalence/CITATION.cff`** (CFF v1.2.0). Software-citation metadata: title, version (`0.2.2`), date-released (`2026-06-08`), license (`Apache-2.0`), repository-code URL, keywords, authors (`PWM Protocol Foundation` as organisational author until manuscript `\todo{author list}` populates). `preferred-citation` block points at the *Nature Methods* manuscript (in preparation). `identifiers` block includes the framework spec SHA-256 hash so a citer can resolve which framework version the cited library version commits to. Validated via `yaml.safe_load`. | *(this commit)* |
| **L0.2.2-gov-3** | **Manuscript §software_rigor "Release cadence and governance" paragraph rewritten** to name the actual `CONTRIBUTING.md` path, list the Tier-A and Tier-B module surfaces explicitly, mention the schema-mutation discipline and security-disclosure window, and cite `CITATION.cff` at the same path. Adds substance: the previous paragraph asserted a contribution policy existed; the new paragraph names the modules it governs and the disciplines it documents. PDF rebuilt at 22 pp; no LaTeX errors. | *(this commit)* |
| **L0.2.2-gov-4** | **Library README + WS-2 README + WS-1 cross-reference propagation.** Library `README.md` gains "Contributing" + "Citation" sections (replacing the bare "License" section). WS-2 README status pin updated to include the governance landing; D9+19 closure list gains the gov rows; Subfolders pwm_dose_equivalence row mentions CONTRIBUTING + CITATION. | *(this commit)* |

### What §software_rigor now backs (updated table)

| Claim in paragraph | Backing artifact |
|---|---|
| Documentation site (readthedocs.io URL) | Pending TestPyPI publish |
| API reference (auto-generated from docstrings) | Pending TestPyPI publish |
| Three tutorial notebooks (one per validated modality) | `pwm_dose_equivalence/notebooks/01_*.py`, `02_*.py`, `03_*.py` (R3-2) |
| Optical / fluorescence extension tutorial | `pwm_dose_equivalence/notebooks/04_optical_extending.py` (R3-3) |
| ``Credential reading guide'' for non-coder reviewers | `paper_draft/credential_reading_guide.md` v1.3 (R3-4 + audit / CLI / examples shortcuts) |
| Internal-consistency audit available from Python and shell | `pwm_dose_equivalence.audit_credential` + `pwm-audit` (L0.2.1 / L0.2.2) |
| Worked example credentials (one clean + six broken) | `pwm_dose_equivalence/examples/` (D9 + 19) |
| Standalone JSON Schema artifact | `pwm_dose_equivalence/credential_schema.json` (D9 + 19) |
| 90 % minimum line coverage | 100 % on 437 statements |
| Contribution policy in `CONTRIBUTING.md` | `pwm_dose_equivalence/CONTRIBUTING.md` (this commit) |
| Two-tier maintainer sign-off | `CONTRIBUTING.md` "Sign-off tiers" section (this commit) |
| Software citation | `pwm_dose_equivalence/CITATION.cff` (this commit) |

Every concrete claim in the §software_rigor paragraph now resolves to an artifact in this repository.

### Schema unchanged (a fourth time)

FRAMEWORK_SPEC byte-for-byte identical to v0.2.1 / v0.2.2; CITATION.cff and CONTRIBUTING.md are governance documents, not credential code.

---

## Worked examples + standalone JSON Schema artifact — D9 + 19 (2026-06-08)

Closes the "show me what each red flag actually looks like" gap. The R3-4 reading guide tells reviewers what to look for; the v0.2.1 `audit_credential` function and v0.2.2 `pwm-audit` CLI run those checks; today's commit adds **concrete example credentials** — one clean PASS and six deliberately-broken variants, one per audit signal — so a reviewer can play with the audit on actual files without having to construct credentials themselves. Adds a top-level **standalone `credential_schema.json`** so non-Python tooling (JSON-Schema-aware editors, `ajv`, registry validators) can validate credentials without importing the library.

No library version bump — these are pure artifacts + tests.

| ID | What landed | Commit |
|---|---|---|
| **L0.2.2-ex-1** | **`pwm_dose_equivalence/examples/`** directory. `regenerate.py` issues every example from seed = 42 (the clean credential via `signal_equivalence_credential` on synthetic AUC scores with realistic overlap; the failure variants by deterministic JSON perturbation of the clean credential). `valid_ct_lung_nodule.json` — clean PASS credential at the WS-1 v0.5 lung-nodule operating point (n_test = 500, ε = 0.05, DeLong, delta_mean ≈ −0.007, CI ≈ [−0.013, −0.0002]). `failures/tampered_verdict.json` — verdict flipped on a valid CI (hard issue). `failures/inverted_ci.json` — delta_ci_low > delta_ci_high (hard issue). `failures/missing_field.json` — required `verdict` field removed (hard issue, schema invalid). `failures/unknown_framework_hash.json` — framework_hash replaced with sha256:0…0 (soft warning). `failures/undersized_pass.json` — PASS verdict with sample_size_check.ok = False (soft warning). `failures/bca_headline.json` — estimator = "bca" (soft warning per `proofs/estimator.md` §4). `examples/README.md` documents each file with its expected `pwm-audit` output and exit code. | *(this commit)* |
| **L0.2.2-ex-2** | **`pwm_dose_equivalence/credential_schema.json`** — top-level standalone artifact, `json.dump`ed from `CREDENTIAL_JSON_SCHEMA` with `indent=2, ensure_ascii=False`. Non-Python validators can reference this file directly: JSON-Schema-aware editors auto-validate when `"$schema"` resolves to it; `ajv` and similar libraries can validate without installing the Python package. Regenerated from `scripts/dump_schema.py` so the artifact stays in sync with the Python-side dict. | *(this commit)* |
| **L0.2.2-ex-3** | **11 new tests in `tests/test_examples.py`** covering: the clean example audits OK with no warnings; the clean example's verdict is PASS (not INDETERMINATE — guards against the degenerate-CI bug fixed during initial development); each failure example produces its expected hard issue or soft warning by substring match; **drift detection** that regenerates every example into `tmp_path` and asserts byte-identical match against the committed JSON (catches hand-edits); the standalone `credential_schema.json` is byte-identical to `json.dumps(CREDENTIAL_JSON_SCHEMA)`; the standalone artifact is draft-07-compatible. **Library coverage now 128 → 139 tests at 100 % line coverage** (statement count unchanged at 437; new tests exercise existing code paths). | *(this commit)* |
| **L0.2.2-ex-4** | **Reading guide v1.2 → v1.3** — new §7b "Worked examples" with the per-file audit-signal table; §8 cross-references gain links to `examples/` and `credential_schema.json`. Library README gains "Examples + standalone schema" subsection. WS-2 README status pin bumped to D9 + 19 / 2026-06-08; Subfolders pwm_dose_equivalence row mentions examples + schema artifact; D9+19 closure row added. WS-1 cross-reference mentions the examples directory as the "see what a clean credential on a WS-1-like cohort looks like" entry point. | *(this commit)* |

### Why this lands

The R3-4 reading guide (D9 + 16) is *prescriptive* — it tells a reviewer what to check for. The v0.2.1 `audit_credential` (D9 + 16) and v0.2.2 `pwm-audit` CLI (D9 + 16) are *automated* — they run those checks. But neither is *concrete*: a reviewer reading the guide and the CLI docs still has to construct example credentials themselves to see what each red flag looks like. The `examples/` directory closes that gap with 7 ready-to-audit files, and the per-file table in `examples/README.md` is the cheat-sheet that maps "this kind of tampering" to "this exact audit output."

The standalone `credential_schema.json` extends the same discipline to non-Python tooling. Any future registry that wants to validate credentials at submission time can point its JSON-Schema validator at this file. No Python install required at the validating end.

### What the reviewer can now do, end-to-end

1. Read [`paper_draft/credential_reading_guide.md`](credential_reading_guide.md) §1–§8 to understand what a credential asserts and what to look for.
2. Run `pwm-audit pwm_dose_equivalence/examples/valid_ct_lung_nodule.json` to see a clean PASS audit.
3. Run `pwm-audit pwm_dose_equivalence/examples/failures/tampered_verdict.json` (and the other five failure variants) to see how each audit signal surfaces.
4. Take a credential they want to evaluate (from an author submission, a registry, a paper supplement) and run `pwm-audit their_credential.json`.
5. If the audit returns `ok=True` and they want full reproduction, follow `paper_draft/reproduction_guide.md` to re-derive every numerical claim against the published artifacts.

That is the full *reviewer surface*: definition, audit, examples, reproduction. All four anchored to artifacts in this repository at SHA-256-pinned framework version.

### Schema unchanged (a third time)

FRAMEWORK_SPEC byte-for-byte identical to v0.2.1 / v0.2.2; every credential in `examples/valid_ct_lung_nodule.json` is bit-identical to what v0.2.1 would emit from the same inputs. The standalone `credential_schema.json` is a *serialisation* of an existing constant, not a new constant. Pure additive change.

---

## Library v0.2.2 — pwm-audit CLI — D9 + 16 (2026-06-05)

Closes the "no Python required" gap for credential auditing. v0.2.1 gave a non-coder reviewer a one-call Python audit; v0.2.2 puts the same audit behind a `pwm-audit` shell command so a reviewer with the credential JSON and Python installed never has to write a Python line. Drop `pwm-audit credential.json` into a CI hook or a submission-checklist script and any internally-inconsistent credential fails the workflow.

| ID | What landed | Commit |
|---|---|---|
| **L0.2.2-1** | **`cli.py` — `pwm-audit` entry point.** New `src/pwm_dose_equivalence/cli.py` with `main(argv=None, *, stdin, stdout, stderr)` function. Argparse-based CLI: one positional argument (credential JSON path, or `-` for stdin), `--json` for machine-readable output, `--version` for library version, `--help` for usage. Human-readable summary names the hard checks, soft signals, and lists issues + warnings; JSON output is `dataclasses.asdict(CredentialAudit)`. Streams are dependency-injected so tests can capture them without monkey-patching. | *(this commit)* |
| **L0.2.2-2** | **`pyproject.toml` registers `pwm-audit`.** New `[project.scripts]` block points `pwm-audit` at `pwm_dose_equivalence.cli:main`. Version bump 0.2.1 → 0.2.2. `__init__.py` `__version__` follows. After `pip install -e .[test]`, `pwm-audit --version` prints `pwm-audit (pwm_dose_equivalence 0.2.2)`. | *(this commit)* |
| **L0.2.2-3** | **12 new CLI tests in `tests/test_cli.py`** covering: valid credential → exit 0 + "OK"; tampered verdict → exit 1; bad JSON → exit 1; nonexistent file → exit 2; stdin via `-`; `--json` output round-trips via `json.loads`; `--help` exits 0; `--version` exits 0 with library version printed; missing positional → exit 2; BCa-as-headline warning surfaces in human output; unknown framework-hash surfaces in human output and `framework_hash_known = False`; default sys.* streams when `main()` called without explicit kwargs. **Library coverage now 128/128 tests at 100 % line coverage on 437 statements** (up from 116/378 in v0.2.1; +12 tests, +59 statements). | *(this commit)* |
| **L0.2.2-4** | **Reading guide v1.1 → v1.2; manuscript + library README + WS-2 README + WS-1 cross-reference propagation.** Reading guide §7a now documents the `pwm-audit` CLI alongside the Python API with the three input modes (file / `--json` / stdin) and the exit-code contract; reading-guide footer bumped to v1.2. Manuscript §software_rigor Testing paragraph updated to v0.2.2 numbers (116/378 → 128/437; CLI exit-code contract exercised). §software_rigor Versioning policy current-version bumped to 0.2.2. §anchoring "Internal-consistency audit" paragraph gains a sentence noting `pwm-audit` is available from the shell. Library README "v0.2.2 additions" section + status line + test-count table + Versioning paragraph all bumped. WS-2 README status pin + Goals 2 + Tasks 3.1 + D9+16 closure list + Subfolders + Cross-references rows all bumped to v0.2.2. WS-1 README cross-reference entry mentions `pwm-audit` as the no-Python-call-needed alternative to the Python API. PDF rebuilt at 22 pp. | *(this commit)* |

### Schema unchanged (again)

v0.2.2 changes neither the credential wire format nor the framework specification. `FRAMEWORK_SPEC` is byte-for-byte identical to v0.2.1; every v0.2.2 credential is bit-identical to what v0.2.1 would have issued from the same inputs. The CLI is a thin shell over the v0.2.1 `audit_credential` function — same checks, same output semantics, different I/O.

### What the §software_rigor paragraph now backs

| Claim in paragraph | Backing artifact |
|---|---|
| Documentation site (readthedocs.io URL) | Pending TestPyPI publish; URL is the post-publish anchor |
| API reference (auto-generated from docstrings) | Pending TestPyPI publish; sphinx-autodoc on docstrings |
| Three tutorial notebooks (one per validated modality) | `pwm_dose_equivalence/notebooks/01_*.py`, `02_*.py`, `03_*.py` (R3-2) |
| Optical / fluorescence extension tutorial (Methods Table 7 claim) | `pwm_dose_equivalence/notebooks/04_optical_extending.py` (R3-3) |
| ``Credential reading guide'' for non-coder reviewers / regulators | `paper_draft/credential_reading_guide.md` v1.2 (R3-4 + audit / CLI shortcuts) |
| Internal-consistency audit available from Python and shell | `pwm_dose_equivalence.audit_credential` (v0.2.1) + `pwm-audit` (v0.2.2) |
| 90 % minimum line coverage | 100 % on 437 statements (well above floor) |

---

## Library v0.2.1 — audit_credential + machine-readable JSON Schema — D9 + 16 (2026-06-05)

Backs the manuscript §software_rigor "Credential reading guide" claim with **code**: anything the reading guide tells a human to check by eye, the library now offers as a one-call audit function. Also closes the latent documentation drift between the reading guide's example JSON and what the library actually emits.

| ID | What landed | Commit |
|---|---|---|
| **L0.2.1-1** | **`credential_schema.py` — `CREDENTIAL_JSON_SCHEMA`**. Explicit draft-07-compatible JSON Schema for the credential wire format, exposed as a Python dict (no `jsonschema` dependency added). Matches `SignalEquivalenceCredential.to_dict()` exactly: 3 top-level required fields; 16 credential sub-fields; verdict/estimator/task.metric enums; `framework_hash` regex `^sha256:[0-9a-f]{64}$`; `signal_ratio` in $(0, 1]$; `epsilon > 0`; `alpha \in (0, 1)$; `n_test >= 1$; `additionalProperties: false`. Arbitrary `modality` strings accepted (per R3-3 modality-extension tutorial). One `json.dumps(CREDENTIAL_JSON_SCHEMA)` away from a stand-alone validation artifact. | *(this commit)* |
| **L0.2.1-2** | **`audit.py` — `audit_credential(json_dict_or_str)`**. Internal-consistency audit returning `CredentialAudit` dataclass with `ok`, `schema_valid`, `framework_hash_known`, `verdict_self_consistent`, `sample_size_check_ok`, `issues`, `warnings`. Hard checks (block `ok`): schema validity, verdict self-consistency (`verdict_from_ci(delta_ci_low, delta_ci_high, epsilon)` must match the stored verdict), CI sanity (`delta_ci_low <= delta_mean <= delta_ci_high`). Soft checks (warnings): framework-hash recognition (mismatch = older framework version), DeLong-with-nonzero-bootstrap, BCa-as-headline opt-in flag, undersized cohort with PASS verdict. Does **not** re-run the bootstrap (that requires the original test-set scores — reproduction guide's job). | *(this commit)* |
| **L0.2.1-3** | **35 new tests in `tests/test_credential_audit.py`** covering: schema introspection; JSON-string acceptance; bad-JSON handling; missing required field detection (top-level and inner); unexpected-field rejection; bad framework_hash pattern; bad verdict/estimator/task.metric enum; signal_ratio / epsilon / alpha / n_test bound rejections; type mismatches; arbitrary-modality acceptance (R3-3 round-trip); framework-hash recognition (known vs unknown); tampered-verdict detection at all three verdict boundaries (PASS / FAIL / INDETERMINATE); inverted CI; delta_mean outside its own CI; sample_size_check propagation; undersized-PASS warning; estimator-specific soft signals (DeLong nonzero bootstrap; BCa opt-in flag); the `_check_type` unsupported-type guardrail; deep-copy non-mutation invariant. **Library coverage now 116/116 tests at 100 % line coverage on 378 statements** (up from 81/265 in v0.2.0; +35 tests, +113 statements, coverage discipline unchanged). | *(this commit)* |
| **L0.2.1-4** | **Reading guide v1.0 → v1.1 reconciliation.** The R3-4 example JSON showed `method`/`reference_method` as `{name, code_hash}` dicts, but the v0.2 schema (and the v0.2.1 library) emit them as bare strings. Fixed the example to match what the library emits, added a "schema-evolution note" explaining that v1.0 of the schema will widen these to `{name, code_hash}` for full method-bundle provenance, updated the §7 red-flag table to point at `audit_credential` where applicable, added a new §7a "audit_credential shortcut" section demonstrating the one-call audit, and added the audit + schema modules to the §8 cross-references. Reading guide footer bumped to v1.1. | *(this commit)* |
| **L0.2.1-5** | **Manuscript + WS-2 README + WS-1 README propagation.** Manuscript §software_rigor "Testing" paragraph updated: v0.1.0 / 60 tests / 230 statements → v0.2.1 / 116 tests / 378 statements (BCa + audit_credential exercised). §software_rigor "Versioning policy" current-version bumped to 0.2.1 with one-line summary of v0.2.0 + v0.2.1 additions. §anchoring "Content-addressed credential schema" gains a new paragraph "Internal-consistency audit" describing `audit_credential` as the bootstrap-free preflight check for regulators / readers without raw-DICOM access. WS-2 README D9+16 closure list gains the L0.2.1-N rows. WS-1 README cross-reference entry mentions `audit_credential` as the no-Python-required way to check a credential issued on the v0.5 cohort. PDF rebuilt at 22 pp; no LaTeX errors. | *(this commit)* |

### Why this lands now

The R3-4 reading guide (D9 + 16) tells a non-coder reviewer what to *look for*: schema validity, verdict-vs-CI consistency, framework-hash recognition, sample-size-check coherence, red-flag patterns. Without `audit_credential` and the explicit schema, those checks are eye-only — the reviewer has to walk the JSON manually and trust their own arithmetic. With L0.2.1 they get the same checks in one call. The reading guide's §7a now demonstrates this directly; the manuscript §anchoring "Internal-consistency audit" paragraph anchors the same claim in the framework discussion.

Net effect: the manuscript §software_rigor "Documentation and tutorial notebooks" claim is now backed by **code**, not just documentation. A reviewer reading a credential JSON can either (a) walk through `credential_reading_guide.md` field-by-field, or (b) call `audit_credential(d)` and read the `CredentialAudit` report — both arrive at the same conclusion.

### Schema unchanged

`schema_version` remains `pwm-signal-equivalence/v0.2`; `FRAMEWORK_SPEC` unchanged; the credential wire format is unchanged. v0.2.1 *describes* the existing format more rigorously (via `CREDENTIAL_JSON_SCHEMA`) and adds a *verifier* for it (via `audit_credential`); it does not change what a credential looks like.

---

## v0.3 reviewer-reproduction surface (continued) — D9 + 16 (2026-06-05)

Closes the *non-coder reviewer* gap in the §software_rigor "Documentation and tutorial notebooks" paragraph. The previous v0.3 reproduction-surface entry covered the *code-savvy* reviewer (R3-1 reproduction guide + R3-2 / R3-3 tutorials); today's entry covers the *non-coder* reviewer (R3-4 reading guide), and adds a small manuscript text edit pointing readers at both companion documents.

| ID | What landed | Commit |
|---|---|---|
| **R3-4** | **`paper_draft/credential_reading_guide.md`** — 8-section field-by-field walk through a published credential JSON, written for reviewers / regulators / clinicians who need to *interpret* a credential without re-running the bootstrap themselves. Sections: (1) what a credential is + what it is not; (2) JSON field table (14 fields); (3) verdict semantics (PASS / FAIL / INDETERMINATE); (4) sample-size sanity check (with the WS-1 v0.5 INDETERMINATE-dominated regime called out by name at n ≈ 208 / AUC ≈ 0.92, $P(\text{PASS}) \approx 0.40$); (5) framework-hash guarantees + non-guarantees (3 + 3); (6) common reviewer / regulator questions (7); (7) red-flag checklist (9 entries); (8) cross-references. Audience-disjoint from `reproduction_guide.md`: the reproduction guide answers "how do I re-derive the numbers?"; the reading guide answers "how do I read a credential someone else published?" `reproduction_guide.md` §10a added pointing at the reading guide; library `README.md` "Tutorial notebooks" section updated to list *both* reviewer-facing companions; manuscript §software_rigor "Documentation and tutorial notebooks" paragraph updated to name both files by path. **Closes the manuscript §software_rigor "Credential reading guide" claim**, leaving zero unbacked claims in that paragraph. | *(this commit)* |

The §software_rigor "Documentation and tutorial notebooks" paragraph now has every concrete claim backed by an artifact:

| Claim in paragraph | Backing artifact |
|---|---|
| Documentation site (readthedocs.io URL) | Pending TestPyPI publish; URL is the post-publish anchor |
| API reference (auto-generated from docstrings) | Pending TestPyPI publish; sphinx-autodoc on docstrings |
| Three tutorial notebooks (one per validated modality) | `pwm_dose_equivalence/notebooks/01_*.py`, `02_*.py`, `03_*.py` (R3-2) |
| Optical / fluorescence extension tutorial (Methods Table 7 claim) | `pwm_dose_equivalence/notebooks/04_optical_extending.py` (R3-3) |
| ``Credential reading guide'' for non-coder reviewers / regulators | `paper_draft/credential_reading_guide.md` (R3-4, today) |
| CI testing of the notebooks (runnable as the API evolves) | Pending TestPyPI publish; CI matrix already defined for the test suite |

The remaining "pending TestPyPI publish" items are infrastructure work outside what the local repository can certify on its own and ship with the v1.0.0 release alongside paper acceptance.

---

## v0.3 reviewer-reproduction surface — D9 + 16 (2026-06-05)

Closes two complementary items that together complete the *reviewer-can-reproduce-every-number* discipline: the last v0.2.0 library follow-up (integration tests), and a new top-level reviewer-facing document (`paper_draft/reproduction_guide.md`). No manuscript text change; both items strengthen what reviewers see *around* the manuscript without changing the manuscript prose.

| ID | What landed | Commit |
|---|---|---|
| **L0.2-4** | **Integration tests for the library.** New `pwm_dose_equivalence/tests/test_integration.py` — 10 end-to-end tests exercising the full credential-issuance pipeline through the public API: CT AUC / MRI Dice / PET CR per-modality credentials; cross-modality consistency reproduced through the production library (not the prototype); JSON round-trip + framework-hash audit; seeded bit-reproducibility; T_r operator integration; verdict transitions (boundary INDETERMINATE; FAIL at $\Delta_{\text{true}} > \varepsilon$ + $n = 500$). Library README updated: 71/71 → **81/81 tests** at 100 % line coverage (265/265 statements; unchanged — the integration tests exercise existing code paths). | `a5b5163` |
| **R3-1** | **`paper_draft/reproduction_guide.md`** — 12-section reviewer walkthrough mapping every numerical claim in the v0.3 manuscript to its repo anchor + the command that re-derives it. Sections: install + pytest; cross-modality consistency table (Results §); AUC coverage 27-cell (§2); AUC power 24-cell (§4a); Dice + CR (§§4b / 4c); production-library reproduction; framework hash; sample-size formulas (S1) / (S3) / (S4); BCa / small-n / bound_M; quickstart-on-your-own-method; **per-claim anchor table (16 rows)** mapping every concrete number in the manuscript to its proofs document + reproduction command; what's intentionally not covered (data-blocked / submission-time / literature). | `558d112` |
| **R3-2** | **Three tutorial notebooks** in `pwm_dose_equivalence/notebooks/`, one per validated modality: `01_ct_lung_nodule_auc.py` (CT AUC, DeLong auto-selection, ε = 0.05, demonstrates the §4a cohort-sizing implication table); `02_mri_meniscus_dice.py` (MRI Dice, percentile + `sigma_delta_hint` triggering (S1) / (S4) pre-flight, demonstrates the Dice-vs-AUC cohort contrast and `estimator="bca"` opt-in); `03_pet_phantom_cr.py` (PET CR, activity-reduction as canonical `T_r`, n = 30 recommended cohort, demonstrates the small-$n$ warning by re-running at n = 6). Format: `.py` files with `#%%` cell markers — run as both Python scripts and Jupyter notebooks (no `.ipynb` binary diffs). Closes the *"three tutorial notebooks (one per validated modality)"* claim in §software_rigor "Documentation and tutorial notebooks". `notebooks/README.md` + library README "Tutorial notebooks" section added. | `db1d31b` |
| **R3-3** | **Extending-to-new-modality tutorial** — `notebooks/04_optical_extending.py` shows a user how to define their own `T_r` operator (worked example: Optical / fluorescence imaging at 25 % exposure, per Methods Table 1) and plug it through the unchanged `signal_equivalence_credential` API. **Closes the manuscript Methods Table 7 "Optical / fluorescence: specified; not validated; user-implementable" claim** with a concrete worked example. Demonstrates that (a) `Tr_optical` is mathematically identical to `Tr_ct` (Poisson-thinning) but scientifically distinct via Π's acquisition-protocol metadata (fluorophore / wavelength / specimen class); (b) `modality="Optical"` is just a string tag — the library accepts arbitrary modalities; (c) cross-modality consistency demos work for free with user-implemented operators. Tutorial runs cleanly: PASS verdict at n = 80 specimens. `notebooks/README.md` + library README updated to enumerate four tutorials. Test count and coverage unchanged (uses existing code paths via `Tr_ct` re-export). | `00880ed` |

### `R-N` ID convention

Introduced today for *reviewer-facing reproduction artifacts* — distinct from manuscript-side `V3-N` items and library `L0.2-N` items. Future reviewer-facing artifacts (e.g.\ a tutorial notebook, a "How to integrate a new modality" walkthrough) would use `R3-2`, `R3-3`, etc. Until the manuscript itself bumps, the prefix stays at `R3`.

### What this completes

The repository now answers five orthogonal reviewer + user questions:

1. *What changed and why?* — `CHANGELOG.md` (this file), one row per substantive edit / artifact.
2. *Where does each claim live?* — `reproduction_guide.md` §10 per-claim anchor table (R3-1).
3. *How do I re-derive the numbers?* — `reproduction_guide.md` §§1–9 commands; library tests at 100 % coverage.
4. *How do I use the library on my own method?* — three modality-specific tutorial notebooks (R3-2) in `pwm_dose_equivalence/notebooks/`.
5. *How do I extend the framework to a new modality?* — `04_optical_extending.py` (R3-3) shows the user-implementable path with a worked Optical / fluorescence example.

A reviewer can now sit down with the v0.3 manuscript + the repo and verify every numerical claim *without trusting the authors* on any of them. A new user (PI / postdoc / engineer) can follow the modality-matching tutorial end-to-end without reading the manuscript at all. A researcher working in a modality the framework does not yet validate (Optical / OCT / Ultrasound / etc.) can follow `04_optical_extending.py` and have a working credential pipeline in their own modality without touching the library source. This was the discipline V3-2 / V3-5 had reached for via inline cross-links to `proofs/estimator.md`; today's reproduction guide (R3-1) makes the *verification* path explicit; tutorials R3-2 make the *usage* path explicit; and R3-3 makes the *extension* path explicit.

### Schema / manuscript unchanged

Credential JSON `schema_version` stays at `pwm-signal-equivalence/v0.2`. The manuscript text is unchanged at v0.3 (22 pp). The reproduction guide is a supplementary document; a future v0.4 manuscript revision could reference it directly from §Code availability, but for v0.3 it lives alongside the manuscript as a peer artifact in `paper_draft/`.

### `open_questions.md` status after R3-1 + L0.2-4

No theory-side movement. All BLOCK items remain done. The remaining open items are the same external-action-blocked ones: §1 literature depth-pass; §5 monotonicity empirical check (gated on Phase 1 pilot).

### Today's commits

| Commit | Touched |
|---|---|
| `a5b5163` | `pwm_dose_equivalence/tests/test_integration.py` (new); library README test/coverage line bumped to 81/81 |
| `558d112` | `paper_draft/reproduction_guide.md` (new) |
| `db1d31b` | `pwm_dose_equivalence/notebooks/` (new dir + 3 tutorials + README); library README "Tutorial notebooks" section added |
| `00880ed` | `pwm_dose_equivalence/notebooks/04_optical_extending.py` (new); `notebooks/README.md` + library README extended to four tutorials |

### Downstream-doc propagation

The L0.2-4 + R3-1 landings propagated to both READMEs to keep cross-document references in sync:

* **WS-2 README — pass 1 (L0.2-4 + R3-1)** (`4d80ad2` + `f904a8d`). Status pin date bumped D9 + 15 → D9 + 16; library `v0.1.0 alpha / 60/60` → `v0.2.0 alpha / 81/81 (incl. 10 integration tests)` across the status pin, Goal 2, Phase 3.1 status, Subfolders `paper_draft/` row, Subfolders `pwm_dose_equivalence/` row, and Cross-references library bullet. New "Landed at D9 + 15 late (Library v0.2.0)" sub-block + "Landed at D9 + 16 (reviewer-reproduction surface)" sub-block in the "Done when" intermediate-progress section with L0.2-1 .. L0.2-4 + R3-1 checked. Subfolders `paper_draft/` row description extended to mention the reproduction guide. Timeline preface five-pass enumeration extended (D9 + 12 / 13 / 14 / 15 / 16).
* **WS-2 README — pass 2 (R3-2 tutorials)** (`aa51f6e` + `ccf6b2e`). Five sections extended for the three validated-modality tutorials: status pin appended "+ three tutorial notebooks"; "Reviewer side" → "Reviewer + user surface"; Done-when D9 + 16 sub-block gained an R3-2 row; Goal 2 + Subfolders pwm_dose_equivalence row + Cross-references library bullet all enumerated the three new tutorials and named them by file.
* **WS-2 README — pass 3 (R3-3 modality-extension)** (`362fa9b`). Same five surfaces extended again: three tutorials → four tutorials; "Reviewer + user" → "Reviewer + user + extension surface"; Done-when D9 + 16 sub-block gained an R3-3 row naming the Methods Table 7 "user-implementable" claim closure; Goal 2 + Subfolders + Cross-references all named the Optical extension tutorial alongside the three validated ones.
* **WS-1 README — pass 1** (`18bcbfe`). Four "as of today" date bumps (status pin + Timeline preface + "Done when" preface + section heading) D9 + 15 → D9 + 16. **Cross-references → WS-2 entry "Downstream-user note"** updated: library v0.1.0 → v0.2.0; tests 60/60 → 81/81; estimator list extended (percentile + DeLong + BCa); sample-size pre-flight gains `bound_M`; small-$n$ warning enumerated. **NEW pointer** to `paper_draft/reproduction_guide.md` for downstream WS-1 researchers who want to verify any specific WS-2 numerical claim against their experimental setup using the 16-row per-claim anchor table as the entry point.
* **WS-1 README — pass 2** (`3bf1647`). Extended the same downstream-user note with a follow-on pointer to the R3-2 tutorial notebooks. Frames the two pointers as complementary for the WS-1 audience: `reproduction_guide.md` is for *reviewers verifying* WS-2 claims against the WS-1 cohort; `pwm_dose_equivalence/notebooks/` is for *downstream researchers learning* to use the library on their own method against WS-1 data. Names `01_ct_lung_nodule_auc.py` explicitly as the natural entry point for the WS-1 CT lung-nodule use case.
* **WS-1 README — pass 3** (`5ce213c`). Extended the same tutorials pointer sentence again to surface the R3-3 modality-extension template. Now distinguishes **three downstream audiences** with their entry-point tutorial: CT researchers → `01_ct_lung_nodule_auc.py`; MRI / PET reference → `02` / `03`; researchers in unvalidated modalities (Optical / OCT / Ultrasound / …) → `04_optical_extending.py` (R3-3) as the user-implementable template. Honestly extends WS-1's reach (a reader who works in OCT now has a starting point) without overstating WS-1's own CT-only scope.

The 16-row per-claim anchor table in the reproduction guide AND the three modality-matching tutorials AND the modality-extension template are now all referenced directly from the WS-1 README — completing the *reviewer + user + extension* audit-trail discipline that the v0.3 evidence-completion + Library v0.2.0 sections began.

### Cumulative reviewer + user reproduction surface

A reviewer landing on either README today sees:

| Surface | Where | Audience |
|---|---|---|
| Manuscript claims | `paper_draft/manuscript.tex` v0.3 | reviewers |
| What changed and why | `paper_draft/CHANGELOG.md` (this file) | reviewers + maintainers |
| Where each claim lives + how to re-derive | `paper_draft/reproduction_guide.md` (R3-1) | reviewers |
| How to use the library end-to-end per modality | `pwm_dose_equivalence/notebooks/` (R3-2, three validated-modality tutorials) | new users (PI / postdoc / engineer) |
| How to extend the framework to a new modality | `pwm_dose_equivalence/notebooks/04_optical_extending.py` (R3-3) | researchers in unvalidated modalities (Optical / OCT / Ultrasound / …) |
| Library implementation + 81 tests at 100 % | `pwm_dose_equivalence/` v0.2.0 alpha | downstream users + reviewers |
| Cross-workstream cohort-sizing implications | WS-1 README Target specs row + WS-2 cross-reference | downstream WS-1 users |

The discipline is end-to-end: every cited number, every cross-reference, every library feature has an identified anchor and a documented path to **verification** (R3-1), **usage on validated modalities** (R3-2), or **extension to a user-implementable modality** (R3-3).

---

## Library v0.2.0 — D9 + 15 (2026-06-04, late)

Closes the three v0.2.0 library items the *v0.3 evidence-completion* section recorded as follow-ups: BCa estimator exposure (deferred from v0.1.0 per the v0.3 estimator-default decision); small-$n$ anti-conservativeness warning surfaced by V3-11; `bound_M` argument for unbounded metrics. **No manuscript text change**: the §software_rigor and §Code availability paragraphs were filled with v0.1.0 numbers via V3-3 / V3-8 and intentionally stay at v0.1.0 (the journal-acceptance re-pin per V3-8 will move them forward when the time comes). The credential JSON schema is unchanged at `pwm-signal-equivalence/v0.2`.

| ID | What landed | Commit |
|---|---|---|
| **L0.2-1** | **BCa estimator exposure.** New `bca_ci()` in `pwm_dose_equivalence/src/pwm_dose_equivalence/estimator.py` implementing generalised Efron 1987 bias-corrected accelerated bootstrap on per-patient deltas (not AUC-specific). Vectorised fast-jackknife (`(sum - deltas[i]) / (n - 1)`). Degenerate-input fallback to percentile when `z0` is undefined. Wired into the API as `estimator="bca"`; opt-in only per the v0.3 §4 decision (does not robustly outperform percentile under the null in the 27-cell coverage sim). | `8e6dbdb` |
| **L0.2-2** | **Small-$n$ anti-conservativeness warning.** New `_SMALL_N_THRESHOLD = 30` constant in `api.py`; `UserWarning` fires for any percentile or BCa call with $n < 30$, citing the V3-11 finding in `theory/proofs/estimator.md` §4c (coverage 0.82–0.93 in that regime). Independent of the existing (S1) sample-size warning — both can fire simultaneously. | `8e6dbdb` |
| **L0.2-3** | **`bound_M` argument for unbounded metrics.** New `bound_M` argument on `signal_equivalence_credential()` (default 1.0); propagates to `required_n_bernstein`. Allows users to specify $M$ for MAE / MSE on raw HU / unnormalised intensities. The credential's `sample_size_check` field records `bound_M` alongside `n_required_clt` and `n_required_bernstein`. Larger `bound_M` strictly grows the Bernstein requirement; the CLT bound is unaffected. | `8e6dbdb` |

### Test + coverage growth

| Metric | v0.1.0 | v0.2.0 |
|---:|---:|---:|
| Tests | 60 | **71** |
| Statements covered | 230 | **265** |
| Line coverage | 100 % | **100 %** |

11 new tests in `tests/test_v020_features.py` cover `bca_ci` direct (4 — including degenerate fallback + empty-array rejection), API `estimator="bca"` (2 — PASS verdict + AUC-mode rejection), small-$n$ warning (3 — fires below threshold, silent above, fires for BCa too), and `bound_M` (2 — default 1.0, larger M strictly grows the Bernstein n while CLT n unchanged).

### Manuscript impact

* §software_rigor "Testing" paragraph still cites *60 unit tests / 100 % line coverage on 230 statements* — intentionally **not** updated to v0.2.0 numbers. The V3-3 framing froze those values at the v0.3 draft point; per V3-8 the library version (and these numbers) will be re-pinned at the journal-acceptance release. A future v0.4 manuscript revision will move them to 71 / 265.
* §Code availability still cites `pwm_dose_equivalence==0.1.0` for the same reason.
* The §methods-estimator "Estimator defaults" paragraph already mentions BCa as an opt-in alternative via the v0.3 V3-2 rewrite — V3-2's prose remains correct under v0.2.0 (BCa is now actually exposed as it claimed).

### `open_questions.md` status after v0.2.0

No theory-side movement. All BLOCK items remain done. The §3 cross-metric synthesis from V3-10 / V3-11 is now backed by an actual library implementation of the BCa option that the §4 decision discusses, closing the "claimed but not exposed" gap that v0.1.0 had carried.

### v0.2.0 → v1.0.0 remaining items

Per the library README: ~~integration tests~~ (done D9 + 16 — see *v0.3 reviewer-reproduction surface* section above), macOS + Windows CI runners (Linux only at v0.2.0), and the manuscript-acceptance fixes journal review surfaces. None of these is methodologically blocking; they are pre-release infrastructure that lands alongside the *Nature Methods* acceptance per the V3-3 / V3-8 framing.

---

## v0.3 evidence-completion — D9 + 15 (2026-06-04)

Path-1 (Nature Methods) non-AUC blocker closed. The v0.3 manuscript advertised three worked-example metrics — AUC (CT lung-nodule), Dice (MRI knee-meniscus segmentation), CR (PET NEMA NU-2 IQ phantom contrast-recovery) — but the empirical estimator-backing only covered AUC. Two new simulations land today closing the per-modality trio. **No manuscript text changes**: the V3-2 / V3-5 inline cross-link to `proofs/estimator.md` (added during v0.3 main pass) routes both new findings into the §methods-estimator paragraph automatically.

| ID | What landed | Commit |
|---|---|---|
| **V3-10** | **Dice (MRI segmentation) coverage + power simulation.** New [`experiments/estimator_coverage/dice_sim.py`](../experiments/estimator_coverage/dice_sim.py) — 18 cells under the (S1) general-metric Normal generative model at the v0.3 non-AUC default `ε = 0.02`. Closes the "AUC only" caveat in `proofs/estimator.md` §5.1 that the v0.2 of that document had carried. Headline contrast with AUC: at realistic clinical $\sigma_\Delta = 0.05$ and $n = 200$, P(`PASS`) under the null = 1.000 for Dice — substantively different from the same $n$ at AUC = 0.92 where P(`PASS`) = 0.40 (V3-9 §4a). The difference is variance-relative-to-margin: Dice $\sigma_\Delta = 0.05$ relative to $\varepsilon = 0.02$ is much narrower than AUC placement-difference $s = 0.15$ relative to $\varepsilon = 0.05$. `proofs/estimator.md` bumped v0.2 → v0.3 with new §4b. | `d8c45e1` |
| **V3-11** | **CR (PET phantom) coverage + power simulation — per-modality trio CLOSED.** New [`experiments/estimator_coverage/cr_sim.py`](../experiments/estimator_coverage/cr_sim.py) — 24 cells at smaller cohort sizes (n ∈ {6, 12, 30, 60}) reflecting per-credential phantom-acquisition counts (6 spheres × 1–10 acquisitions). **New methodological finding the larger-cohort AUC and Dice sims could not surface**: percentile bootstrap is anti-conservative at very small $n$ — coverage 0.82–0.88 at n=6; 0.88–0.93 at n=12. **At $n \geq 30$ coverage returns to nominal** (0.93–0.96). Practical PET recommendation: $n \geq 30$ (≥ 5 NEMA NU-2 IQ phantom acquisitions). `proofs/estimator.md` bumped v0.3 → v0.4 with new §4c; §5.1 caveat closed (per-modality trio now AUC + Dice + CR — only unbounded MAE / MSE pending). **New v0.2.0 library item recorded**: flag credentials issued at $n < 30$ for non-AUC metrics with an explicit small-sample warning citing §4c. | `1911b68` |

### Cross-metric synthesis

The four sims now back the framework's estimator across **93 cells × four metric families** (AUC coverage 27 + AUC power 24 + Dice 18 + CR 24). The cross-metric conclusion: **the framework's coverage and power properties hold across all three worked-example metric families at $n \geq 30$**; below n = 30 the percentile bootstrap is anti-conservative (CR finding); at n ≥ 100 (AUC and Dice cells) calibration is nominal across all tested cells. The estimator-default decision recorded in §4 of `proofs/estimator.md` (percentile general; DeLong-for-AUC auto-selected; BCa opt-in) survives non-AUC extension across both bounded metric families.

### `open_questions.md` status after V3-10 / V3-11

All BLOCK items remain done. The §3 BLOCK now has *four* sub-deliverables closed (under-null AUC; non-null AUC power; Dice coverage + power; CR coverage + power) where the original §3 scoping had only two (under-null + non-null AUC). The next §3 extension would be unbounded metrics (MAE / MSE) where the (S4) Bernstein bound applies with user-specified $M$ per Supplementary S1; this is a v0.2.0 library item, not a v0.3 manuscript item.

### Schema (unchanged at v0.3-evidence-completion)

Credential JSON `schema_version` remains `pwm-signal-equivalence/v0.2`. The library API is unchanged. The new sims exercise the same paired-bootstrap codepath the library v0.1.0 alpha already implements.

### Manuscript text unchanged

The §methods-estimator "Estimator defaults" paragraph already cites `proofs/estimator.md` inline (added during the v0.3 main pass via V3-2 / V3-5). Both V3-10 (§4b) and V3-11 (§4c) findings are routed into the manuscript through that pre-existing link — no manuscript edit required. A future v0.4 manuscript revision could pull explicit numbers from §4b / §4c into the prose; for v0.3 the inline cross-link is sufficient.

---

## v0.3 polish — D9 + 14 (2026-06-03, late)

Four post-v0.3 items closing remaining `\todo{}` placeholders, an open theory section, and the second deliverable of `open_questions.md` §3 (power simulation). The manuscript text grows by ~3 pp (the Bernstein supplementary); the credential schema is unchanged. V3-6 / V3-7 / V3-8 landed in `1ca1a15`; the power sim (V3-9) landed in `c25b81f`.

| ID | What landed | Commit |
|---|---|---|
| **V3-6** | **Supplementary Section S1: Bernstein finite-sample correction.** Self-contained derivation of (S4) appended at the end of `manuscript.tex` inside a `\appendix` block: setup with bounded `|Δ_k - μ| ≤ M`, Bernstein's inequality (cite Boucheron–Lugosi–Massart 2013), substitution at $t = \varepsilon$, the boxed (S4) bound, numerical comparison to (S1), library-behaviour note (both bounds reported in `sample_size_check`), practical guidance ((S1) for n ≥ 100; (S4) for n < 100), two caveats (unbounded metrics → Hoeffding; paired AUC → DeLong instead of (S4)). The §methods-estimator `\todo{supp section}` placeholder is replaced with `\ref{supp:bernstein}`. | `1ca1a15` |
| **V3-7** | **`theory/proofs/monotonicity.md` v0.1** — closes the theory side of `open_questions.md` §5 (SHARPEN). Frames naive monotonicity as false in general; defines the class $\mathcal{M}_{[r_{\min}, 1]}$ of methods trained over a signal-ratio distribution covering the range; states the conditional-monotonicity conjecture precisely; sketches two candidate counterexamples (catastrophic-overfit-to-low-end; equivariance-breaking architecture); scopes the empirical-check plan against Phase 1 pilot data; recommends a v0.4 manuscript design-recommendation paragraph supported by 3 baselines. Empirical validation gated on D9 + 90 (the Phase 1 pilot's 5-tuples). | `1ca1a15` |
| **V3-8** | **Pinned library version placeholder filled.** §Code availability: `\todo{pinned-version-at-submission}` → "`pwm_dose_equivalence==0.1.0` (released against credential schema `pwm-signal-equivalence/v0.2`; will be pinned to the journal-acceptance release at submission)". | `1ca1a15` |
| **V3-9** | **Non-null power simulation — closes `open_questions.md` §3 second deliverable.** The D9 + 13 coverage sim verified the CI's containment of true Δ under the null; this sim verifies the *verdict distribution* under controlled non-null shifts ($\Delta_{\text{AUC,true}} \in \{0, \varepsilon, 2\varepsilon\}$). New `experiments/estimator_coverage/power_sim.py` + frozen `power_results.json` (24 cells; ~25 min wall time; seed = 42). `theory/proofs/estimator.md` bumped from v0.1 to v0.2 with a new §4a (verdict-distribution table + 5 readings: framework conservatively INDET-s rather than over-commits; P(`PASS`) under null hits nominal at AUC = 0.92, n = 500; power at $2\varepsilon$ ≥ 0.90 across the typical operating range; INDETERMINATE dominates at the boundary; percentile and DeLong agree on power to within 1.5 pp). §5 caveats trimmed (the v0.1 "null only" caveat now superseded). **Cohort-sizing implication recorded**: the WS-1 v0.5 cohort ($n \approx 208$) is *exactly* in the regime where INDETERMINATE-but-truly-equivalent is the modal outcome; absence of a `PASS` verdict is not evidence of non-equivalence, only of insufficient n. No manuscript text change (the §methods-estimator "Estimator defaults" paragraph already cites `proofs/estimator.md` inline via V3-2); the manuscript inherits the §4a finding through that link. | `c25b81f` |

PDF rebuilds at **22 pages** (was 19 before V3-6; +3 pp is Supplementary S1). 0 LaTeX errors, 0 undefined references.

### Remaining `\todo` placeholders in the manuscript (intentional, submission-gated)

- §Discussion / point-evaluated-by-design list: `\todo{supp v2}` — task-bundle extension supplementary, deferred to v2 of the framework.
- §Data availability: `\todo{supp tab}` — test-split manifest hash table, gated on real Phase 1 / Phase 3 cohorts.
- §Author contributions: `\todo{Fill at submission per CRediT taxonomy: ...}`.
- §Competing interests: `\todo{Declare at submission. ...}`.
- §Acknowledgments: `\todo{Fill at submission. ...}`.

The remaining placeholders are all submission-time fields; no further v0.3-level work is feasible without external action (real cohort, author confirmation, journal upload, PyPI auth).

### `open_questions.md` re-priority after V3-9

V3-9 closes the second deliverable of §3 (non-null power), leaving §1 (literature depth-pass — external) and §5 (monotonicity *empirical* check — gated on Phase 1 pilot) as the only open theory items. All BLOCK items are now fully done. The recommendation in `proofs/estimator.md` §6 ("estimator-default decision survives under both null coverage and non-null power") is the new theory-side anchor for the v0.3 manuscript's §methods-estimator "Estimator defaults" paragraph; the cohort-sizing implication is the new theory-side anchor for the §sample-size paragraph.

### Downstream-doc propagation

The V3-9 cohort-sizing finding was propagated downstream across the WS-1 dataset README in two passes:

* **Pass 1 — WS-1 Cross-references → WS-2 entry sharpening** (commit `d0569f3`). The prior "(S3) formula is met → cohort is comfortably sized" framing was sharpened with the empirical verdict-distribution evidence. The new note tells downstream WS-1 users to **expect `INDETERMINATE` verdicts on the v0.5 cohort even for genuinely equivalent methods** at AUC ≈ 0.92 / n ≈ 200, and that **absence of `PASS` is not evidence of non-equivalence** — only of insufficient n (P(`PASS`) under the null is ≈ 0.40 at n = 200, lifting to ≈ 0.94 at n = 500).
* **Pass 2 — WS-1 Target specs new row** (commit `7817fad`). A "Credential-issuance regime (per V3-9 power sim, D9 + 14)" row was added to the v0.5 / v1.0 Target specs table, immediately after the patient-counts row. This puts the formula-side fact + empirical-side fact + operational message in the table a downstream researcher *actually consults when sizing an experiment*. v0.5 column carries the INDETERMINATE-dominated message above; v1.0 column carries the complementary "n ≥ 500 lifts into the P(`PASS`) ≈ 0.94 regime; supports tighter ε = 0.02 at the upper cohort range" message.

The (S3) sample-size formula and the V3-9 power simulation are consistent — they just answer different questions (formula: minimum n for the CI half-width to be ≤ ε in expectation; power sim: empirical verdict-distribution behaviour at the threshold n). Both passes now surface in the WS-1 README — Pass 1 in the Cross-references prose; Pass 2 in the Target specs table.

The WS-2 README was correspondingly refreshed at D9 + 14 across the status pin, Phase 2.2 status, Timeline, Subfolders proofs/ + experiments/ rows, Cross-references, and the "Done when" intermediate D9 + 14 sub-block (commits `b301b04`, `964e8c0`), plus a residual 19 pp → 22 pp page-count cleanup (commit `d253e4e`).

**Bidirectional-flow framing across both READMEs.** With V3-9 making the cross-workstream flow explicitly bidirectional (WS-1 → WS-2 contributed the annotation QA protocol; WS-2 → WS-1 now contributes the cohort-sizing implication), the sibling-workstream cross-references on both sides were updated to name the relationship symmetrically: WS-2 README's WS-1 entry (commit `88c963a`) and WS-1 README's WS-2 entry (commit `5c4d028`). Both now lead with "The cross-workstream flow is bidirectional (as of D9 + 14)" and enumerate the same two propagation commits (`d0569f3`, `7817fad`).

The V3-9 finding now appears in 7 places with consistent numbers: manuscript `proofs/estimator.md` §4a (canonical); `experiments/estimator_coverage/` (the simulation); WS-2 README; WS-2 CHANGELOG (this file); WS-1 README Cross-references; WS-1 README Target specs; the WS-2 §methods-estimator "Estimator defaults" paragraph (via the V3-2 / V3-5 inline cross-link to `proofs/estimator.md`).

---

## v0.3 — 2026-06-03 (D9 + 14)

v0.3 applies the five manuscript edits triggered by the D9 + 13 / D9 + 14 theory-and-library pass. The supporting artifacts (proofs writeups + library) had already landed; v0.3 is the manuscript-side propagation of their consequences. PDF rebuilds at 19 pages (same length as v0.2 — the new prose displaces the corrected hedges rather than adding to them).

### Theory landings

| Artifact | `open_questions.md` ref | Commit | What landed |
|---|---|---|---|
| [`theory/proofs/mri_mask.md`](../theory/proofs/mri_mask.md) | §7 (BLOCK MRI) | `526baaa` | Records option (c): `mask_family` rides inside Π as acquisition-protocol metadata, preserving the 5-tuple shape. Manuscript-side already adopted via A3 / clarification C5; this is the theory-side anchor. |
| [`theory/proofs/pet_reduction.md`](../theory/proofs/pet_reduction.md) | §8 (SHARPEN) | `526baaa` | Canonicalises activity-reduction as the v1 PET `T_r`; scan-time reduction is documented as v2. Surfaces a footnote item for Table 1 row 3. |
| [`theory/proofs/composition.md`](../theory/proofs/composition.md) | §4 (DEFER) | `526baaa` | Negative-result note: no clean composition law; framework is point-evaluated by design. Theory-side mirror of manuscript Discussion §"Point-evaluated by design". |
| [`theory/proofs/estimator.md`](../theory/proofs/estimator.md) | §3 (BLOCK) | `44a58f0` | Theorem statement (cites Efron 1979, Bickel–Freedman 1981); 27-cell empirical coverage table; estimator-default decision: **percentile** for general use, **DeLong** auto-selected for AUC tasks (~300× faster with mild conservativeness), **BCa opt-in only** (does not robustly beat percentile under the null). The v0.1 manuscript hedge "library defaults to BCa for AUC > 0.95" is **withdrawn**. |
| [`theory/proofs/sample_size.md`](../theory/proofs/sample_size.md) | §2 (BLOCK) | `e3c1ee2` | (S1) general CLT formula + (S3) paired-AUC DeLong specialisation + (S4) Bernstein finite-sample correction; numerical tables at canonical operating points; empirical validation against the §3 simulation. **Surfaces a v0.3 manuscript correction** — see *Triggered manuscript edits* below. |
| [`experiments/estimator_coverage/`](../experiments/estimator_coverage/) | §3 backing | `44a58f0` | 27-cell coverage simulation (AUC × n × CI variant), seed = 42; ~35 min wall time; `results.json` committed. |

### Library landings

| Artifact | Commit | What landed |
|---|---|---|
| [`pwm_dose_equivalence/`](../pwm_dose_equivalence/) v0.1.0 alpha | `0836162` (scaffold) + `e18121f` (gitignore) | Pip-installable package: modality-agnostic `signal_equivalence_credential` API; percentile + DeLong estimators with the v0.3 defaults baked in; (S1) / (S3) / (S4) sample-size pre-flight; content-addressed framework hash; `Tr_ct` / `Tr_mri` / `Tr_pet` operators consistent with the proofs writeups. |
| Same, test suite | `3a4b0f1` (coverage) + `909d505` (README number bumps) | **60/60 tests pass; 100 % line coverage** (230/230 statements). Well above the manuscript §software_rigor's 90 % v0.2 floor. Includes regression tests for the (S1)/(S3) numerical-table values, the estimator coverage-under-null, the verdict logic, and every documented `ValueError` branch in the public API. |

### Landed (manuscript-side propagation of the D9 + 13 / D9 + 14 landings)

| ID | What changed | Why |
|---|---|---|
| **V3-1** | **AUC-task default `ε` correction.** §methods-estimator rewritten with the corrected (S1) general CLT formula and the (S3) paired-AUC specialisation in terms of the DeLong placement-difference SD. The four end-to-end AUC code-block instances of `epsilon=0.02` (lung-nodule-AUC case study + Discussion sentence + §methods-library API showcase) bumped to `epsilon=0.05`; the API showcase comment now says "AUC default; 0.02 for non-AUC metrics". Reproducible n ≈ 130–250 across the typical AUC operating range — comfortably within the WS-1 v0.5 cohort. Non-AUC metrics keep ε = 0.02. | `proofs/sample_size.md` §5: the v0.1 hedge "n ≥ 192 for ε = 0.02" was wrong (took σ as per-arm AUC SD instead of DeLong placement-difference SD); at realistic placement variances, ε = 0.02 needs n ≈ 1500 at AUC = 0.85. |
| **V3-2** | **Estimator-default text rewrite.** Replaced the §methods-estimator "Coverage of percentile CIs near boundary" paragraph (which recommended BCa for AUC > 0.95 with `n < 200`) with a new "Estimator defaults" paragraph: percentile is the default; DeLong is auto-selected when `task.metric == "auc"` (mildly conservative; $\sim 300\times$ faster than the bootstrap variants); BCa remains opt-in. Discussion §"Estimator failure modes" softened the v0.2 "the library defaults to BCa in this regime with an explicit warning" to the new DeLong-and-MC-SE language. | `proofs/estimator.md` §3.2: BCa coverage at AUC = 0.97 / $n = 100$ is $0.900$ vs percentile $0.935$. BCa does not robustly outperform percentile under the null. |
| **V3-3** | **B5 software-rigor numbers.** Filled four `\todo` placeholders in §software_rigor: 60 unit tests (integration tests land at v0.2.0 alongside BCa); 100 % line coverage on 230 statements; current version `0.1.0` (alpha). Test inventory rewritten to match the actual v0.1.0 test suite (percentile + DeLong coverage; sample-size formulas vs numerical-table values; `T_r` operator invariants including NaN sentinel; JSON round-trip + framework-hash stability; verdict logic at boundaries; mode-misuse / sample-size-warning / ValueError branches). | Library at v0.1.0 alpha now exists with 60/60 tests passing at 100 % coverage; the placeholders had no reason to remain. Closes audit item B5. |
| **V3-4** | **PET Table 1 footnote.** Added a footnote on Methods Table 1 row 3 clarifying that the canonical PET `$T_r$` for v1 is *activity reduction*; *scan-time reduction* at full activity is statistically equivalent at the level of total counts but not physically equivalent (motion blur, kinetic modelling differ) and is documented as a v2 distinction. Footnote cites `experiments/cross_modality_consistency/` and `theory/proofs/pet_reduction.md`. Implemented as `\footnotemark[1]` in the table cell + `\footnotetext[1]{...}` after `\end{table}` (see *Typesetting fixes* below). | `proofs/pet_reduction.md` §3 explicitly recommended this footnote. |
| **V3-5** | **Cross-link the proofs.** Added inline pointers in §framework (to `proofs/mri_mask.md`, on the subpopulation-as-acquisition-protocol-bearing-measure paragraph) and Discussion §"Point-evaluated by design" (to `proofs/composition.md`, on the algebraic-combination-not-derivable paragraph). The §methods-estimator "Sample-size formula" and "Estimator defaults" paragraphs (V3-1 / V3-2) already cite `proofs/sample_size.md` and `proofs/estimator.md` inline. The PET Table 1 footnote (V3-4) cites `proofs/pet_reduction.md`. | Signposting the theory-side anchors so a reader/reviewer can pull the supporting derivations without leaving the manuscript text-flow. |

### Typesetting fixes

| ID | Issue | Fix | Commit |
|---|---|---|---|
| **V3-4-fix** | The V3-4 commit (`6416881`) placed `\footnote{...}` directly inside a `tabular` inside a `\begin{table}` float. LaTeX silently drops footnote bodies in this configuration: the marker (¹) rendered next to "rate `$r$`" in the PET row, but the footnote text never appeared on the page. Confirmed via `pdftotext` (grep for "canonical PET" returned nothing). | Switched the footnote to `\footnotemark[1]` in the table cell + `\footnotetext[1]{...}` placed immediately after `\end{table}`. The footnote body now renders at the bottom of page 10 with the standard horizontal rule above it. | `6fb1ee7` |

This is a recurring LaTeX footgun. For future table-cell footnotes in the manuscript, use the `\footnotemark` + `\footnotetext` pattern directly.

### Status changes

- Manuscript header status comment + `\date{}` bumped from v0.2 to v0.3 (commit `6416881`).
- Credential JSON `schema_version` unchanged at `pwm-signal-equivalence/v0.2` (none of V3-1 .. V3-5 change the JSON schema).
- PDF rebuilds at 19 pages, **517 KB** (was 453 KB at the V3-4-fix-pending commit `6416881`; the +64 KB is the now-rendered PET footnote body).
- Clean build: 0 LaTeX errors, 0 undefined references / citations, 0 BibTeX warnings. The only overfull `\hbox` warnings are the two pre-existing ones at lines 118–119 (verbatim listing) and 190–202 (comparison table), unchanged from v0.2.

### `open_questions.md` table — re-priority after D9 + 14

| § | Was | Now |
|---|---|---|
| §1 Literature depth-pass | SHARPEN, 1.5 wk | **still pending** — genuinely external work (reading specific papers) |
| §2 Sample-size formula | BLOCK, 2.0 wk | **done** — `proofs/sample_size.md` |
| §3 Estimator validity | BLOCK, 1.5 wk | **done (null only)** — `proofs/estimator.md`; non-null power sim is the follow-up |
| §4 Composition law | DEFER, 0.5 wk | **done** — `proofs/composition.md` |
| §5 Conditional monotonicity | SHARPEN, 1.0 wk | **still pending** — best after Phase 1 pilot data lands |
| §6 Per-patient guidance | SHARPEN, 0.5 wk | **done at manuscript level** (Definition 2 opt-in; Discussion paragraph) |
| §7 MRI mask decision | BLOCK MRI, 1.0 wk | **done** — `proofs/mri_mask.md` |
| §8 PET model | SHARPEN, 0.5 wk | **done** — `proofs/pet_reduction.md` |
| §9 Multi-task aggregation | DEFER (v2 acknowledgment) | unchanged |
| §10 Cross-subpopulation | DEFER (v2 acknowledgment) | unchanged |

Effort accounting: of the ~8 weeks of theory work originally scheduled, ~5.5 weeks closed across D9 + 13 / D9 + 14. The remaining items (§1 depth-pass; §5 monotonicity) are genuinely externally gated, not theory-time-blocked.

### Theory-doc lag (narrowed but not closed)

`theory/dose-equivalence-framework.md` still at **v0.1**. The gap to v0.2 is now narrowed to the literature depth-pass: the manuscript-side commitments that the proofs writeups anchored (Π-as-metadata; population-vs-sample evidence; estimator defaults; composition as non-derivable; activity-reduction-as-canonical-PET-`T_r`) are all consistent across (manuscript v0.2 + proofs/*.md v0.1), and a future theory-doc v0.2 will incorporate them with the depth-pass reading in the same pass.

---

## v0.2 — 2026-06-01

Seven pure-text edits + one synthetic experiment, all done before any Phase 1
or Phase 3 empirical work landed. The draft is now reviewer-readier than v0.1
without depending on data the team does not yet have.

### Landed

| ID | Commit | What changed | Why |
|---|---|---|---|
| **A4** | `5e90b88` | Demoted the on-chain registry from "contribution #4" to a deployment-only detail; SHA-256 content-addressing is now the methodological substance. Renamed `l2_framework_hash` → `framework_hash`; removed *blockchain* / *on-chain* / *L2 spec* jargon from the abstract, intro, results case study, and discussion. | The blockchain framing was the most reviewer-hostile claim in v0.1; Nature Methods reviewers reach for "gimmick" when they see *blockchain* attached to a methods paper. Content-addressing is the actual contribution and survives that framing intact. |
| **B2** | `5e90b88` | Title shortened from "Signal-Equivalence: A Probabilistic Framework for Comparing Reconstruction Methods Across Reduced-Signal Imaging Modalities" (18 words) to "Signal-equivalence: testable dose-reduction claims for medical imaging" (8 words). Abstract restructured into four beats (problem / framework / library + worked examples / implications) without literal headings. | v0.1 title front-loaded "probabilistic" and was too long for Nature Methods house style. |
| **A3** | `5e90b88` | In §framework and clarification C5: `Π` carries acquisition-protocol metadata (CT vendor/kVp, MRI mask family, PET tracer/scanner). The MRI mask family rides inside `Π`, not as a sixth tuple slot. | open_questions §7 had flagged that the 5-tuple was effectively a 6-tuple for MRI. This edit closes the asymmetry inside the manuscript, not just in the proofs. |
| **B3** | `5e90b88` | "Out-of-scope claim types" rewritten as "Point-evaluated by design"; superiority / cross-modality / composition / multi-task framed as deliberate non-derivability rather than refusals. "Subpopulation failure modes" softened to "Subpopulation specificity" with explicit FDA subgroup-stratified-reporting alignment. | v0.1 read as a list of apologies. Same content, defensive instead of apologetic. |
| **B1** | `1cb17dd` | Added "Population claim vs.\ sample evidence" paragraph immediately after Definition 1: the two expectations are deterministic population objects the credential **asserts**; the bootstrap procedure at significance `α` provides finite-sample **evidence** from a test set drawn from `Π`. The credential records `n_test` and a slug resolving to the operational sampling protocol. | v0.1 conflated "population mean" (LHS of Eq. 1) with "α-confidence under the paired bootstrap" inside a single iff. The cleanest reviewer attack on the v0.1 draft. |
| **A5** | `5f0317e` | New "Ground-truth protocol" paragraph at the top of §methods-estimator borrowing the PWM-LDCT v0.5 annotation QA protocol verbatim (eligibility / 20-case calibration κ ≥ 0.60 / IoU ≥ 0.3 matching / >50 % majority-vote consolidation / third-rad discordance adjudication / rotating 5-case drift re-calibration). New "Label-noise refusal threshold" paragraph: the library refuses to issue a credential when documented inter-reader disagreement exceeds `ε/2`. Unified the credential JSON `ground_truth_protocol` field across the two worked-example JSONs. | v0.1's `ground_truth = "majority-vote-2-rads"` slug was hand-waved; for lung-nodule AUC this is the single most attackable claim in the paper. |
| **A6** | `120c61b` | New "Relation to task-based image-quality assessment" intro paragraph positioning signal-equivalence as complementary to the Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233 lineage. Three anchor cites added to `refs.bib`. Theory folder: seeded `theory/related_work.md` with the four-paper memo skeleton and a "what is genuinely new" novelty gate for the v0.2 framework draft. | Closes the "you have reinvented task-based image quality" reviewer attack. open_questions §1 literature pass has a head start. |
| **A2** | `a5b67e2` | New Results subsection "Cross-modality consistency on synthetic data" with **real numbers** (not `\todo`): six credentials (3 modalities × 2 candidates) produced by the same paired-bootstrap code path show 3 expected PASS and 3 expected FAIL verdicts. New `experiments/cross_modality_consistency/` with a self-contained Python script, frozen `results.json`, and README. | The three independent per-modality worked examples did not rule out the possibility that the framework's generality is rhetorical. This experiment closes the gap with reproducible (seed = 42, bit-for-bit) numbers. |

### Schema bumps

- Credential JSON `schema_version`: `pwm-signal-equivalence/v0.1` → `v0.2`. Field renames (`l2_framework_hash` → `framework_hash`; `ground_truth` → `ground_truth_protocol`) are technically breaking; in pre-v1 we bump MINOR rather than introduce a parallel-versioning shim. The library, once it exists in Phase 3, ships against the v0.2 schema directly.

### What v0.2 still does **not** contain

- **Real per-modality Results tables.** Gated on WS-2 Phase 1 (CT, D9+90) and Phase 3 (MRI + PET validators, D9+270 → D9+365).
- **Numbers in the end-to-end worked example prose** (B4). Gated on the per-modality tables.
- **Real software-rigor counts.** `$N_{\textrm{tests}}$` and coverage % remain `\todo` until Phase 3 `pwm_dose_equivalence` v0.1 ships.
- **Closed-form sample-size derivation + coverage simulations.** open_questions §2 (BLOCK, ~2 wk) and §3 (BLOCK, ~1.5 wk); not data-gated but theory work that has not been scheduled into this pass.

### Theory-doc lag (intentional)

`theory/dose-equivalence-framework.md` remains at **v0.1**. Its own headline says it "Will be superseded by v0.2 after literature pass (see [`open_questions.md`](open_questions.md) §1)," and the literature pass has only been *seeded* (`theory/related_work.md` v0.1) rather than completed in depth. The manuscript-side v0.2 has therefore moved ahead of the theory-doc v0.1 — that is the documented gap.

What would close the gap: the depth-pass reading of fastMRI reader studies, one CHO-for-low-dose-CT paper, and Wunderlich/Noo on observer-model variance (listed in `theory/related_work.md` §5). At that point the theory doc bumps to v0.2 with the [SHARPEN-N] points reconciled against the manuscript edits in this changelog.

---

## v0.1 — 2026-05-20

Initial Nature Methods working draft seeded alongside `theory/dose-equivalence-framework.md` v0.1 and `theory/open_questions.md` v0.1. Not logged in detail here; see commit `5e90b88`'s parent for the seed state.
