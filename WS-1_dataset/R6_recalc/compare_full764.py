"""R6 独立复算 · 步骤4 全量复算结果与 on-board 基准的数值比对。

比对 r6 复算输出 results/<model>_det_full764.json
与作者 onboard 基准 <repo>/WS-1_dataset/baselines/results/<model>_results_det_full764.json
逐 seed、逐 dose 比对 psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean，以及 n。

判定口径（dated 2026-09-09，issue #5 route (a) 实证后修订）：
- shipped 判据保持预注册的 absolute 1e-6 不变（见 results/comparison_full764.json
  的 status/overall 字段，本脚本不放松该阈值）；
- 按 DIRECTOR_DECISIONS §2.1 要求，比较器同时**按指标各自量纲声明一致性**
  （per-metric 块：每指标 max abs/rel diff + rel 1e-6 判定），不再只给单一
  绝对阈值跨五个数量级施压；
- route(a) deterministic 内核重跑（2026-09-05/06 执行完毕）的实证记录写入
  routeA_rerun_evidence 块：重跑与 pre-routeA 非确定性结果逐位一致（差异
  不是 kernel 非确定性），与 onboard 的残留差异为跨环境系统性 float 偏差
  （最差 reldiff red_cnn 6.4e-5 / corediff 2.5e-5 / ctformer 4.4e-7）。

输出：results/comparison_full764.json + 控制台摘要
"""
from __future__ import annotations

import json
import os

MODELS = ["blur", "red_cnn", "learn", "ctformer", "corediff"]
SEEDS = ["42", "2023", "7", "12345", "999"]
DOSES = ["sim_r010", "sim_r025", "sim_r050"]
METRICS = ["psnr", "ssim", "cnr_mean", "cho_auc_mean", "npwe_mean"]
ABS_TOL = 1e-6          # shipped, pre-registered absolute criterion (unchanged)
REL_UNIT = 1e-6         # per-metric relative strictness used for declaration

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "results")           # r6 recalc outputs live under results/
ONBOARD = os.environ.get(
    "R6_ONBOARD_RESULTS",
    r"D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\results",
)

ROUTE_A_EVIDENCE = {
    "dated": "2026-09-09",
    "issue": "#5",
    "route": "(a) deterministic kernels re-run, as decided by the Director",
    "rerun_script": "run_routeA_det.py (r6_recalc work dir, outside this repo)",
    "rerun_performed": "2026-09-05 00:21 .. 2026-09-06 06:48 local",
    "rerun_log": "r6_recalc/routeA_run.log: red_cnn 585.4min rc=0, ctformer 422.8min rc=0, "
                 "corediff 1824.1min rc=0; kernels: cudnn.deterministic=True, "
                 "cudnn.benchmark=False, use_deterministic_algorithms(True), "
                 "CUBLAS_WORKSPACE_CONFIG=:4096:8; 2x RTX 4090",
    "models_rerun": ["red_cnn", "ctformer", "corediff"],
    "models_not_rerun_reason": "blur/learn were already bit-identical to onboard; "
                               "route (a) covers the three learning models only",
    "same_side_determinism_check": (
        "deterministic re-run vs pre-routeA non-deterministic re-run of the same side: "
        "n_diffs = 0 for red_cnn / ctformer / corediff (bit-identical). The eval path "
        "is therefore not sensitive to cuDNN kernel non-determinism in this environment."
    ),
    "vs_onboard_finding": (
        "Deterministic re-run still differs from the onboard reference at the shipped "
        "absolute 1e-6 (red_cnn 45 / ctformer 25 / corediff 45 of 75 comparisons). "
        "Worst relative differences: red_cnn 6.36e-5 (cnr_mean), corediff 2.50e-5 "
        "(cnr_mean), ctformer 4.41e-7 (cnr_mean). Since determinism on/off does not "
        "change the recalc side, the residual difference is NOT cuDNN kernel "
        "non-determinism; it is a systematic cross-environment float offset between "
        "the independent recalc venv and the onboard environment (driver/library "
        "build differences). Route (a) as scoped -- deterministic re-run of the "
        "recalc side only -- cannot reach bit-identical agreement with the historical "
        "onboard reference. Per-metric declaration below is the honest statement."
    ),
}


def metric_val(per_dose, met):
    if met in ("cnr_mean", "cho_auc_mean", "npwe_mean"):
        return (per_dose.get("detectability") or {}).get(met)
    return per_dose.get(met)


