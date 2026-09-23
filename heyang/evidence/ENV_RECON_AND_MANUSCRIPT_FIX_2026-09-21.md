# ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21

- **日期**：2026-09-21
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，HEAD `3472815`，工作区干净）
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 1（P0 论文包）Agent 侧三项子任务：1.1 环境记录盘点、1.3 数字校准、1.2 解释修正
- **红线遵守**：未修改任何 score / tolerance / artifact / registry 常量；未 commit / 未 push / 未删除任何文件；最小改动（仅 prose）

> **2026-09-21 更新**：owner 澄清——参考环境的确切版本即本地运行环境的完整确切版本记录。
> §1.1-B、§1.2、§6 已按最新事实修订；§3.1 补记 manuscript.tex Methods 与 README.md 的后续改写。
> §2（数字校准）、§3（原始旧→新对照）、§4（grep）、§5（文件汇总）保持首版内容不变。

---

## 1. 环境记录盘点（任务 1.1）

### 1.1 可恢复清单

#### A. 复算（recomputation）环境 — 全部可恢复（R = 文档/日志记录的事实）

来源：`WS-1_dataset/R6_recalc/R6_recalc_report.md` §2、`WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt`、`Heyang-paper/manuscript.tex` Methods、`WS-1_dataset/R6_recalc/compare_full764.py` `ROUTE_A_EVIDENCE` 块。

| 项 | 值 | 来源类型 |
|---|---|---|
| OS | Windows（manuscript Methods "on Windows"）| R |
| GPU | 2× NVIDIA RTX 4090（双 GPU）| R |
| 驱动 | 591.86 | R |
| Python | 3.12.10（venv `.venv_r6`，独立于作者环境）| R |
| PyTorch | 2.3.0+cu121（CUDA 12.1）| R |
| torchvision | 0.18.0+cu121 | R |
| NumPy | 1.26.4 | R |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2024.9.20 | R |
| mkl | 2021.4.0（随 wheels 安装，SHA256 `ceef3caf…` 已校验）| R |
| CPU / RAM | 128 核 / 125 GB | R |
| 依赖冻结 | `env_pip_freeze.txt`（57 行）| R |
| 源码基线 commit | `4875338`（on-board `WS-1_dataset/baselines` 工作树；复算快照 `r6_recalc/r6_baselines/` 6 个关键文件 eval.py/cli.py/observers.py/models/__init__.py/models/ctformer_wrapper.py/train.py SHA256 逐文件 MATCH）| R |
| task_spec 哈希 | `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`（`hashes/task_spec_hash.txt`）| R |
| checkpoint 哈希 | 5 个权重 SHA256（`hashes/ckpt_hashes.txt`：red_cnn.pt=DF775D08… / learn.pt=3EABF525… / ctformer.pt=AEAD0C15… / corediff.pt=41ABA674… / ctformer_small_retrain.pt=78C0C59C…）| R |
| 数据 manifest | LIDC sim 树 364 项（`data_hashes.txt`）、AAPM held-out 树 25 项（`aapm_hashes.txt`）| R |
| 运行命令 | `R6独立复算操作指南.md`（venv 重建 + 各模型 eval 命令 + blur trap 验证）；route(a) 确定性重跑日志 `r6_recalc/routeA_run.log`（red_cnn 585.4min rc=0 / ctformer 422.8min rc=0 / corediff 1824.1min rc=0；2026-09-05 00:21 – 09-06 06:48；内核设置 cudnn.deterministic=True / cudnn.benchmark=False / use_deterministic_algorithms(True) / CUBLAS_WORKSPACE_CONFIG=:4096:8）| R |

#### B. 参考（reference / on-board / 作者）环境 — 完整确切版本记录（owner 2026-09-21 澄清）

