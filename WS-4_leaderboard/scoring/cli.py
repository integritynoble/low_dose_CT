"""WS-4 leaderboard CLI.

Usage:
    python -m scoring.cli init --out <leaderboard.json>
    python -m scoring.cli validate --result <results.json>
    python -m scoring.cli submit --result <results.json> --method <name> [--vendor <v>] [--dose <d>] [--out <leaderboard.json>]
    python -m scoring.cli list [--leaderboard <leaderboard.json>]
    python -m scoring.cli spread [--leaderboard <leaderboard.json>] [--by vendor|dose]
    python -m scoring.cli observer-sensitivity [--leaderboard <leaderboard.json>] [--seed N] [--markdown]
    python -m scoring.cli rung-status [--registry <rung_registry.json>] [--markdown]

Run from the WS-4_leaderboard root. ``--out`` defaults to ``scoring/data/leaderboard.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .heldout import (OWN_PRINCIPAL, SubmissionEnvelope,
                      check_submission_cannot_write_back, make_heldout_set)
from .leaderboard import (REFERENCE_ENTRY_ID, add_submission, blur_entry,
                          compute_spread, load, new_leaderboard, save)
from .observer_sensitivity import publish_observer_channels, report_observer_sensitivity
from .rung_registry import DEFAULT_REGISTRY, load_registry, render_markdown
from .verify import check_submission_result

DEFAULT_BOARD = Path(__file__).resolve().parent / "data" / "leaderboard.json"


def _load_result(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_init(args) -> int:
    board = new_leaderboard()
    save(board, args.out)
    print(f"initialised leaderboard with seed entries at {args.out}")
    print(f"  permanent blur trap: {board['entries'][0]['id']}")
    return 0


def cmd_validate(args) -> int:
    result = _load_result(args.result)
    violations = check_submission_result(result)
    if violations and any(errs for errs in violations.values()):
        for name, errs in violations.items():
            if errs:
                print(f"REJECT method '{name}':")
                for e in errs:
                    print(f"  - {e}")
        return 1
    print("OK: every method block carries paired fidelity+detectability (§4)")
    return 0


def cmd_submit(args) -> int:
    board = load(args.out) if Path(args.out).exists() else new_leaderboard()
    result = _load_result(args.result)
    # P1-3: every submission travels in a write-path-free envelope.
    envelope = SubmissionEnvelope(method_name=args.method, result=result)
    violations = check_submission_cannot_write_back(envelope)
    if violations:
        print("REJECT: submission is structurally able to write back to the board/data:")
        for v in violations:
            print(f"  - {v}")
        return 1
    try:
        created = add_submission(board, result, method=args.method,
                                 vendor=args.vendor, dose=args.dose)
    except ValueError as exc:
        print(f"REJECT: {exc}")
        return 1
    try:
        save(board, args.out)
    except ValueError as exc:
        print(f"REJECT: {exc}")
        return 1
    for e in created:
        m = e["metrics"]
        ctx = f" vendor={e.get('vendor')} dose={e.get('dose')}" if e.get("vendor") or e.get("dose") else ""
        print(f"accepted {e['id']}: method={e['method']} psnr={m.get('psnr_db'):.3f} "
              f"cnr={m.get('cnr_mean')} cho_auc={m.get('cho_auc_mean')}{ctx}")
    print(f"leaderboard now has {len(board['entries'])} entries -> {args.out}")
    pub = board.get("publication", {}).get("status", "pending")
    print(f"receipt recorded; publication status: {pub} "
          "(a receipt is not a publication)")
    return 0


def cmd_list(args) -> int:
    board = load(args.leaderboard)
    blur = blur_entry(board.get("entries", []))
    assert blur is not None, "blur trap missing"
    bm = blur["metrics"]
    print(f"WS-4 leaderboard (detectability-first; task: {board['task']['label']})")
    print(f"{'rank':<5}{'id':<24}{'method':<36}{'psnr_db':>9}{'ssim':>10}"
          f"{'cnr':>8}{'cho_auc':>9}{'vs_blur_psnr':>14}{'vs_blur_cnr':>12}")
    for i, e in enumerate(board.get("entries", []), 1):
        m = e["metrics"]
        cnr = m.get("cnr_mean")
        vs_p = (m.get("psnr_db") - bm.get("psnr_db")) if m.get("psnr_db") is not None else None
        vs_c = (cnr - bm.get("cnr_mean")) if isinstance(cnr, (int, float)) else None
        tag = " [TRAP]" if e.get("trap") else (" [placeholder]" if e.get("placeholder") else "")
        print(f"{i:<5}{e['id']:<24}{e['method'][:35]:<36}"
              f"{m.get('psnr_db'):>9.3f}"
              f"{(m.get('ssim') if m.get('ssim') is not None else float('nan')):>10.4g}"
              f"{(cnr if isinstance(cnr, (int, float)) else float('nan')):>8.3g}"
              f"{m.get('cho_auc_mean'):>9.3f}"
              f"{(vs_p if vs_p is not None else float('nan')):>14.3f}"
              f"{(vs_c if vs_c is not None else float('nan')):>12.3g}{tag}")
    return 0


def cmd_spread(args) -> int:
    board = load(args.leaderboard)
    spread = compute_spread(board.get("entries", []), by=args.by)
    print(f"WS-4 spread by {args.by} (Rung 6: never average across {args.by})")
    print(f"{'group':<16}{'n':>4}{'psnr_span':>12}{'psnr_std':>12}"
          f"{'cnr_span':>12}{'cnr_std':>12}")
    for key in sorted(spread):
        s = spread[key]
        print(f"{key:<16}{s.get('n', 0):>4}"
              f"{s.get('psnr_db_span', float('nan')):>12.4g}"
              f"{s.get('psnr_db_std', float('nan')):>12.4g}"
              f"{s.get('cnr_mean_span', float('nan')):>12.4g}"
              f"{s.get('cnr_mean_std', float('nan')):>12.4g}")
    if not spread:
        print("  (no entries carry this grouping key yet)")
    return 0


def cmd_observer_sensitivity(args) -> int:
    board = load(args.leaderboard)
    channels = publish_observer_channels()
    print(f"observer channels: {channels['observers'][0]['name']} + "
          f"{channels['observers'][1]['name']} (internal noise published)")
    print(report_observer_sensitivity(board.get("entries", []), seed=args.seed,
                                      markdown=args.markdown))
    return 0


def cmd_verify_bundle(args) -> int:
    verdict = verify_runbundle(
        args.bundle,
        live_result=(_load_result(args.live) if args.live else None),
        entries=None,  # S4 pre-check needs the candidate board; pipeline never writes it
        method_name="submission",
        vendor=args.vendor,
        dose=args.dose,
        run_ws1_gates=not args.skip_ws1_gates)
    print(f"verify-bundle: {verdict.summary()}")
    for stage in ("S1", "S2", "S3", "S4"):
        viol = verdict.violations.get(stage, [])
        if stage in verdict.skipped:
            print(f"  {stage}: SKIPPED")
        elif viol:
            print(f"  {stage}: REJECT ({len(viol)} violation(s))")
            for v in viol:
                print(f"    - {v}")
        else:
            print(f"  {stage}: PASS")
    if "S3" in verdict.skipped:
        print("  (S3 live execution is a container/data-machine dependency; "
              "the numeric comparison is exercised by verify_published_vs_live)")
    if "S4" in verdict.skipped:
        print("  (S4 pre-check needs the candidate board entries; the final "
              "write goes through `python -m scoring.cli submit`, which runs "
              "the full §2-C gate chain)")
    return 0 if verdict.ok else 1


def cmd_rung_status(args) -> int:
    reg = load_registry(args.registry)
    if args.markdown:
        print(render_markdown(reg))
    else:
        print(f"WS-4 Rung 1-6 registry (updated {reg.get('updated_at', 'unknown')})")
        for r in reg["rungs"]:
            print(f"  Rung {r['rung']} [{r['status']:<7}] {r['title']}")
            print(f"           supported: {'; '.join(r.get('supported_data', []))}")
            print(f"           reason: {r.get('reason', '')}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="WS-4 leaderboard CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create a fresh leaderboard with seed entries")
    p.add_argument("--out", default=str(DEFAULT_BOARD))
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="check a submission's paired gate only")
    p.add_argument("--result", required=True)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("submit", help="gate + append a submission to the leaderboard")
    p.add_argument("--result", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--vendor", default=None, help="measurement vendor (spread grouping)")
    p.add_argument("--dose", default=None, help="measurement dose level (spread grouping)")
    p.add_argument("--out", default=str(DEFAULT_BOARD))
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("list", help="print the leaderboard with blur-trap comparison")
    p.add_argument("--leaderboard", default=str(DEFAULT_BOARD))
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("spread", help="per-vendor/per-dose dual-metric spread (P1-4)")
    p.add_argument("--leaderboard", default=str(DEFAULT_BOARD))
    p.add_argument("--by", choices=("vendor", "dose"), default="vendor")
    p.set_defaults(func=cmd_spread)

    p = sub.add_parser("observer-sensitivity",
                       help="second-observer rank-change report (P2-5, synthetic)")
    p.add_argument("--leaderboard", default=str(DEFAULT_BOARD))
    p.add_argument("--seed", type=int, default=20260821)
    p.add_argument("--markdown", action="store_true")
    p.set_defaults(func=cmd_observer_sensitivity)

    p = sub.add_parser("rung-status", help="print Rung 1-6 registry (P3-6)")
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p.add_argument("--markdown", action="store_true")
    p.set_defaults(func=cmd_rung_status)

    p = sub.add_parser("verify-bundle",
                       help="S1-S4 verification pipeline on a RunBundle (Phase 1, 1.2)")
    p.add_argument("--bundle", required=True,
                   help="path to the RunBundle directory (contract §1)")
    p.add_argument("--live", default=None,
                   help="optional live results.json from sandbox execution (S3)")
    p.add_argument("--vendor", default=None, help="measurement vendor label")
    p.add_argument("--dose", default=None, help="measurement dose level label")
    p.add_argument("--skip-ws1-gates", action="store_true",
                   help="skip the Rung 2/3/4 WS-1 artifact gates (S2)")
    p.set_defaults(func=cmd_verify_bundle)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
