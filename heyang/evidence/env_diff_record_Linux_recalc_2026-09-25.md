---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_de20598ab88211f1b24b525400ea19b7
    ReservedCode1: XzNK7ASGGpuSAPf0yRG1nd9jGvTgiv/ThkCtOU/QTEMf18hXMYpfcmUh+tX9FC1k+gNU3d+uZrM5dDQ6cmkwLWNBc+LAydBvb++015Wyx6VqA0WmrQWe4HjaVOucQ0tl/OQho7MrGiw4VCo8xDohYuYh6G3gxHdNXmgkKFrzs7FrH1N9n0bmF0KqWAg=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_de20598ab88211f1b24b525400ea19b7
    ReservedCode2: XzNK7ASGGpuSAPf0yRG1nd9jGvTgiv/ThkCtOU/QTEMf18hXMYpfcmUh+tX9FC1k+gNU3d+uZrM5dDQ6cmkwLWNBc+LAydBvb++015Wyx6VqA0WmrQWe4HjaVOucQ0tl/OQho7MrGiw4VCo8xDohYuYh6G3gxHdNXmgkKFrzs7FrH1N9n0bmF0KqWAg=
---

# 真实环境差异记录 — 供论文摘要三轴补来源

- 日期：2026-09-25
- 用途：HEYANG_NEXT 任务1（环境表 vs 论文主张）方案 B 的证据材料——为摘要 "in a separate environment differing in operating system, CUDA build, and deep-learning framework version" 的三轴提供可引用的真实记录（版本号/命令/日期），维持跨环境叙事
- 记录等级：R（文档/日志/实测事实）

---

## 1. 参考环境（原始结果产生侧）

来源：owner 2026-09-21 澄清（ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md §1.1-B）、`WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt`（57 行）、manuscript.tex Methods。

| 项 | 值 | 来源 |
|---|---|---|
| OS | Windows（本地运行环境） | R |
| GPU / 驱动 | 2× NVIDIA RTX 4090 / 591.86 | R |
| Python | 3.12.10 | R |
| PyTorch / torchvision | 2.3.0+cu121（CUDA 12.1）/ 0.18.0+cu121 | R |
| NumPy | 1.26.4 | R |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2024.9.20 | R |
| mkl | 2021.4.0（SHA256 已校验） | R |
| 依赖冻结 | 57 行 `env_pip_freeze.txt` | R |
| 源码基线 | commit `4875338` | R |
| 哈希 | task_spec `AE7AE799…`、5 权重 SHA256、数据 manifest 364+25 项 | R |
| 澄清日期 | 2026-09-21（owner） | R |

---

## 2. Linux 独立复现环境（真实跨环境记录，2026-09-23/24 实测）

来源：WSL Ubuntu 实测（`/etc/os-release`、`.venv_r6/bin/pip freeze`、`nvidia-smi`、`python -c torch 查询`）、运行日志 `~/r6_recalc_linux/r6_out/*.log`、比对报告 `linux_vs_windows_full764_comparison.json`。

| 项 | 值 | 来源 |
|---|---|---|
| OS | Ubuntu 24.04.3 LTS（WSL2，内核 6.6.87.2-microsoft-standard-WSL2） | R |
| GPU / 驱动 | 2× NVIDIA RTX 4090（WSL 透传）/ 591.86（与 Windows 共享） | R |
| Python | 3.12.3（独立 venv `.venv_r6`） | R |
| PyTorch / torchvision | 2.3.0+cu121（CUDA 12.1，cuDNN 8.9.2.26 via nvidia-cudnn-cu12）/ 0.18.0+cu121 | R |
| NumPy | 1.26.4 | R |
| scipy / scikit-image / pydicom / timm / einops | 1.13.1 / 0.23.2 / 3.0.2 / 1.0.29 / 0.8.2 | R |
| tifffile / pytest | 2026.3.3 / 9.1.1 | R |
| 包安装 | editable `git+https://github.com/integritynoble/low_dose_CT.git@b0686eb`（pwm_ldct_baselines 0.5.0 / pwm_ldct_loader） | R |
| 数据 | `~/r6_recalc_linux/data`（364 文件 / 24G，`manifest.sha256` 校验） | R |
| 权重 | `repo_local/WS-1_dataset/baselines/checkpoints`（与参考侧相同 5 权重） | R |
| 运行命令 | `run_full.sh`（nohup 启动 5 模型 eval，含 PYTHONPATH 导出；脚本后清理，日志留存） | R |
| 运行日期 | smoke 09-23 15:32 → blur 09-23 17:24 → ctformer 09-23 19:41 → learn 09-23 21:26 → red_cnn 09-24 08:28 → corediff 09-24 21:04（完成） | R |
| 结果 | 5 模型 × 5 seed × 3 dose × 5 指标 = 375 项比对全部 PASS（reldiff ≤ 1.5e-5，容差 1e-4） | R |

