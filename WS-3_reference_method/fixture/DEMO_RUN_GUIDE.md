# Isolated run guide: the synthetic package, verified both ways

Ticket H1a/H8a of the September 2026 implementation plan (v8 §6, stage 1): a reproducible artifact with no
LLM, run in a pinned, isolated environment, that **accepts one valid synthetic package and rejects
deliberately corrupted copies with a specific reason**, with every command and hash recorded. It also
emits the minimum R1-compatible evidence packet (v8 §10).

Everything here is **synthetic**. Pixels and scores come from a seeded RNG. No reconstruction runs, no
image-quality number is computed, and nothing is a clinical or scientific result. What is demonstrated is
that the deposit verifiers are real verifiers: each accepts the field's own well-formed package and
refuses a broken copy for the reason it was broken.

## 1. Pin the environment

Any Python ≥ 3.10. Install only what the fixture needs; nothing else.

```bash
git clone git@github.com:integritynoble/low_dose_CT.git && cd low_dose_CT
git checkout 49bd9f9764dcf3b6e8bc05fdea0170ed445e7f9c        # or the commit that carries this guide
python3 -m venv /tmp/ldct-venv
/tmp/ldct-venv/bin/pip install numpy nibabel pytest jsonschema
/tmp/ldct-venv/bin/pip install -e WS-2_framework/pwm_dose_equivalence   # pulls scipy
/tmp/ldct-venv/bin/pip list
```

`jsonschema` is **mandatory** here even though the code treats it as optional: `package_corpus` validates
the metadata only if the module is importable and otherwise reports *no errors*. The demonstration below
detects that and reports the check as not executed, but the existing fixture tests do not, so a run
without `jsonschema` would pass the suite while never having checked the schema.

Recorded run (2026-09-07, host alias `spiritai`, 8 vCPU, no GPU):

| Component | Version |
|---|---|
| Python | 3.12.3 (Linux 6.17, glibc 2.39) |
| numpy | 2.5.3 |
| scipy | 1.18.1 |
| nibabel | 5.4.2 |
| jsonschema | 4.26.0 |
| pytest | 9.1.1 |
| pwm_dose_equivalence | 0.2.2, editable from `WS-2_framework/` |

Environment size: 112 MB before the WS-2 library, ~150 MB after. Install took under a minute.

## 2. Run the existing fixture tests, skips reported

```bash
cd WS-3_reference_method/fixture
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /tmp/ldct-venv/bin/python -m pytest -q -p no:cacheprovider -rs tests/test_make_synthetic_corpus.py
```

Recorded: **14 passed, 0 skipped** in 3.2 s. (The README's "11 passed" predates three error-map tests.)
The two NIfTI round-trip tests skip when `nibabel` is absent; with `-rs` a skip is printed, not hidden.

## 3. Run the demonstration

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/ldct-venv/bin/python demo_verify.py /tmp/ldct-demo --seed 42 --host-alias <your alias>
```

It builds one valid corpus at `/tmp/ldct-demo/valid`, then for each case below makes a **disposable copy**
under `/tmp/ldct-demo/cases/<case>/`, corrupts only the copy, and runs six verifiers on it: completeness,
integrity (`MANIFEST.sha256`), error-map construction (`error_abs == |recon − reference|`), credential
audit, metadata consistency against disk, and metadata schema. Finally it re-verifies the valid corpus and
checks its manifest hash is unchanged.

| Case | Package | Fixed expectation | Recorded decision and reason |
|---|---|---|---|
| D01 | valid, seed 42 | ACCEPT | ACCEPT |
| D02 | valid, seed 43 (own provenance) | ACCEPT | ACCEPT |
| D03 | `task_nodule_score.nii.gz` deleted | REJECT | REJECT: completeness names the file; integrity lists it as absent; metadata says 32 records, disk holds 31 |
| D04 | `recon_mean.nii.gz` bytes replaced | REJECT | REJECT: bytes differ from `MANIFEST.sha256` for that file; its error map is no longer `|recon − reference|` |
| D05 | `counts.n_scans` set to 9, manifest rebuilt | REJECT | REJECT: metadata says 9, disk holds 2 (only the consistency check can see this; the manifest is valid) |
| D06 | a credential's verdict flipped, manifest rebuilt | REJECT | REJECT: stored `PASS` but the interval vs ε implies `INDETERMINATE` |
| D07 | `error_abs.nii.gz` replaced by a constant, manifest rebuilt | REJECT | REJECT: not `|recon − reference|`, max deviation 99 |
| D08 | `MANIFEST.sha256` deleted | UNVERIFIED | UNVERIFIED: integrity verifier raised `PackageError`; completeness also names the missing manifest |

Recorded summary line:

```
requested 8  completed 8  admissible 7  as expected 8  valid corpus untouched: True  verdict: PASS
```

Wall time 0.7 s, GPU 0 s, no tokens, no paid calls, no human intervention. Exit code 0.

The three outcomes are kept apart on purpose. `ACCEPT`/`REJECT` are decisions about the package's
structural claims. `UNVERIFIED` is an execution outcome: a verifier could not run, so no claim was
decided. D08 passes the error-handling test without becoming a successful verification, and it is not a
refusal of any scientific claim.

## 4. Read the evidence packet

`/tmp/ldct-demo/evidence_packet.json` carries, per v8 §10's minimum envelope: run id, UTC start and end,
host alias, source commit plus a digest of the dirty diff and untracked files in scope, the script's own
SHA-256, agent identity (deterministic script, no model), runtime versions, the synthetic designation and
data-use scope, input hashes (seed metadata, schema), requested against completed cases, attempts,
failures/timeouts, per-case verifier outputs, wall and GPU time, token and cost status, output hashes, the
acceptance verdict, limitations, a supersession slot and the public-export allowlist.

Recorded: seed metadata `9c9390ab…018f02`, schema `63e1dd77…0dccda`, source commit
`49bd9f9764dcf3b6e8bc05fdea0170ed445e7f9c`.

## 5. Run the demonstration's own tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /tmp/ldct-venv/bin/python -m pytest -q -p no:cacheprovider -rs tests
```

`tests/test_demo_verify.py` holds seven tests: every case decides as fixed in advance; each rejection
names the thing that is wrong; a verifier that cannot run yields UNVERIFIED and not a verdict; the valid
corpus is byte-identical after all cases and every corruption happened in a copy; the packet carries the
envelope; **with `jsonschema` absent the schema check reports itself as not executed and the package is
not ACCEPTed**; and a non-empty output directory is refused. Recorded: 21 passed, 0 skipped.

## 6. What this does not establish

- Nothing about reconstruction quality, the reference method, or any baseline. No model ran.
- Nothing clinical. The inputs are random numbers with the right shapes.
- Nothing about the WS-3 detector, which is still the deterministic stub (`method/src/pwm_ldct_recon/detector.py`).
- Nothing about the rung statuses or the R6 comparison; those are separate open items.
- One seed and eight cases are an engineering pilot, not a reliability estimate. Cases T07–T10 of the
  plan's ten-case pilot (unsupported interpretation, stub described as real, verifier crash under an agent,
  timeout) need the agent wrapper of ticket C1a and are not attempted here.
- A second machine reproducing this is a cross-environment reproduction, not an independent evaluation.
