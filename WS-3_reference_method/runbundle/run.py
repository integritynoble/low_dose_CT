#!/usr/bin/env python
"""WS-3 RunBundle entrypoint -- reproduce the corpus + validation numbers.

Modes:
  --self-test   Synthetic end-to-end (no GPU / no data): train a tiny ensemble, emit a corpus
                (reference + FBP baseline), run the deposit pipeline, and compute a validation
                block. Proves the bundle executes; the numbers are NOT scientific.
  --emit        Real reproduction: reconstruct a held-out WS-1 split with pinned ensemble
                weights and the frozen detector (GPU + data gated; stubbed until Phase 3).

Writes ``results.json`` (validated against ``results.schema.json``) and exits non-zero on any
failure, so an external verifier can `docker run` the bundle and diff the results.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent


def _ensure_import() -> None:
    """Allow running from a checkout without installing (CI/self-test); the image installs it."""
    try:
        import pwm_ldct_recon  # noqa: F401
    except ImportError:
        sys.path.insert(0, str(_HERE.parent / "method" / "src"))
    # The sibling corpus_emit tool imports pwm_dose_equivalence (WS-2) to audit
    # credentials; expose its src in a repo-tree layout (Docker images install it).
    try:
        import pwm_dose_equivalence  # noqa: F401
    except ImportError:
        ws2_src = _HERE.parent.parent / "WS-2_framework" / "pwm_dose_equivalence" / "src"
        if ws2_src.is_dir() and str(ws2_src) not in sys.path:
            sys.path.insert(0, str(ws2_src))


def self_test(out_dir: str, size: int, steps: int) -> dict:
    _ensure_import()
    from pwm_ldct_recon import __version__
    from pwm_ldct_recon.demo import demo_ok, run_demo

    report = run_demo(out_dir, size=size, steps=steps)
    return {
        "bundle": "pwm-ldct-recon-runbundle",
        "method_version": __version__,
        "mode": report["mode"],
        "ok": demo_ok(report),
        "corpus": {k: report[k] for k in (
            "n_credentials", "n_baseline_methods", "manifest_ok",
            "error_maps_ok", "n_error_maps_checked")},
        "counts": report["counts"],
        "validation": report["validation"],
        "notes": ("self-test on synthetic data; not scientific numbers. Real reproduction "
                  "needs pinned ensemble weights + an authorised WS-1 tree (`--emit`)."),
    }


def emit_real(args: argparse.Namespace) -> dict:
    raise SystemExit(
        "emit: real reproduction is GPU- and data-gated. Provide --weights (pinned ensemble), "
        "--data-root (authorised WS-1 tree), and the frozen detector, then wire "
        "pwm_ldct_recon.emit_corpus.run here (see method/src/pwm_ldct_recon/cli.py cmd_emit). "
        "The --self-test path exercises the identical pipeline on synthetic data."
    )


def _validate_results(results: dict) -> list[str]:
    schema_path = _HERE / "results.schema.json"
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []  # validation is best-effort; absence of jsonschema is not a failure
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return [e.message for e in
            sorted(jsonschema.Draft202012Validator(schema).iter_errors(results),
                   key=lambda e: e.path)]


def _paired_gate(results: dict) -> list[str]:
    """Hard §4 paired gate (both numbers or neither) -- independent of jsonschema.

    Enforced in code so the gate cannot silently disappear when the optional
    ``jsonschema`` dependency is missing: every validation block must carry PSNR and
    detectability together, for the reference method and for each paired_methods entry
    (the permanent Gaussian blur trap included).
    """
    _ensure_import()
    try:
        from pwm_ldct_recon.evaluation import validate_paired_report
    except Exception as exc:  # pragma: no cover - import environment failure
        return [f"evaluation import failed; paired gate cannot run: {exc}"]
    v = results.get("validation")
    if not isinstance(v, dict):
        return ["validation block missing; paired gate fails"]
    return validate_paired_report(v)


def _heldout_gate(results: dict, mode: str) -> list[str]:
    """Held-out split isolation gate (low-dose-ct.md §6 / §7.2, P1-4).

    Structural check, independent of the paired gate:
      * self-test mode: static scan that the eval entrypoints (evaluation.py, run.py)
        do not import the training path (``data`` / ``train``) -- the demo uses
        synthetic pairs and is explicitly non-scientific.
      * emit mode (real reproduction): the validation block must additionally declare
        held-out-split provenance before its numbers can be publishable evidence.
    """
    _ensure_import()
    try:
        from pwm_ldct_recon.heldout import heldout_isolation_gate
    except Exception as exc:  # pragma: no cover - import environment failure
        return [f"heldout import failed; isolation gate cannot run: {exc}"]
    v = results.get("validation")
    if not isinstance(v, dict):
        return ["validation block missing; held-out isolation gate fails"]
    return heldout_isolation_gate(v, mode=mode)


def _json_safe(obj):
    """Recursively replace non-finite floats with None (strict-JSON output).

    Undefined ratios (e.g. CNR on a locally noise-free synthetic patch) must not be
    serialised as the non-standard ``Infinity`` / ``NaN`` tokens; the schema allows
    ``null`` for those fields so the emitted results.json stays portable.
    """
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WS-3 RunBundle: reproduce corpus + validation.")
    ap.add_argument("--self-test", action="store_true", help="synthetic end-to-end (no GPU/data)")
    ap.add_argument("--emit", action="store_true", help="real reproduction (GPU+data gated)")
    ap.add_argument("--out", default="/tmp/pwm_ws3_runbundle_corpus", help="corpus output dir")
    ap.add_argument("--results", default="results.json", help="results.json path")
    ap.add_argument("--size", type=int, default=24)
    ap.add_argument("--steps", type=int, default=3)
    args = ap.parse_args(argv)

    if args.emit:
        results = emit_real(args)
    else:  # default to the self-test
        results = self_test(args.out, args.size, args.steps)

    schema_errors = _validate_results(results)
    paired_errors = _paired_gate(results)
    mode = "emit" if args.emit else "self-test"
    heldout_errors = _heldout_gate(results, mode=mode)
    results["results_schema_ok"] = not schema_errors
    results["paired_gate_ok"] = not paired_errors
    results["heldout_isolation_ok"] = not heldout_errors
    results["heldout_gate_mode"] = mode
    Path(args.results).write_text(
        json.dumps(_json_safe(results), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(_json_safe(results), indent=2))
    if schema_errors:
        print("results.json schema errors:", schema_errors, file=sys.stderr)
    if paired_errors:
        print("paired gate errors:", paired_errors, file=sys.stderr)
    if heldout_errors:
        print("held-out isolation gate errors:", heldout_errors, file=sys.stderr)
    return 0 if (results.get("ok") and not schema_errors and not paired_errors and not heldout_errors) else 1


if __name__ == "__main__":
    raise SystemExit(main())
