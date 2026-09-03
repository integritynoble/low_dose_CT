"""A4 统计检验复算脚本（作者随附资产）。

用途：R6 独立复算操作指南 §6「统计检验复算」的随附脚本。
复现手稿 R5/R6 段落两个检验的 exact 算法与随机种子；复算者用自己的
复算输出 JSON（相同 schema）作为输入即可，不得自行另写实现。

包含两个子命令：
  vendor-kw       vendor 效应：patient-level permutation Kruskal-Wallis
                  （默认 20000 draws，seed 42），输入 aapm_lidc_cross_vendor_spread.json
                  结构（per_vendor.<vendor>.patients[].models.<m>.freq_roi.roi_band_energy_ratio），
                  LIDC 4 vendor（GE/Philips/Siemens/Toshiba，各 2 患者）。
                  对照声明：p ≈ 0.0103（20000 draws，方向一致）。
  dose-friedman   dose 效应：exact-permutation Friedman（repeated measures，
                  (3!)^4 = 1296 枚举），输入 aapm_dose_detectability.json 结构
                  （per_patient.<pid>.doses.<dose>.models.<m>.freq.roi_band_energy_ratio，
                  dose 序 sim_r010 / real_r025 / sim_r050，4 患者）。
                  对照声明：red_cnn/learn/blur p ≈ 0.0417，ctformer p ≈ 0.1250（3/4 模型显著）。

用法示例：
    python statistical_tests_recalc.py vendor-kw \
        --input r6_recalc/aapm_lidc_cross_vendor_spread.json \
        --models red_cnn,ctformer,learn,blur \
        --n-perm 20000 --seed 42 \
        --out r6_recalc/vendor_perm_kw.json

    python statistical_tests_recalc.py dose-friedman \
        --input r6_recalc/aapm_dose_detectability.json \
        --models red_cnn,ctformer,learn,blur \
        --out r6_recalc/dose_exact_friedman.json

算法与作者运行脚本逐行一致（run_r5_spread.py, 2026-08-22 版本）：
  - permutation_kruskal_wallis：观测 H 统计量，随机重排样本（保持每组样本数），
    统计重排 H >= obs H 的比例，p = (n_ge + 1) / (n_perm + 1)；
  - friedman_exact：观测 Friedman Q 统计量，枚举所有 (k!)^n 个 within-subject
    排列（k=3 dose, n=4 patients -> 1296），p = n_ge / total。
"""
from __future__ import annotations

import argparse
import itertools as it
import json
import random
import sys

MODELS_DEFAULT = ["red_cnn", "ctformer", "learn", "blur"]
VENDOR_ORDER = ["GE", "Philips", "Siemens", "Toshiba"]
DOSE_ORDER = ["sim_r010", "real_r025", "sim_r050"]


# ---------------------------------------------------------------------------
# 核心检验（与作者运行脚本逐行一致）
# ---------------------------------------------------------------------------
def permutation_kruskal_wallis(groups, rng, n_perm=20000):
    """Patient-level permutation Kruskal-Wallis across groups.

    groups: list of lists，每个 list 为一个组内各患者的 ROI BandER（patient 级均值）。
    """
    import scipy.stats as st

    n_groups = len(groups)
    sizes = [len(g) for g in groups]
    allvals = [v for g in groups for v in g]
    H_obs = st.kruskal(*groups).statistic
    n_greater_or_equal = 0
    for _ in range(n_perm):
        rng.shuffle(allvals)
        perm = []
        idx = 0
        for s in sizes:
            perm.append(allvals[idx:idx + s])
            idx += s
        H_perm = st.kruskal(*perm).statistic
        if H_perm >= H_obs:
            n_greater_or_equal += 1
    p = (n_greater_or_equal + 1) / (n_perm + 1)
    return {
        "H": float(H_obs),
        "n_groups": n_groups,
        "n_patients_per_group": sizes,
        "p_value_permutation": p,
        "n_permutations": n_perm,
        "significant_at_0_05": bool(p < 0.05),
    }


def friedman_exact(data):
    """Exact permutation Friedman test for repeated measures.

    data: list of subjects，每个 subject 为 k 个 within-subject 观测
    （此处为 3 个 dose 水平的 ROI BandER）。精确零分布枚举所有 (k!)^n
    个 within-subject 排列（k=3, n=4 -> 1296）。
    """
    k = len(data[0])
    n = len(data)
    perms = list(it.permutations(range(k)))

    def friedman_stat(rows):
        ranks = []
        for row in rows:
            order = sorted(range(k), key=lambda i: row[i])
            r = [0] * k
            for rank_idx, idx in enumerate(order, 1):
                r[idx] = rank_idx
            ranks.append(r)
        R = [sum(r[i] for r in ranks) for i in range(k)]
        return (12.0 / (n * k * (k + 1))) * sum((ri - n * (k + 1) / 2) ** 2 for ri in R)

    obs = friedman_stat(data)
    n_ge = 0
    total = 0
    for combo in it.product(perms, repeat=n):
        rows2 = [[data[si][perm[i]] for i in range(k)]
                 for si, perm in enumerate(combo)]
        if friedman_stat(rows2) >= obs - 1e-12:
            n_ge += 1
        total += 1
    return {
        "H_friedman": float(obs),
        "p_exact_permutation": n_ge / total,
        "n_permutations_enumerated": total,
        "significant_at_0_05": bool((n_ge / total) < 0.05),
    }