def main():
    report = {
        "tolerance": ABS_TOL,
        "tolerance_kind": "absolute",
        "criterion_note": (
            "shipped pre-registered criterion is absolute 1e-6, unchanged; "
            "comparator additionally declares agreement per metric in that metric's "
            "own units (DIRECTOR_DECISIONS 2.1); route (a) deterministic re-run "
            "evidence appended dated 2026-09-09 (issue #5)"
        ),
        "per_model": {},
        "routeA_rerun_evidence": ROUTE_A_EVIDENCE,
    }
    all_pass_abs = True
    per_metric_decl = {}
    for m in MODELS:
        rec = os.path.join(REC, f"{m}_det_full764.json")
        ob = os.path.join(ONBOARD, f"{m}_results_det_full764.json")
        if not (os.path.isfile(rec) and os.path.isfile(ob)):
            report["per_model"][m] = {"status": "MISSING",
                                      "recalc": os.path.isfile(rec),
                                      "onboard": os.path.isfile(ob)}
            all_pass_abs = False
            continue
        with open(rec, encoding="utf-8") as f:
            rj = json.load(f)
        with open(ob, encoding="utf-8") as f:
            oj = json.load(f)
        diffs = []
        n_checked = 0
        worst_abs = 0.0
        worst_rel = 0.0
        per_metric = {}
        for s in SEEDS:
            if s not in rj.get("per_seed", {}) or s not in oj.get("per_seed", {}):
                diffs.append(f"{m} s{s}: missing per_seed")
                continue
            for d in DOSES:
                rd = rj["per_seed"][s]["per_dose"].get(d, {})
                od = oj["per_seed"][s]["per_dose"].get(d, {})
                for met in METRICS:
                    rv = metric_val(rd, met)
                    ov = metric_val(od, met)
                    n_checked += 1
                    if rv is None or ov is None:
                        if rv != ov:
                            diffs.append(f"{m} s{s} {d} {met}: recalc={rv} onboard={ov}")
                        continue
                    rv, ov = float(rv), float(ov)
                    ad = abs(rv - ov)
                    rel = ad / max(abs(ov), 1e-12)
                    worst_abs = max(worst_abs, ad)
                    worst_rel = max(worst_rel, rel)
                    pm = per_metric.setdefault(
                        met, {"max_absdiff": 0.0, "max_reldiff": 0.0})
                    pm["max_absdiff"] = max(pm["max_absdiff"], ad)
                    pm["max_reldiff"] = max(pm["max_reldiff"], rel)
                    if ad > ABS_TOL:
                        diffs.append(f"{m} s{s} {d} {met}: "
                                     f"recalc={rv:.9g} onboard={ov:.9g} "
                                     f"absdiff={ad:.3g} reldiff={rel:.3g}")
        # n 一致性
        for s in SEEDS:
            for d in DOSES:
                rn = rj["per_seed"][s]["per_dose"].get(d, {}).get("n")
                on = oj["per_seed"][s]["per_dose"].get(d, {}).get("n")
                if rn is not None and on is not None and rn != on:
                    diffs.append(f"{m} s{s} {d} n: recalc={rn} onboard={on}")
        ok = len(diffs) == 0
        all_pass_abs = all_pass_abs and ok
        decl = {}
        for met, v in sorted(per_metric.items()):
            decl[met] = {
                "max_absdiff": v["max_absdiff"],
                "max_reldiff": v["max_reldiff"],
                "declared_at_rel_1e-6": "PASS" if v["max_reldiff"] <= REL_UNIT else "FAIL",
            }
        per_metric_decl[m] = decl
        report["per_model"][m] = {
            "status": "PASS" if ok else "FAIL",
            "n_checked": n_checked, "n_diffs": len(diffs),
            "worst_absdiff": worst_abs, "worst_reldiff": worst_rel,
            "diffs": diffs[:50],
        }
        print(f"[{m}] {'PASS' if ok else 'FAIL'}  checked={n_checked} "
              f"diffs={len(diffs)} worst_abs={worst_abs:.3g} worst_rel={worst_rel:.3g}")
        for met, v in decl.items():
            print(f"      {met:12s} abs={v['max_absdiff']:.3e} "
                  f"rel={v['max_reldiff']:.3e}  rel1e-6={v['declared_at_rel_1e-6']}")
    report["per_metric_declaration"] = per_metric_decl
    report["overall"] = "PASS" if all_pass_abs else "FAIL"
    with open(os.path.join(REC, "comparison_full764.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"[overall, shipped absolute 1e-6] {report['overall']}")


if __name__ == "__main__":
    main()
