"""A3 频域检测性复算脚本（detectability-freq-v1，作者随附资产）。

用途：R6 独立复算操作指南 §5「频域检测性复算」的随附脚本。
由独立复算者在自己的环境中运行；不得按 task_spec.json 文字描述自由另写实现，
本脚本与作者产出 aapm_lidc_cross_vendor_spread.json / aapm_per_dose_spread.json
中频域协议使用的实现一致（源自 WS 项目 R6/R3 运行脚本，2026-08-22 正则化修订版）。

协议（task_spec.json -> frequency_domain_detectability, protocol_version=detectability-freq-v1）：
  - 高频带提取：h = img - G(sigma=1.0px)(img)（1-px 高频带）；
  - ROI：find_tissue_roi（HU [10,120] + 低梯度 + 低 std，seed 42，32x32）；
  - 信号位置：find_micro_peak（ROI 外、距边缘 margin=40 的局部极大，远离 tissue ROI）；
  - band_energy_ratio：
        ROI  = ||h(o)_patch||^2 / max(||h(fd)_patch||^2, eps_floor)
        full = ||h(o)||^2 / max(||h(fd)||^2, 1e-9)
        eps_floor = 1e-4 * ||h(fd)||^2_full   （2026-08-22 自适应正则化，
        见 run_lidc_r6 中 GE/Toshiba 近零分母 ROI 的说明；rank 类统计不受影响）
  - tm_auc：模板匹配 AUC（Mann-Whitney 等价），正样本=信号位置模板相关，
        负样本=absent 软组织 patch（tissue ROI 处）。

运行前置（依赖资产 A2 pwm_ldct_loader 与 baselines 包）：
    pip install -e <pwm_ldct_loader 路径>     # 例：D:\\ZHY\\low_dose_CT-heyang\\WS-1_dataset\\pwm_ldct_loader
    pip install -e <baselines 路径>           # baselines 仓库 src 在 PYTHONPATH
    pip install numpy scipy torch pydicom

输入格式：
    全剂量与低剂量均为归一化 [0,1] 的 npy 数组（shape [S, H, W] 或 [1, S, H, W]），
    同一患者 fd/ld 文件名一一对应（默认同名；可用 --suffix-ld 指定低剂量后缀，
    例如 --suffix-ld _r025）。

用法示例（复算 AAPM held-out test，4 患者）：
    python freq_detectability_recalc.py \
        --fd-dir  r6_recalc/data/aapm_test_fd \
        --ld-dir  r6_recalc/data/aapm_test_ld \
        --suffix-ld _r025 \
        --task-json r6_baselines/task_spec.json \
        --device cuda \
        --out r6_recalc/freq_band_energy_aapm_test.json

产出 JSON 结构：
    {
      "schema": "detectability-freq-v1/recalc",
      "protocol": {...},
      "n_patients": N,
      "per_patient": {
         "<pid>": {
            "n_roi": int, "roi_band_energy_ratio": float,
            "band_energy_ratio_full": float, "roi_tm_auc": float,
            "ber_per_slice": [float,...]
         }, ...
      },
      "summary_mean": {"roi_band_energy_ratio": ..., "band_energy_ratio_full": ...,
                       "roi_tm_auc": ...}
    }
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage

# ---- 依赖 baselines / pwm_ldct_loader（资产 A2），如已 pip install 可删下面两行 ----
# sys.path.insert(0, r"D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\src")
# sys.path.insert(0, r"D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pwm_ldct_loader\src")

from pwm_ldct_baselines.observers import (TaskSpec, find_tissue_roi, norm_to_hu,
                                          hu_to_norm, run_model)
from pwm_ldct_baselines.models import get_model

HF_SIGMA = 1.0        # 1-px 高频带高斯核 sigma（detectability-freq-v1）
PATCH = 32            # ROI 尺寸（task_spec: roi 32px）
DET_SLICES = 48       # 每患者采样 slice 数（R6 协议）
MARGIN = 40           # find_micro_peak 边缘 margin


# ---------------------------------------------------------------------------
# 核心算子（与作者 R6 运行脚本逐行一致）
# ---------------------------------------------------------------------------
def highfreq_hu(img_hu):
    """1-px 高频带：h = img - G(sigma=1.0px)(img)。"""
    return img_hu - ndimage.gaussian_filter(img_hu, HF_SIGMA)


def corr2(a, b):
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / denom) if denom > 1e-9 else 0.0


def roc_auc(pres, abss):
    """Mann-Whitney 等价 AUC；正样本=signal 位置，负样本=absent 软组织。"""
    scores = [(s, 1) for s in pres] + [(s, 0) for s in abss]
    scores.sort(key=lambda t: -t[0])
    tp = 0
    fp = 0
    Np = len(pres)
    Na = len(abss)
    auc = 0.0
    prev_tp = 0
    prev_fp = 0
    for s, lab in scores:
        if lab == 1:
            tp += 1
        else:
            fp += 1
            auc += (tp + prev_tp) * (fp - prev_fp) / 2.0
            prev_tp, prev_fp = tp, fp
    auc += (Np + prev_tp) * (Na - prev_fp) / 2.0
    return auc / (Np * Na)


def find_micro_peak(hf, absent_pos, patch_size=PATCH, margin=MARGIN):
    """在 ROI 外找模板匹配的信号峰值位置（远离 tissue ROI 与图像边缘）。"""
    ay, ax = absent_pos
    amp = np.abs(hf)
    peak_mask = amp == ndimage.maximum_filter(amp, size=5)
    ys, xs = np.where(peak_mask)
    order = np.argsort(amp[ys, xs])[::-1]
    for k in order:
        y, x = int(ys[k]), int(xs[k])
        y0, x0 = y - patch_size // 2, x - patch_size // 2
        if y0 < margin or x0 < margin or y0 + patch_size > hf.shape[0] - margin or x0 + patch_size > hf.shape[1] - margin:
            continue
        if abs(y0 - ay) < patch_size and abs(x0 - ax) < patch_size:
            continue
        return (y0, x0)
    return None


def eval_freq_roi(model, ld_n, fd_n, task, device, det_slices=DET_SLICES):
    """逐 slice 计算 ROI BandER / full BandER / tm_auc（含自适应 eps 正则化）。"""
    n = ld_n.shape[0]
    step = max(1, n // det_slices)
    idx = list(range(0, n, step))[:det_slices]
    pres_all, abss_all = [], []
    ber_roi_all, ber_full_all = [], []
    for i in idx:
        fd_hu = norm_to_hu(fd_n[i])
        hf_fd = highfreq_hu(fd_hu)
        abs_pos = find_tissue_roi(fd_n[i], PATCH, task)
        y0, x0 = abs_pos
        st_pos = find_micro_peak(hf_fd, abs_pos, PATCH)
        if st_pos is None:
            continue
        sy, sx = st_pos
        tmpl = hf_fd[sy:sy + PATCH, sx:sx + PATCH]
        x = torch.from_numpy(ld_n[i]).unsqueeze(0).unsqueeze(1).to(device)
        with torch.no_grad():
            out = run_model(model, x).clamp(0, 1)
        out_hu = norm_to_hu(out[0, 0].cpu().numpy())
        o_hf = highfreq_hu(out_hu)
        hf_fd_patch = hf_fd[y0:y0 + PATCH, x0:x0 + PATCH]
        o_hf_patch = o_hf[y0:y0 + PATCH, x0:x0 + PATCH]
        denom_full = float((hf_fd ** 2).sum())
        # BandER 自适应正则化（2026-08-22）：eps = 1e-4 * 全图 FD 高频能量，
        # 见 run_lidc_r6 中近零 ROI 分母的说明；rank 类统计不受影响。
        eps_floor = 1e-4 * denom_full
        denom = float((hf_fd_patch ** 2).sum())
        ber_roi_all.append(float((o_hf_patch ** 2).sum()) / max(denom, eps_floor))
        ber_full_all.append(float((o_hf ** 2).sum()) / max(denom_full, 1e-9))
        pres_all.append(corr2(tmpl, o_hf[sy:sy + PATCH, sx:sx + PATCH]))
        abss_all.append(corr2(tmpl, o_hf[y0:y0 + PATCH, x0:x0 + PATCH]))
    return {
        "n_roi": len(ber_roi_all),
        "roi_band_energy_ratio": float(np.mean(ber_roi_all)) if ber_roi_all else None,
        "band_energy_ratio_full": float(np.mean(ber_full_all)) if ber_full_all else None,
        "roi_tm_auc": float(np.mean(roc_auc(pres_all, abss_all))) if pres_all else None,
        "ber_per_slice": ber_roi_all,
    }


def load_arrays(path):
    """读取 npy（[S,H,W] 或 [1,S,H,W]）为 [S,H,W] float32。"""
    a = np.load(path)
    a = np.asarray(a, dtype=np.float32)
    if a.ndim == 4 and a.shape[0] == 1:
        a = a[0]
    if a.ndim != 3:
        raise ValueError(f"{path}: 期望 [S,H,W] 或 [1,S,H,W]，实际 shape={a.shape}")
    return a


def build_model(model_name, ckpt, device):
    """按权重构建模型；model_name='blur' 时为内置 trap（无需权重）。"""
    if model_name == "blur":
        m = get_model("blur").to(device)
        m.eval()
        return m
    st = torch.load(ckpt, map_location=device)
    m = get_model(st["model"]).to(device)
    m.load_state_dict(st["state_dict"])
    m.eval()
    return m


def main():
    ap = argparse.ArgumentParser(description="detectability-freq-v1 频域检测性复算脚本（资产 A3）")
    ap.add_argument("--fd-dir", required=True, help="全剂量归一化 npy 目录（每患者一文件）")
    ap.add_argument("--ld-dir", required=True, help="低剂量归一化 npy 目录（与 fd 同名配对）")
    ap.add_argument("--suffix-ld", default="", help="低剂量文件名后缀（如 _r025），默认与 fd 同名")
    ap.add_argument("--task-json", default="", help="task_spec.json 路径（用于读取 frequency_domain_detectability 参数，可选）")
    ap.add_argument("--model", default="blur", help="模型名：blur / red_cnn / learn / ctformer / corediff / ctformer_small_retrain")
    ap.add_argument("--checkpoint", default="", help="模型权重路径（blur 可省略）")
    ap.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu")
    ap.add_argument("--det-slices", type=int, default=DET_SLICES)
    ap.add_argument("--out", required=True, help="输出 JSON 路径")
    args = ap.parse_args()

    import torch  # noqa: F401  (局部导入，便于 --help 不依赖 torch)
    t0 = time.time()
    task = TaskSpec()
    if args.task_json and os.path.isfile(args.task_json):
        spec = json.load(open(args.task_json, encoding="utf-8"))
        freq_spec = spec.get("frequency_domain_detectability", {})
        print(f"[protocol] {freq_spec.get('protocol_version', 'detectability-freq-v1')} "
              f"HF_SIGMA={freq_spec.get('hf_sigma', HF_SIGMA)}", flush=True)

    model = build_model(args.model, args.checkpoint or None, args.device)
    print(f"[load] {args.model} on {args.device}", flush=True)

    fd_files = sorted(glob.glob(os.path.join(args.fd_dir, "*.npy")))
    if not fd_files:
        raise SystemExit(f"[error] {args.fd_dir} 下无 npy 文件")
    per_patient = {}
    for fd_fp in fd_files:
        pid = os.path.splitext(os.path.basename(fd_fp))[0]
        ld_fp = os.path.join(args.ld_dir, pid + args.suffix_ld + ".npy")
        if not os.path.isfile(ld_fp):
            # 尝试直接同名
            ld_fp = os.path.join(args.ld_dir, pid + ".npy")
        if not os.path.isfile(ld_fp):
            print(f"[skip] {pid}: 无配对低剂量文件", flush=True)
            continue
        fd_n = load_arrays(fd_fp)
        ld_n = load_arrays(ld_fp)
        if fd_n.shape != ld_n.shape:
            print(f"[skip] {pid}: shape 不匹配 fd={fd_n.shape} ld={ld_n.shape}", flush=True)
            continue
        res = eval_freq_roi(model, ld_n, fd_n, task, args.device, det_slices=args.det_slices)
        per_patient[pid] = res
        print(f"[ok] {pid}: n_roi={res['n_roi']} roi_ber={res['roi_band_energy_ratio']:.4f} "
              f"ber_full={res['band_energy_ratio_full']:.4f} tm_auc={res['roi_tm_auc']:.4f} "
              f"({time.time()-t0:.0f}s)", flush=True)

    if not per_patient:
        raise SystemExit("[error] 无任何患者成功计算")

    def _mean(key):
        vals = [v[key] for v in per_patient.values() if v.get(key) is not None]
        return float(np.mean(vals)) if vals else None

    report = {
        "schema": "detectability-freq-v1/recalc",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model,
        "protocol": {"protocol_version": "detectability-freq-v1", "hf_sigma": HF_SIGMA,
                     "patch": PATCH, "det_slices": args.det_slices,
                     "bander_eps_floor": "1e-4 * full-image FD HF energy (2026-08-22 adaptive)"},
        "n_patients": len(per_patient),
        "per_patient": {pid: {k: v[k] for k in ("n_roi", "roi_band_energy_ratio",
                                                "band_energy_ratio_full", "roi_tm_auc",
                                                "ber_per_slice")}
                        for pid, v in per_patient.items()},
        "summary_mean": {"roi_band_energy_ratio": _mean("roi_band_energy_ratio"),
                         "band_energy_ratio_full": _mean("band_energy_ratio_full"),
                         "roi_tm_auc": _mean("roi_tm_auc")},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("[DONE] wrote", args.out, flush=True)
    print("[SUMMARY]", json.dumps(report["summary_mean"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