| 项 | 值 | 来源类型 |
|---|---|---|
| 权威澄清 | owner 确认：参考环境的确切版本 = 本地运行的版本；以已整理的"项目运行时所有环境"记录作为参考环境的确切记录 | R（owner 澄清）|
| OS | Windows（本地运行环境）| R |
| GPU / 驱动 | 2× NVIDIA RTX 4090 / driver 591.86 | R |
| Python | 3.12.10 | R |
| PyTorch / torchvision | 2.3.0+cu121 / 0.18.0+cu121 | R |
| NumPy | 1.26.4 | R |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2024.9.20 | R |
| mkl | 2021.4.0（SHA256 `ceef3caf…`）| R |
| 依赖冻结 | `env_pip_freeze.txt`（57 行，含 SHA-256 校验的本地 wheel 源）| R |
| 源码基线 commit | `4875338` | R |
| task_spec 哈希 | `AE7AE799…`（`task_spec_hash.txt`）| R |
| checkpoint 哈希 | 5 个权重 SHA256（`ckpt_hashes.txt`：red_cnn=DF775D08… / learn=3EABF525… / ctformer=AEAD0C15… / corediff=41ABA674… / ctformer_small_retrain=78C0C59C…）| R |
| 数据 manifest | LIDC sim 树 364 项（`data_hashes.txt`）、AAPM held-out 树 25 项（`aapm_hashes.txt`）| R |
| 备注 | 首版"与复算环境不同 OS/CUDA build/framework"、"author's environment"、"作者标称容器 tag"等旧记录随 owner 澄清作废，不再作为参考环境描述依据 | — |

### 1.2 不可恢复项（2026-09-21 更新后）

owner 澄清后，参考环境的全部核心版本信息（OS/GPU/驱动/CUDA/cuDNN/Python/PyTorch/NumPy）已可恢复（见 §1.1-B），**原"核心版本不可恢复"结论作废**。Methods 中的局限声明已改写为参考环境确切记录（见 §3.1），README 待办第 1 条已标记 resolved。

仅余以下**非阻塞备注项**（不构成论文局限声明）：

| 项 | 说明 | 建议 |
|---|---|---|
| 原始 onboard 运行命令/脚本日志 | 作者首次运行时的逐条命令未单独留档于仓库（现以项目运行环境记录 + `R6独立复算操作指南.md` 命令体系为准）| 可选：owner 如有历史 shell 记录可补充 |
| ASSET_MANIFEST.md SHA256 栏 | 作者资产清单 SHA256 为空占位（R6_recalc_report §1 步骤 0 核对结论），仅存在性核对 | 建议 owner 补填（历史建议）|
| 参考侧"bit-identical 证明"的独立性 | 复算快照 6 文件 MATCH 出自复算者报告，非独立第三方核验 | 如实标注来源 |

~~参考环境"可能为 Linux + 更早 CUDA 构建"（M 推断）~~：已随 owner 澄清作废，不成立。

---

## 2. 数字校准（任务 1.3）

### 2.1 命令原始输出（Windows 本机执行，`$env:PYTHONUTF8=1`）

**命令 1**：`python Heyang-paper/make_tables.py --check`

```
all tables current
exit=0
```

**命令 2**：`python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`

```
declared criterion (2026-09-12): per metric, R6独立复算操作指南.md §4, revision of 2026-09-12; Director decision 2026-09-11 §2.1 route (b)
  blur      PASS  outside declared: 0  worst: {}
  corediff  PASS  outside declared: 0  worst: {'psnr': '4.22e-07', 'cnr_mean': '2.50e-05', 'npwe_mean': '5.15e-06'}
  ctformer  PASS  outside declared: 0  worst: {'cnr_mean': '4.41e-07', 'npwe_mean': '2.03e-07'}
  learn     PASS  outside declared: 0  worst: {}
  red_cnn   PASS  outside declared: 0  worst: {'psnr': '4.69e-07', 'cnr_mean': '6.36e-05', 'npwe_mean': '3.62e-05'}
overall: PASS
committed verdict matches the re-derivation
exit=0
```

### 2.2 计数结论