# ---------------------------------------------------------------------------
# 输入提取（与作者 spread JSON schema 对齐）
# ---------------------------------------------------------------------------
def extract_vendor_patient_ber(cv_json, model, vendors):
    """从 aapm_lidc_cross_vendor_spread.json 提取各 vendor 的 patient 级 ROI BandER。"""
    groups = []
    group_names = []
    for v in vendors:
        vals = []
        for rec in cv_json.get("per_vendor", {}).get(v, {}).get("patients", []):
            mr = rec.get("models", {}).get(model, {})
            freq = mr.get("freq_roi", {})
            val = freq.get("roi_band_energy_ratio")
            if val is not None and isinstance(val, (int, float)):
                vals.append(float(val))
        if vals:
            groups.append(vals)
            group_names.append(v)
    return group_names, groups


def extract_dose_patient_ber(dd_json, model, doses):
    """从 aapm_dose_detectability.json 提取每患者 3 个 dose 的 ROI BandER。"""
    data = []
    pids = []
    for pid, pp in dd_json.get("per_patient", {}).items():
        row = []
        ok = True
        for d in doses:
            try:
                row.append(float(pp["doses"][d]["models"][model]["freq"]["roi_band_energy_ratio"]))
            except (KeyError, TypeError):
                ok = False
                break
        if ok:
            data.append(row)
            pids.append(pid)
    return pids, data


# ---------------------------------------------------------------------------
def cmd_vendor_kw(args):
    cv = json.load(open(args.input, encoding="utf-8"))
    rng = random.Random(args.seed)
    models = [m.strip() for m in args.models.split(",") if m.strip()] or MODELS_DEFAULT
    vendors = [v.strip() for v in args.vendors.split(",") if v.strip()] or VENDOR_ORDER
    out = {"schema": "vendor-perm-kw/recalc", "test": "patient-level permutation Kruskal-Wallis",
           "n_permutations": args.n_perm, "seed": args.seed, "vendors": vendors,
           "models": {}}
    for m in models:
        names, groups = extract_vendor_patient_ber(cv, m, vendors)
        if len(groups) < 2:
            out["models"][m] = {"status": "skipped", "reason": "vendor 组数不足 2"}
            continue
        out["models"][m] = permutation_kruskal_wallis(groups, rng, n_perm=args.n_perm)
        out["models"][m]["groups"] = names
        res = out["models"][m]
        print(f"[kw {m}] H={res['H']:.4f} p={res['p_value_permutation']:.4f} "
              f"(n_perm={res['n_permutations']}, sig={res['significant_at_0_05']})", flush=True)
    _write(args.out, out)
    print("[DONE] wrote", args.out, flush=True)


def cmd_dose_friedman(args):
    dd = json.load(open(args.input, encoding="utf-8"))
    models = [m.strip() for m in args.models.split(",") if m.strip()] or MODELS_DEFAULT
    doses = [d.strip() for d in args.doses.split(",") if d.strip()] or DOSE_ORDER
    out = {"schema": "dose-exact-friedman/recalc", "test": "exact-permutation Friedman (repeated measures)",
           "doses": doses, "models": {}}
    for m in models:
        pids, data = extract_dose_patient_ber(dd, m, doses)
        if len(data) < 2 or len(data[0]) < 2:
            out["models"][m] = {"status": "skipped", "reason": "患者/剂量数据不足"}
            continue
        out["models"][m] = friedman_exact(data)
        out["models"][m]["n_patients"] = len(pids)
        out["models"][m]["patient_ids"] = pids
        res = out["models"][m]
        print(f"[friedman {m}] Q={res['H_friedman']:.4f} p={res['p_exact_permutation']:.4f} "
              f"(enumerated={res['n_permutations_enumerated']}, sig={res['significant_at_0_05']})", flush=True)
    _write(args.out, out)
    print("[DONE] wrote", args.out, flush=True)


def _write(path, obj):
    import os
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser(description="统计检验复算脚本（资产 A4）：permutation KW / exact Friedman")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("vendor-kw", help="patient-level permutation Kruskal-Wallis（vendor 效应）")
    p1.add_argument("--input", required=True)
    p1.add_argument("--models", default=",".join(MODELS_DEFAULT))
    p1.add_argument("--vendors", default=",".join(VENDOR_ORDER))
    p1.add_argument("--n-perm", type=int, default=20000)
    p1.add_argument("--seed", type=int, default=42)
    p1.add_argument("--out", required=True)

    p2 = sub.add_parser("dose-friedman", help="exact-permutation Friedman（dose 效应）")
    p2.add_argument("--input", required=True)
    p2.add_argument("--models", default=",".join(MODELS_DEFAULT))
    p2.add_argument("--doses", default=",".join(DOSE_ORDER))
    p2.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "vendor-kw":
        cmd_vendor_kw(args)
    elif args.cmd == "dose-friedman":
        cmd_dose_friedman(args)
    else:
        ap.error("unknown command")


if __name__ == "__main__":
    main()
