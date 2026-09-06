"""R6 独立复算 · 步骤4 全量复算结果与 on-board 基准的数值比对。

比对 pwm_ldct_baselines eval 的复算输出 r6_recalc/<model>_det_full764.json
与作者 onboard 基准 <repo>/results/<model>_results_det_full764.json
逐 seed、逐 dose 比对 psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean，以及 n。

判定容差：路线 (b) 修订（dated 2026-09-06）——GPU 推理路径改为逐指标相对容差 REL_TOL=1e-4。
依据：route (a) 确定性内核重跑已证明复算自身 bit-identical；复算与 onboard 的残留差异为
跨环境 float 系统性偏差（最差 reldiff 6.4e-5），绝对 1e-6 在跨五数量级指标上不可达。
输出：r6_recalc/comparison_full764.json + 控制台摘要
"""
from __future__ import annotations

import json
import os
import sys

MODELS = ["blur", "red_cnn", "learn", "ctformer", "corediff"]
SEEDS = ["42", "2023", "7", "12345", "999"]
DOSES = ["sim_r010", "sim_r025", "sim_r050"]
METRICS = ["psnr", "ssim", "cnr_mean", "cho_auc_mean", "npwe_mean"]
REL_TOL = 1e-4  # 路线 (b)：逐指标相对容差（dated amendment 2026-09-06）

HERE = os.path.dirname(os.path.abspath(__file__))
ONBOARD = os.environ.get(
    "R6_ONBOARD_RESULTS",
    r"D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\results",
)


def main():
    report = {"tolerance": REL_TOL, "tolerance_kind": "relative",
              "criterion_note": "route (b) amendment dated 2026-09-06: GPU inference "
                                "paths compare at per-metric RELATIVE 1e-4; route (a) "
                                "deterministic re-runs proved bit-identical internally",
              "per_model": {}}
    all_pass = True
    for m in MODELS:
        rec = os.path.join(HERE, f"{m}_det_full764.json")
        ob = os.path.join(ONBOARD, f"{m}_results_det_full764.json")
        if not (os.path.isfile(rec) and os.path.isfile(ob)):
            report["per_model"][m] = {"status": "MISSING",
                                      "recalc": os.path.isfile(rec),
                                      "onboard": os.path.isfile(ob)}
            all_pass = False
            continue
        with open(rec, encoding="utf-8") as f:
            rj = json.load(f)
        with open(ob, encoding="utf-8") as f:
            oj = json.load(f)
        diffs = []
        n_checked = 0
        for s in SEEDS:
            if s not in rj.get("per_seed", {}) or s not in oj.get("per_seed", {}):
                diffs.append(f"seed {s}: missing")
                continue
            for d in DOSES:
                rd = rj["per_seed"][s]["per_dose"].get(d, {})
                od = oj["per_seed"][s]["per_dose"].get(d, {})
                for met in METRICS:
                    rv = rd.get(met)
                    if met in ("cnr_mean", "cho_auc_mean", "npwe_mean"):
                        rv = (rd.get("detectability") or {}).get(met)
                        ov = (od.get("detectability") or {}).get(met)
                    else:
                        ov = od.get(met)
                    n_checked += 1
                    if rv is None or ov is None:
                        if rv != ov:
                            diffs.append(f"{m} s{s} {d} {met}: recalc={rv} onboard={ov}")
                        continue
                    rel = abs(float(rv) - float(ov)) / max(abs(float(ov)), 1e-12)
                    if rel > REL_TOL:
                        diff = abs(float(rv) - float(ov))
                        diffs.append(f"{m} s{s} {d} {met}: "
                                     f"recalc={rv:.9g} onboard={ov:.9g} absdiff={diff:.3g} reldiff={rel:.3g}")
        # n 一致性
        for s in SEEDS:
            for d in DOSES:
                rn = rj["per_seed"][s]["per_dose"].get(d, {}).get("n")
                on = oj["per_seed"][s]["per_dose"].get(d, {}).get("n")
                if rn is not None and on is not None and rn != on:
                    diffs.append(f"{m} s{s} {d} n: recalc={rn} onboard={on}")
        ok = len(diffs) == 0
        all_pass = all_pass and ok
        report["per_model"][m] = {"status": "PASS" if ok else "FAIL",
                                  "n_checked": n_checked, "n_diffs": len(diffs),
                                  "diffs": diffs[:50]}
        print(f"[{m}] {'PASS' if ok else 'FAIL'}  checked={n_checked} diffs={len(diffs)}")
        for d in diffs[:10]:
            print("    ", d)
    report["overall"] = "PASS" if all_pass else "FAIL"
    with open(os.path.join(HERE, "comparison_full764.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"[overall] {report['overall']}")


if __name__ == "__main__":
    main()