- artifact `WS-1_dataset/R6_recalc/results/comparison_full764.json`：每模型 `n_checked = 75`，5 模型 → **375 总比较**。
- 维度核对：SEEDS = 5（42/2023/7/12345/999）× DOSES = 3（sim_r010/sim_r025/sim_r050）× METRICS = 5（psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean）= **75 per method**；5 方法 × 75 = **375 total**。
- manuscript.tex Methods 原 TODO 写"5 methods × 3 dose levels × 5 reported quantities = 75 comparisons per method"：**乘法与 per-method 标签不一致**（把 5 methods 放进 per-method 乘法，75 实际是全局数才为 375）。正确值 = 5 **seeds** × 3 doses × 5 quantities = 75 per method；5 methods × 75 = 375 total。
- **修正**：已将 TODO 替换为正确计数正文（见 §3 M5），与 artifact 一致；`make_tables.py --check` 通过进一步确认生成表与 artifact 一致。
- **未修改**：`comparison_full764.json` 及任何 tolerance/score 常量未改动；`recompare_per_metric.py --check` 为只读复核，未写回。

---

## 3. 解释修正（任务 1.2）— 每处"旧→新"对照

文件：`Heyang-paper/manuscript.tex`（19 处）+ `Heyang-paper/README.md`（6 处）。所有替换均先校验唯一匹配（count==1）后执行。

### manuscript.tex

| # | 位置 | 旧文本（取证） | 新文本 | 理由 |
|---|---|---|---|---|
| M1 | abstract Methods | "the benchmark's **pre-registered criterion**" | "the benchmark's **original declared criterion**" | 无带时间戳预注册证据 → 改称 original declared（任务 1.2d） |
| M2 | abstract Results | "**The determinism hypothesis was falsified**: re-running the same side with deterministic kernels reproduced the original bit-for-bit, **leaving the residual attributable to the environment rather than to kernel non-determinism**. The criterion audit showed that **no absolute tolerance resolves** the comparison" | "Re-running the same side with deterministic kernels reproduced the original bit-for-bit, and **no kernel non-determinism was observed in this environment**. The criterion audit showed that **none of the tested absolute tolerances resolves** the comparison" | 缓和因果断言（同侧重跑只建立该配置下可重复性，不唯一识别成因）；绝对容差结论限定为"所测"范围（任务 1.2a/b） |
| M3 | abstract Conclusions | "loosening it does not repair it" | "**within the range we tested** loosening it does not repair it" | 限定绝对容差失败范围（任务 1.2b） |
| M4 | Introduction | "The **pre-registered** criterion of the benchmark under study" + "the difference **was not caused by the mechanism everyone expects**, and the criterion **could not have been satisfied by any absolute threshold worth declaring**" | "The **original declared** criterion of the benchmark under study" + "**no kernel non-determinism was observed as the cause in this environment**, and **none of the tested absolute thresholds resolved** the comparison" | 同上 a/b/d |
| M5 | Methods §evaluation | TODO: "5 **methods** × 3 dose levels × 5 reported quantities = 75 comparisons per method" | "75 comparisons per method --- **5 seeds** × 3 dose levels × 5 reported quantities --- and 375 in total across the five methods" | 修正计数乘法并解决 TODO（任务 1.3；见 §2.2） |
| M6 | Methods §two environments | TODO "Record the reference environment exactly --- OS, driver, CUDA, torch, numpy … first thing to fix" | "The reference environment was recorded at the time only as ``the author's environment''; its exact operating system, GPU, driver, CUDA/cuDNN, Python, PyTorch and NumPy versions **were not preserved … could not be recovered for this submission**. This limitation is stated explicitly … **no new independent reproduction of the reference run is claimed**" | 环境盘点结论落盘为 Methods 局限声明（任务 1.1；禁止声称新独立复现） |
| M7 | Methods §determinism | "This hypothesis is testable and it makes a **sharp prediction** … and any residual against the reference **must therefore come from somewhere else**" | "This hypothesis is testable: … and any residual … observed under that configuration **would not be attributable to kernel non-determinism in this environment**" | 缓和"必须来自别处"的过度因果（任务 1.2a） |
| M8 | Methods §determinism | "the three methods **outside the pre-registered criterion**" | "outside the **original declared** criterion" | 任务 1.2d |
| M9 | Results §Agreement | "Under the **pre-registered** absolute criterion, 115 of 375" | "Under the **original declared** absolute criterion, 115 of 375" | 任务 1.2d |
| M10 | Results 表 caption | "under the **pre-registered** absolute $10^{-6}$ criterion" | "under the **original declared** absolute $10^{-6}$ criterion" | 任务 1.2d |
| M11 | Results 表 caption 尾 | "That two methods reproduce exactly **establishes** … so the differences in the other three **are a property of those computations rather than of the harness**" | "That two methods reproduce exactly, together with the route-(a) rerun … **shows** … are capable of bit-identical reproduction **under this configuration**; in this environment the differences in the other three **were not observed to depend on kernel non-determinism**" | 缓和因果断言并限定于该配置（任务 1.2a） |
| M12 | Results 子节标题 | "The determinism hypothesis **is false here**" | "**No kernel non-determinism was observed in this environment**" | 缓和（任务 1.2a） |
| M13 | Results 正文 | "The prediction … **failed** … The evaluation path was **not sensitive to kernel non-determinism** … the difference against the reference **is** a systematic cross-environment offset" | "The prediction … **was not supported in this environment** … **No kernel non-determinism was observed in this environment** … the difference … **is treated as** a systematic cross-environment offset" | 缓和 + 以观察级表述（任务 1.2a） |
| M14 | Results 子节标题 | "**No absolute tolerance** resolves the comparison" | "**None of the tested absolute tolerances** resolves the comparison" | 限定所测范围（任务 1.2b） |
| M15 | Results §ladder | "The **pre-registered** criterion fails at $10^{-6}$" + "Loosening … changes **nothing**, because" | "The **original declared** criterion fails at $10^{-6}$" + "changes nothing **within the range tested**, because" | 任务 1.2b/d |
| M16 | Results 表 caption | "An absolute criterion **cannot be repaired** by loosening it; only changing its kind **resolves** the comparison" | "**None of the absolute criteria tested** is repaired by loosening it; only changing its kind resolved the comparison **among the criteria tested**" | 限定所测范围（任务 1.2b） |
| M17 | Results §ladder | "the **pre-registered** criterion was not unattainable" | "the **original declared** criterion was not unattainable" | 任务 1.2d |
| M18 | Discussion §finding | "stated as a **falsifiable** prediction; the prediction was tested at real cost and **falsified**" + "the superseded criterion and its verdict were retained verbatim beside the new one" | "stated as a **testable** prediction; the prediction was tested at real cost, and **no kernel non-determinism was observed in this environment**" + "was amended **retrospectively, after the mismatch had been observed** … **The per-metric amendment is therefore a retrospective adjustment based on the observed differences, not an independent or prospective validation of the amended tolerance**" | 缓和 falsified + 明确 retrospective、保留原始失败、不声称独立/前瞻验证（任务 1.2a/c） |
| M19 | Conclusions | "fails its **pre-registered** criterion" + "the **mechanism usually blamed was absent**" | "fails its **original declared** criterion" + "**no kernel non-determinism was observed in this environment**" | 任务 1.2a/d |

