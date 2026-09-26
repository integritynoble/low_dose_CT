# 第三方操作者说明（2026-09-25）

> **任务 5（第三环境）交付物 5/5**
> 本说明面向在 **owner 工作站**执行第三环境复算的**非 Agent 第三方操作者**
> （人工操作者），用以强化复算独立性。配套运行手册：
> `THIRD_ENV_RUNBOOK_2026-09-25.md`（自包含命令序列）。

---

## 1. 角色与原则

- 本复算由**第三方人工操作者**在 owner 原生 Linux RTX 5090 工作站上执行，
  不使用任何 Agent 自动化执行，以强化独立性。
- 操作者只负责：环境搭建、数据/权重校验、按手册跑命令、回传结果。**不修改
  任何代码**（尤其 eval.py / observers.py 的计算逻辑）。
- 一切资产（权重/数据）在 **owner 授权后**方可接收（见
  `checkpoint_provenance_license.md` §0）。

---

## 2. 前置条件清单（操作者核对）

| # | 项 | 要求 |
|---|---|---|
| 1 | 硬件 | NVIDIA RTX 5090（Blackwell sm_120），驱动 595.71.05 已装 |
| 2 | OS | Ubuntu 26.04（原生 Linux） |
| 3 | Python | 3.10+（推荐 3.12）已装，可建 venv |
| 4 | 网络 | 可访问 PyPI / download.pytorch.org（安装依赖）；或离线 wheel 包 |
| 5 | 磁盘 | 数据树 + 权重 + 输出 ≥ 若干 GB 空间（LIDC sim 树约数百 MB~GB 级） |
| 6 | 权限 | 仓库访问权（分支 `third-env/blackwell`）+ 资产授权回执 |
| 7 | 时间 | 全量 5 模型预计 **≥ 数十小时量级**（参照 4090：red_cnn 585.4 min、
      ctformer 422.8 min、corediff 1824.1 min；5090 应更快但需实测），
      操作者需预留连续运行窗口 |

---

## 3. 环境核对清单（执行前逐项确认）

1. `git checkout third-env/blackwell` 成功，`git status` 干净（除 WS-4 遗留
   修改外不应有本任务相关改动）。
2. `python -c "import torch; print(torch.__version__, torch.cuda.is_available(),
   torch.cuda.get_device_capability(0))"` → torch ≥2.7.0、cuda_avail=True、
   capability 首元素 ≥12。
3. 数据树 364 项哈希校验 ok=364（手册 §2.2 / `data_manifest_LIDC_AAPM.md` §3）。
4. 5 权重 SHA256 与 `ckpt_hashes.txt` 一致；`task_spec.json` SHA256 =
   `AE7AE799…`。
5. 冒烟：`smoke_blur_seed42.json` 正常产出（3 dose × 764 slices，n=764）。

---

## 4. 执行顺序

1. 按 `THIRD_ENV_RUNBOOK_2026-09-25.md` §1 建 venv 装依赖（路线 A：cu128）。
2. 按 §2 放置并校验数据与权重。
3. 按 §4 冒烟验证。
4. 按 §3 全量命令跑 5 模型（blur / red_cnn / learn / ctformer / corediff），
   输出到 `third_env_run/`，逐模型 `tee` 日志。
5. 记录每模型 wall-clock（`date +%s` 前后差值，或 `time` 包裹命令）。

---

## 5. 结果回传（JSON + log）

回传目录 `third_env_run/` 应包含：

```text
third_env_run/
├── blur_det_full764.json        + blur.log
├── red_cnn_det_full764.json     + red_cnn.log
├── learn_det_full764.json       + learn.log
├── ctformer_det_full764.json    + ctformer.log
├── corediff_det_full764.json    + corediff.log
├── smoke_blur_seed42.json       + smoke.log（可选）
├── env_pip_freeze_third_env.txt      # pip freeze 快照
├── sha256_manifest.txt               # 5 个 JSON + 日志 + freeze 的 SHA256
└── run_notes.md                      # 环境/硬件/驱动/耗时/异常记录
```

`run_notes.md` 模板：

```markdown
# Third-env run notes (2026-09-25 起)
- 硬件: RTX 5090 xN, driver 595.71.05
- OS: Ubuntu 26.04
- venv: .venv_t3, torch <版本>+<cuXXX>, torchvision <版本>
- 分支/commit: third-env/blackwell @ <hash>
- 数据树: <路径>, 校验 ok=364
- 权重: 5 权重 SHA256 与 ckpt_hashes.txt 一致
- task_spec: AE7AE799…
- 耗时: blur=…min red_cnn=…min learn=…min ctformer=…min corediff=…min
- 异常: <无/如实记录>
```

> 回传后由 owner 侧执行比对（`compare_linux_vs_ref.py` 同款判据逻辑）生成
> `comparison_third_env_full764.json`，并附两侧 SHA256 保证基线无歧义。

---

## 6. 与参考 / 第二环境结果的比对方法与判据

- **判据**：per-metric **相对 1e-4**（psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean，
  `n` 精确相等）；shipped 绝对 1e-6 原样保留（跨环境预期 FAIL，不构成真实
  不一致，R6 报告 §10.3 已实证）。
- **参考**：`baselines/results/*_results_det_full764.json`（onboard reference）。
- **第二环境**：R6 复算（Windows 2×RTX 4090）`r6_recalc/results/*_det_full764.json`
  与 Linux rerun（WSL2）`r6_recalc/results/linux_rerun/*_det_full764.json`。
  第三环境结果应：①与 onboard 在相对 1e-4 下一致；②趋势上与第二环境数值一致
  （同属跨环境 float 偏差量级，无需 bit-identical）。
- **判定表述**：见运行手册 §6.3 三行验收口径。