---

## 3. 摘要三轴差异评估

摘要原文："in a separate environment differing in **operating system, CUDA build, and deep-learning framework version**"

| 轴 | 参考（Windows） | Linux 复现（WSL2） | 是否真实不同 | 可引记录 |
|---|---|---|---|---|
| operating system | Windows | Ubuntu 24.04.3 LTS | ✅ 真实不同 | §1 vs §2，R |
| CUDA build | cu121（Windows wheel） | cu121 标称 + 平台特定 Linux wheel / nvidia-cudnn-cu12 8.9.2.26 / WSL 驱动透传 | ⚠️ 标称版本相同，平台构建与运行时（cuDNN 打包、驱动透传）不同 | §2 实测，R |
| DL framework version | PyTorch 2.3.0+cu121 | PyTorch 2.3.0+cu121 | ❌ 名义版本相同 | §1 vs §2，R |

结论：
- **OS 轴**：有真实记录支撑，可直接补来源。
- **CUDA / framework 轴**：名义版本（cu121、torch 2.3.0）相同；真实差异在平台特定构建（Windows/Linux wheel、cuDNN 打包、驱动透传）而非版本号。维持原文三轴字面断言需调整措辞。

---

## 4. 维持跨环境叙事的措辞建议

方案 B 成立（有真实跨 OS 记录），但三轴字面需与记录一致：

- **建议 A（最小改动，保留 "separate environment" 框架）**：
  "recomputed by an independent operator in a separate environment — Linux (Ubuntu 24.04 LTS) instead of Windows, with platform-specific CUDA/cuDNN/driver builds at the same nominal PyTorch 2.3.0+cu121 stack — from checkpoints and data verified by hash."

- **建议 B（保留三轴结构、如实标注）**：
  "in a separate environment differing in operating system (Windows vs Linux) and platform-specific CUDA build (cuDNN 8.9.2.26 Linux wheel vs Windows wheel), at the same nominal deep-learning framework version (PyTorch 2.3.0+cu121)"

- **建议 C（若坚持三轴版本号全不同）**：需在 RTX 5090 / torch 2.13.0+cu130 Linux 工作站上运行论文实验（当前为"第三环境"候选、论文实验未在其上运行，且数据/权重迁移受 deposit 约束），或补充作者原始运行的其他环境记录——目前无此记录。

推荐 A 或 B：OS 差异为真实、可引用、可复现，跨环境叙事完整保留；CUDA/framework 两轴如实表述为平台构建差异，避免评审以"版本号相同却断言不同"为由质疑。

---

## 5. 附：Linux 复现 vs 参考/Windows 基线一致性（支撑 reproducibility 叙事）

| 模型 | max reldiff | 说明 |
|---|---|---|
| blur | 3.4e-16 | 近逐位一致 |
| red_cnn | 0 | 逐位一致 |
| learn | 1.4e-16 | 近逐位一致 |
| ctformer | 4.4e-07 | 远低于 1e-4 |
| corediff | 1.5e-05 | 远低于 1e-4（worst: cnr_mean 1.5e-5 / npwe_mean 2.0e-6） |

375 项全部 PASS（相对容差 1e-4），可并入论文 Results 或 Supplementary 作为跨 OS 独立复算一致的证据。
*（内容由AI生成，仅供参考）*