### README.md

| # | 位置 | 旧文本 | 新文本 | 理由 |
|---|---|---|---|---|
| R1 | Key findings | "A **pre-registered** absolute agreement criterion of $10^{-6}$" | "An **originally declared** absolute agreement criterion of $10^{-6}$" | 任务 1.2d |
| R2 | Key findings 1 | "**The usual explanation is false here.** … stated as a **falsifiable** prediction … so kernel non-determinism **is not the cause** and the residual **is** a cross-environment offset" | "**No kernel non-determinism was observed in this environment.** … stated as a **testable** prediction … so **no kernel non-determinism was observed here**; the residual **is treated as** a cross-environment offset" | 缓和因果断言（任务 1.2a） |
| R3 | Key findings 2 | "**No absolute tolerance** resolves it." | "**None of the tested absolute tolerances** resolves it." | 限定所测范围（任务 1.2b） |
| R4 | What is left 1 | "**Record the reference environment exactly** … **This is the first thing to fix.**" | "**Reference environment recorded only partially.** … could not be recovered; the Methods section states this limitation explicitly, and the owner has been asked for the records." | 环境盘点结论同步（任务 1.1） |
| R5 | What is left 5 | "Confirm the per-method comparison count …" | "Per-method comparison count **confirmed** against the artifact: 75 per method (5 seeds × 3 dose levels × 5 reported quantities), 375 total." | 计数校准完成（任务 1.3） |
| R6 | Files 表 | "Seven `\todo{}` markers remain" | "Five `\todo{}` markers remain" | TODO 数由 7 → 5（M5/M6 已解决） |

### 3.1 后续变更（2026-09-21，owner 澄清"参考环境=本地运行环境"后）

| 文件 | 位置 | §3 首轮结果（前文）| 后续新文 | 理由 |
|---|---|---|---|---|
| `manuscript.tex` | Methods §The two environments（§3 M6 区域）| M6 首轮新文为局限声明："...could not be recovered for this submission. This limitation is stated explicitly..." | 改写为参考环境确切记录："The reference environment, in which the original results were produced, is the local run environment... Windows with two NVIDIA RTX 4090 GPUs (driver 591.86), Python 3.12.10, PyTorch 2.3.0+cu121 (torchvision 0.18.0+cu121), NumPy 1.26.4, SciPy 1.13.1, scikit-image 0.23.2, tifffile 2024.9.20 and mkl 2021.4.0. The complete 57-line dependency freeze... `WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt`... source baseline is pinned at commit `4875338`." | owner 澄清：参考环境=本地运行环境的完整确切版本记录，推翻首轮"不可恢复"判断 |
| `README.md` | What is left 第 1 条（§3 R4 区域）| R4 首轮新文为"Reference environment recorded only partially... owner has been asked for the records" | 改为 "Reference environment recorded (resolved). ... 57-line dependency freeze ... source baseline `4875338`. The Methods section now records the reference environment as the local run environment instead of a limitation." | 同步 owner 澄清，标记 resolved |

---

## 4. grep 复核结果

命令：`Get-ChildItem Heyang-paper -Recurse -Include *.tex,*.md,*.py | Select-String -Pattern "pre-registered","falsified","is false here","not the cause","no absolute tolerance","residual attributable","mechanism usually blamed"`

- **0 命中**于 manuscript.tex / README.md 等 prose 文件。
- 唯一残留：`Heyang-paper/make_tables.py:46` docstring "differences under the pre-registered criterion"（**代码注释，不在任务 1.2 的 prose 修改范围**；修改表格生成器违反最小改动红线，故保留。依据：任务书仅要求修正 manuscript.tex 及含同类表述的 README.md，且红线禁止修改 artifact/registry 相关代码）。
- "original declared" 在 Heyang-paper（tex/md）出现 9 次 ✓。
- manuscript.tex 剩余 `\todo{}` = 5（author 元数据、第三环境决策、data/code 可用性、CRediT、competing interests）✓。

---

## 5. 变更文件汇总（未 commit / 未 push / 未删除）

| 文件 | 改动 |
|---|---|
| `D:\ZHY\low_dose_CT-heyang\Heyang-paper\manuscript.tex` | 19 处 prose 修改（291 行） |
| `D:\ZHY\low_dose_CT-heyang\Heyang-paper\README.md` | 6 处 prose 修改 |

**未改动**：`WS-1_dataset/R6_recalc/results/comparison_full764.json`、`WS-1_dataset/R6_recalc/recompare_per_metric.py`、`WS-1_dataset/R6_recalc/tolerance_audit.py`、`Heyang-paper/make_tables.py`（含其常量/注释）及任何 score/tolerance/registry 常量。

## 6. 需 owner 提供/决策

1. ~~参考环境记录~~（已闭环）：owner 已于 2026-09-21 澄清参考环境=本地运行环境的完整确切版本记录（Windows / 2×RTX 4090 驱动 591.86 / Python 3.12.10 / PyTorch 2.3.0+cu121 / NumPy 1.26.4 / 57 行 freeze / 源码基线 `4875338` / task_spec 与权重与数据哈希），Methods 与 README 已同步，本条不再需要 owner 提供。
   - **新增待决（作者决策）**：Abstract Methods 段 "in a separate environment differing in operating system, CUDA build, and deep-learning framework version" 及 Methods 第三段 "a different library stack tests whether..." 与"参考环境=本地运行环境"存在张力，需作者确认是否同步（涉及论文核心跨环境叙事，Agent 侧未擅自修改）。
2. ASSET_MANIFEST.md SHA256 栏补填（历史建议，R6_recalc_report §8 反馈②）。
3. 其余作者专属字段（author order/ORCID/CRediT 等）不在本任务范围。
