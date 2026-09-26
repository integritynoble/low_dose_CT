# CLAIM_EVIDENCE — paper claim-to-evidence ledger

- **日期**：2026-09-22（本台账创建日）
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，HEAD `66e4758`；台账本体经 commit `d140b71` 提交后，仓库又推进 `04fb541`→`9448610`→`66e4758`）
- **依据**：`heyang/HEYANG_NEXT_2026-09-21.md` 第 2 步
- **范围**：为 manuscript/README 每个关键 abstract/result/conclusion 声明列出 manuscript 位置、支撑 artifact 与字段、可复跑命令、允许解释与局限
- **红线**：本台账为新增文件；未修改任何 artifact / manuscript / README / 常量（工作区既有未提交改动保持原样）
- **来源类型约定**：R = 已落盘/已记录事实（artifact 字段、日志、提交、报告记录）；M = 操作者回忆/当时解释（引用时标注出处，不作为独立证据）；UNRESOLVED = 缺失证据，禁止推断填充

---

## 0. 六项覆盖索引

| 任务书项 | 本台账位置 |
|---|---|
| ① 原始绝对判据失败与保留的失败结果 | §1 |
| ② 同侧重跑测了什么（不唯一归因参考失配原因） | §2 |
| ③ 测试容差阶梯（不推广"无绝对容差可行"） | §3 |
| ④ 修正后 per-metric PASS 日期与追溯性 | §4 |
| ⑤ 比较计数按方法/种子/剂量/指标推导 | §5 |
| ⑥ 两环境已知字段日志来源与显式 UNRESOLVED | §6、§8 |

---

## 1. 原始绝对判据失败与保留的失败结果

> **2026-09-26 更新（任务1收尾）**：本节记录的是 **Windows 历史复算侧**（earlier same-OS recomputation）的失败证据，保留未删除。论文当前数字以 **Linux vs 参考** 为准：manuscript abstract Results 现为 "failed for two of five methods (RED-CNN, CoreDiff)"（`manuscript.tex` L45-46）、Results Agreement "90 of 375 comparisons differed. The blur control, LEARN and CTformer reproduced within the criterion …; RED-CNN and CoreDiff did not"（L202-205）；来源见 §6.2 与 `results/comparison_linux_full764.json`。本节的 115/375 与三方法失败是 Windows 侧历史记录，不再作为论文数字引用。

**声明（历史侧）**：Windows 历史 artifact 记录：原判据下三方法（RED-CNN、CTformer、CoreDiff）失败、115/375 不同。manuscript 在 2026-09-26 前曾引用该计数（L43-47、L190-191）；已改写为 Linux vs 参考数字。

| 项 | 证据 |
|---|---|
| Artifact | `WS-1_dataset/R6_recalc/results/comparison_full764.json` → `shipped_criterion_superseded` 块：`kind=absolute`、`tolerance=1e-06`、`overall=FAIL`、`per_model_status={blur: PASS, red_cnn: FAIL, learn: PASS, ctformer: FAIL, corediff: FAIL}`、`note` 声明原判据与原判定 verbatim 保留 |
| Artifact | 同文件 `per_model.*.n_checked=75`、`n_diffs={blur:0, red_cnn:45, learn:0, ctformer:25, corediff:45}`（合计 115；Windows 历史侧）。Linux vs 参考新 artifact `comparison_linux_full764.json` 为 `n_diffs={blur:0, red_cnn:45, learn:0, ctformer:0, corediff:45}`（合计 90） |
| Artifact | `Heyang-paper/tables/agreement.tex`：当前（Linux vs 参考）Blur 75/0、LEARN 75/0、CTformer 75/0、RED-CNN 75/45、CoreDiff 75/45（abs. $10^{-6}$ 列）；2026-09-22 历史版 CTformer 为 75/25（Windows 侧）；由 `make_tables.py` 从 `comparison_linux_full764.json` 生成 |
| 命令 | `python Heyang-paper/make_tables.py --check` → `all tables current`, exit=0（2026-09-22 复跑） |
| 允许解释 | 失败事实、失败方法集合、115/375 计数均可由 artifact 直接核对 |
| 局限 | "failed" 是就 shipped absolute 1e-6 判据而言的失败；不是"不可复现"的失败。原失败判定 `shipped_criterion_superseded` 与修正后判据**并存保留**，未删除或改写 |

---

## 2. 同侧重跑（route (a)）测了什么

> **2026-09-26 更新（任务1收尾）**：route (a) 是 **earlier Windows same-OS recomputation（2026-09-05/06）** 的实验；manuscript 引用处均已加此归属（abstract Results L46-47、Methods determinism L176-180、Results L229-233）。Linux 独立复算侧不做 route (a)，直接与参考比较（`comparison_linux_full764.json`）。

**声明**：manuscript Results "Re-running the recomputation side with deterministic kernels reproduced the non-deterministic run exactly: zero differing comparisons, bit-identical. This ablation was performed during the earlier Windows same-OS recomputation (2026-09-05/06), and no kernel non-determinism was observed in that environment … the difference against the reference is treated as a systematic cross-environment offset"（L225-233）；abstract Results 同义（L45-48）。

| 项 | 证据 |
|---|---|
| Artifact | `comparison_full764.json` → `routeA_rerun_evidence`：`result="deterministic re-run vs non-deterministic re-run of the SAME side: n_diffs = 0, bit-identical"`；`how_run.flags=[cudnn.deterministic=True, cudnn.benchmark=False, torch.use_deterministic_algorithms(True), CUBLAS_WORKSPACE_CONFIG=:4096:8]`、`models=[red_cnn, ctformer, corediff]`、`cost=~48 GPU-hours`；`recorded_from="DIRECTOR_DECISIONS.md 2.1, decision of 2026-09-11; issue #5"`；`do_not_overwrite` 说明该块是修正可辩护性的关键 |
| Artifact | `WS-1_dataset/R6_recalc/R6_recalc_report.md` §10.1（L220-248）：route (a) 执行记录表 red_cnn 585.4 min rc=0 / ctformer 422.8 min rc=0 / corediff 1824.1 min rc=0，内核设置同左；§10.2 比对 A 同侧 n_diffs=0、比对 B 跨侧仍 FAIL（red_cnn 45 / ctformer 25 / corediff 45） |
| Artifact | route (a) 重跑产物 `WS-1_dataset/R6_recalc/results/{red_cnn,ctformer,corediff}_det_full764.json`（rc=0、json 完整） |
| 日志 | 原始运行日志在复算工作目录 `r6_recalc/routeA_run.log`（**仓库外**，仓库内未提交；`R6_recalc_report.md` L246 记录了该位置声明） |
| 命令 | 复跑比对为只读：`python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`（exit=0，见 §4） |
| 允许解释 | 该实验**只建立**：复算环境该 eval 管线对 cuDNN 内核非确定性不敏感、同一侧在确定性内核下可逐位复现 |
| 局限 | **不唯一归因参考失配原因**。`R6_recalc_report.md` L222-228 integration note 明确："a same-side no-difference rerun does not uniquely establish the cause of a reference mismatch"。§10.3 的因果解释是操作者当时解释（M），非独立证据。`DIRECTOR_DECISIONS.md` §2.1（L82-88）将残余定性为 systematic cross-environment offset，属裁定结论而非直接测量 |
| 未测试 | blur/learn 未重跑（原复算已与 onboard bit-identical，`R6_recalc_report.md` L247） |

---

## 3. 测试的容差阶梯

> **2026-09-26 更新（任务1收尾）**：本节 Windows 历史阶梯保留（abs 各级 3 方法失败）；论文当前数字用 **Linux vs 参考** 阶梯：`comparison_linux_full764.json` → `tolerance_audit.ladder` 8 级中 `absdiff@1e-06..1e-03` 全部 FAIL（failing=[red_cnn, corediff]，**CTformer 退出**）；`reldiff@1e-06/1e-05` FAIL（[red_cnn, corediff]）；`reldiff@1e-04/1e-03` PASS（[]）。manuscript 阶梯正文（L238-248）与 `tables/ladder.tex` 已按此更新。

**声明**：manuscript "None of the tested absolute tolerances resolves the comparison"（L238-241、表 caption L250-254）；abstract "none of the tested absolute tolerances resolves the comparison --- it fails at $10^{-6}$ and equally at $10^{-3}$"（L48-50）；"within the range we tested loosening it does not repair it"（L56-57）。

| 项 | 证据 |
|---|---|
| Artifact | `comparison_full764.json`（Windows 历史）→ `per_metric_declaration.ladder_from_the_committed_diffs`（8 级）：`absdiff@1e-06..1e-03` 全部 FAIL（failing=[corediff, ctformer, red_cnn]）；`reldiff@1e-06/1e-05` FAIL（[corediff, red_cnn]）；`reldiff@1e-04/1e-03` PASS（[]） |
| Artifact | `comparison_linux_full764.json`（Linux vs 参考，论文数字）→ `tolerance_audit.ladder` 同构 8 级：`absdiff@1e-06..1e-03` FAIL（failing=[red_cnn, corediff]）；`reldiff@1e-06/1e-05` FAIL（[red_cnn, corediff]）；`reldiff@1e-04/1e-03` PASS（[]） |
| Artifact | `Heyang-paper/tables/ladder.tex`：与 `comparison_linux_full764.json` 逐行一致（Absolute 1e-6/1e-5/1e-4/1e-3 FAIL × 2 methods；Relative 1e-6/1e-5 FAIL × 2；Relative 1e-4/1e-3 PASS） |
| Artifact | 同文件 `tolerance_audit` 块：`finding` 说明指标跨 5 个数量级（cnr_mean ~5、npwe_mean ~1.56e5、worst 9.7e5），绝对 1e-6 对 npwe_mean 是 ~1e-12 相对要求；`unresolved` 说明未改变原判定 |
| 命令 | `python Heyang-paper/make_tables.py --check`（exit=0）；阶梯原始数据源 `WS-1_dataset/R6_recalc/tolerance_audit.py`（已落盘 `tolerance_audit` 块，本台账未重跑该脚本） |
| 允许解释 | 结论限于**所测集合**：absolute 1e-6/1e-5/1e-4/1e-3 与 relative 1e-6/1e-5/1e-4/1e-3 |
| 局限 | **不得推广为"无绝对容差可行"**（任务书项 ③ 红字）：未测更宽绝对容差、未测其他判据形态（如混合/按指标绝对）。"not unattainable" 方向有独立证据：`manuscript.tex` L259-261（764 项 float64 归约 ~1e-13 相对误差，绝对 1e-6 预算内舒适）支撑"判据错类型而非过严"的解读 |

---

## 4. 修正后 per-metric PASS：日期与追溯性

> **2026-09-26 更新（任务1收尾）**：本节基于 **Windows 历史 artifact** 的 rel 重推导。**校验脚本分工**：Windows 历史 artifact（`comparison_full764.json`）→ `recompare_per_metric.py --check`（验证保留证据，应仍 PASS）；Linux 新 artifact（`comparison_linux_full764.json`）→ `compare_linux_vs_ref.py --check`（重算一致性，abs/rel 双判据均在比较器内生成）。新 artifact 的 `per_model.status` 保留为 abs 判定，勿用 `recompare_per_metric.py` 直接校验（会误报 MISMATCH）。

**声明**：manuscript Discussion "the per-metric amendment is therefore a retrospective adjustment based on the observed differences, not an independent or prospective validation of the amended tolerance"（L291-292）；"The criterion failed … only then was the criterion amended retrospectively, after the mismatch had been observed"（L286-289）；abstract Results "A relative criterion at $10^{-4}$, declared per metric … admits every method, with a worst observed relative difference of $6.36\times10^{-5}$"（L52-53）。

| 项 | 证据 |
|---|---|
| Artifact | `comparison_full764.json` → `criterion`：`declared_on="2026-09-12"`、`declared_in="R6独立复算操作指南.md §4, revision of 2026-09-12; Director decision 2026-09-11 §2.1 route (b)"`、`per_metric`：psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean 均 `{kind: relative, tol: 1e-4}`、`n` `{kind: absolute, tol: 0.0}`、`derived_by="R6_recalc/recompare_per_metric.py"` |
| Artifact | 同文件 `per_metric_declaration`：`declared_on=2026-09-12`；`why_the_old_criterion_misfired` 给出具体反例（ctformer 在最差相对 4.41e-07 时因 npwe_mean 绝对差 0.0335 被判 FAIL → 判据单位缺陷而非模型事实） |
| 复跑 | 2026-09-22 复跑 `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`：5 方法全部 PASS、`outside declared: 0`、`overall: PASS`、`committed verdict matches the re-derivation`、exit=0 |
| 追溯性 | `shipped_criterion_superseded.note`（保留原判据 verbatim）+ `routeA_rerun_evidence` 构成"先失败→再检验→后修正"链；`DIRECTOR_DECISIONS.md` §2.1（L98-99）裁定 route (b) 并要求两个证据块保持原样 |
| 允许解释 | per-metric PASS 是 **2026-09-12 声明判据**下的结论；2026-09-22 复核确认已落盘判定与重推导一致 |
| 局限 | 该修正**不是独立或前瞻验证**（manuscript L291-292 已声明）；是观察失配后对判据的追溯调整。pre-registration 时间戳证据不存在，故全文用 "original declared criterion" 而非 "pre-registered"（修正记录见 [ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](../heyang/evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md) §3 M1/M4/M8-M10/M15/M17/M19 与 README R1） |

---

## 5. 比较计数：按方法/种子/剂量/指标推导

**声明**：manuscript Methods "75 comparisons per method --- 5 seeds × 3 dose levels × 5 reported quantities --- and 375 in total across the five methods"（L91-93）；Results（Linux vs 参考）"90 of 375 comparisons differed"（L202-203）。Windows 历史侧原为 115（见 §1，保留未删除）。

| 项 | 证据 |
|---|---|
| 维度常量 | `WS-1_dataset/R6_recalc/compare_full764.py`：`SEEDS=["42","2023","7","12345","999"]`（5）、`DOSES=["sim_r010","sim_r025","sim_r050"]`（3）、`METRICS=["psnr","ssim","cnr_mean","cho_auc_mean","npwe_mean"]`（5）→ 5×3×5 = 75 per method |
| 计数 | `comparison_full764.json`（Windows 历史）→ `per_model.*.n_checked=75`，5 方法 × 75 = **375 total**；`per_model.*.n_diffs` 之和 = 0+45+0+25+45 = **115**。`comparison_linux_full764.json`（Linux vs 参考，论文数字）→ `n_diffs` 之和 = 0+45+0+0+45 = **90** |
| 交叉核验 | `Heyang-paper/tables/agreement.tex` 每方法 "Comparisons = 75" 列（当前由 `comparison_linux_full764.json` 生成）；`make_tables.py --check` exit=0 确认生成表与 artifact 一致 |
| 旧 TODO 替换 | manuscript 原 TODO "5 methods × 3 dose levels × 5 reported quantities = 75 comparisons per method"（乘法把 5 methods 误放 per-method）已替换为上述正确推导（[ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](../heyang/evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md) §2.2 / §3 M5）；README R5 同步 |
| 允许解释 | 75/375/90/115 均可由常量与 JSON 字段逐项复算 |
| 局限 | 计数是"被检查的比较项数"，不等于"差异项数"（后者按判据不同为 0/25/45 级）；115 是 Windows 历史侧 shipped absolute 1e-6 下的差异项数，90 是 Linux vs 参考下同判据的差异项数，非 per-metric 修正后值（修正后 outside declared 均为 0） |

---

## 6. 两个计算环境

> 更新（2026-09-25，任务1收尾）：manuscript 叙事已按决策采用方案 A —— recomputation 侧以 2026-09-23/24 的 Linux（WSL Ubuntu）独立复算为准（见 §6.2），与本机 Windows 参考侧构成真实跨 OS。原 §6.1 的 Windows 复算保留为历史证据侧（route (a) 确定性重跑与容差阶梯的证据均出自该侧）。
>
> 更新（2026-09-26，任务1收尾）：Linux 输出/日志已入仓（`results/linux_rerun/`，5 JSON + 5 log + `linux_pip_freeze.txt`，U10 关闭），新增 **Linux vs 参考** artifact `results/comparison_linux_full764.json`（abs 1e-6 下 90/375 差异、rel 1e-4 全 PASS、基线命名+哈希），论文全部数字改由此 artifact 支撑（§1/§3/§5/§7）。

### 6.1 本机 Windows 复算（历史证据侧；route (a) 与容差阶梯的证据来源）— 字段全部 R

| 字段 | 值 | 日志/artifact 来源 |
|---|---|---|
| OS | Windows | `manuscript.tex` L112-116；`R6_recalc_report.md` §2 |
| GPU | 2× NVIDIA RTX 4090 | 同上；`R6_recalc_report.md` §10.1（cuda:0/cuda:1） |
| 驱动 | 591.86 | `manuscript.tex` L113 |
| Python | 3.12.10 | `manuscript.tex` L117；`env_pip_freeze.txt` 内 `python` 版本由 venv 重建记录（R6独立复算操作指南.md） |
| PyTorch | 2.3.0+cu121 | `manuscript.tex` L117；freeze 内 torch 行 |
| torchvision | 0.18.0+cu121 | `manuscript.tex` L117 |
| NumPy | 1.26.4 | `manuscript.tex` L117-118；freeze |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2024.9.20 | `manuscript.tex` L118 |
| mkl | 2021.4.0（SHA256 校验 wheel） | `env_pip_freeze.txt`（mkl @ file://…sha256=ceef3caf…） |
| 依赖冻结 | 57 行 | `WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt` |
| 源码基线 | commit `4875338` | `manuscript.tex` L120；freeze 内 `-e git+…@4875338…` |
| task_spec | SHA256 `AE7AE799…` | `hashes/task_spec_hash.txt` |
| checkpoints | 5 权重 SHA256（red_cnn=DF775D08…/learn=3EABF525…/ctformer=AEAD0C15…/corediff=41ABA674…/ctformer_small_retrain=78C0C59C…） | `hashes/ckpt_hashes.txt` |
| 数据 manifest | LIDC sim 364 项 / AAPM held-out 25 项 | `hashes/data_hashes.txt`、`hashes/aapm_hashes.txt`；`manuscript.tex` L164 |
| route (a) 内核设置/耗时 | cudnn.deterministic=True 等 4 项；585.4/422.8/1824.1 min rc=0 | `R6_recalc_report.md` §10.1（L240-245） |

### 6.2 Linux 独立复算（2026-09-23/24，论文叙事 recomputation 侧）— 字段全部 R

| 字段 | 值 | 日志/artifact 来源 |
|---|---|---|
| OS | Ubuntu 24.04.3 LTS（WSL2，内核 6.6.87.2-microsoft-standard-WSL2） | `evidence/env_diff_record_Linux_recalc_2026-09-25.md` §2（`/etc/os-release` 实测） |
| GPU / 驱动 | 2× NVIDIA RTX 4090（WSL passthrough）/ 591.86 | 同上（`nvidia-smi`） |
| Python | 3.12.3（独立 venv `.venv_r6`） | 同上（`pip freeze`） |
| PyTorch / torchvision | 2.3.0+cu121 / 0.18.0+cu121 | 同上 |
| cuDNN | 8.9.2.26（nvidia-cudnn-cu12） | 同上 |
| NumPy | 1.26.4 | 同上 |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2026.3.3 | 同上 |
| 包安装 | editable `git+https://github.com/integritynoble/low_dose_CT.git@b0686eb` | 同上（`.venv_r6/bin/pip freeze`） |
| 数据 / 权重 | `~/r6_recalc_linux/data`（364 文件 / 24G，manifest.sha256 校验）；checkpoints 同参考侧 5 权重 | 同上 §2 |
| 运行记录 | smoke 09-23 15:32 → blur 09-23 17:24 → ctformer 09-23 19:41 → learn 09-23 21:26 → red_cnn 09-24 08:28 → corediff 09-24 21:04；日志 5 个 `*.log` 已入仓 `results/linux_rerun/`（2026-09-26，U10 关闭） | 同上 §2；`results/linux_rerun/*.log` |
| 比对结果（跨 OS 一致性，保留） | 5 模型 × 75 = 375 项比对全部 PASS（rel 容差 1e-4，worst reldiff 1.5e-5）；blur 3.4e-16 / red_cnn 0 / learn 1.4e-16 / ctformer 4.4e-07 / corediff 1.5e-05 | `evidence/linux_vs_windows_full764_comparison.json`；`manuscript.tex` tab:env caption |
| 比对结果（**Linux vs 参考，论文数字**） | abs 1e-6 下 90/375 差异（RED-CNN 45 / CoreDiff 45；**CTformer 翻转通过**，worst abs 2.9e-11）；rel 1e-4 per-metric 全 PASS（outside=0，worst reldiff 6.36e-5 CNR）；RED-CNN 数字与 Windows 侧一致（45 / 34.26 / 6.36e-5）；基线命名+哈希见 artifact | `results/comparison_linux_full764.json`；`results/linux_rerun/`（5 JSON + 5 log + `linux_pip_freeze.txt`，SHA-256 见 `git show <提交>:…` 或仓内记录） |

### 6.3 参考（reference）环境 — 身份裁定 R、独立记录 UNRESOLVED

| 项 | 状态 | 依据 |
|---|---|---|
| 身份裁定 | R：owner 裁定参考环境 = 本地运行环境（"the reference environment, in which the original results were produced, is the local run environment"） | `manuscript.tex` L115-116；`README.md` L54-59 |
| 版本字段 | R（以本地 project-runtime record 填充）：Windows / 2×RTX 4090 / 591.86 / Py3.12.10 / torch2.3.0+cu121 / numpy1.26.4 等 | `manuscript.tex` L116-121；`README.md` L54-57 |
| 作者原始运行时独立记录 | **UNRESOLVED**：无原始 pip freeze / nvidia-smi 存档 / 容器 tag 确证文件 | 仓库全仓 grep 无；[ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](../heyang/evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md) §1.2 |
| 作者标称容器 tag | M（标称非确证）：`pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime` | `R6_recalc_report.md` §2 记录为"作者标称" |
| ASSET_MANIFEST.md SHA256 栏 | UNRESOLVED：空占位，仅存在性核对 | `R6_recalc_report.md` §1 步骤 0 |
| 参考侧 bit-identical 证明独立性 | UNRESOLVED：复算快照 6 文件 MATCH 出自复算者报告，非独立第三方核验 | [ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](../heyang/evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md) §1.2 |

---

## 7. 中央声明 → 证据总表

| # | 声明（位置） | 支撑 artifact 与字段 | 命令 |
|---|---|---|---|
| C1 | 5 方法、764 slices、3 剂量、独立操作者复算（abstract Methods L37） | `compare_full764.py` DOSES/METRICS；`data_hashes.txt`（364）；`ckpt_hashes.txt`；`manuscript.tex` L109-112；[2026-09-26 更新] Linux 复算侧输出/日志入仓 `results/linux_rerun/`（5 JSON + 5 log + `linux_pip_freeze.txt`），摘要失败计数归属 Linux vs 参考（`comparison_linux_full764.json`） | `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`；`python WS-1_dataset/R6_recalc/compare_linux_vs_ref.py --check` |
| C2 | 原始声明判据为 absolute 1e-6（abstract Methods L37-38；L69） | `comparison_full764.json` `tolerance=1e-06`、`shipped_criterion_superseded.kind=absolute`；`comparison_linux_full764.json` 同构 | 同 C1 |
| C3 | 原判据下三方法失败、115/375 不同（L43、L190-191） | `shipped_criterion_superseded.per_model_status`；`per_model.*.n_diffs`（115）；`tables/agreement.tex` | `make_tables.py --check` |
| C3' | **[2026-09-26 更新]** 原判据下两方法失败、90/375 不同（abstract L45-46、Results L202-203，论文当前数字） | `comparison_linux_full764.json` → `per_model.*.n_diffs`（blur 0 / red_cnn 45 / learn 0 / ctformer 0 / corediff 45 = 90）；`tables/agreement.tex`（当前） | `python WS-1_dataset/R6_recalc/compare_linux_vs_ref.py --check`；`make_tables.py --check` |
| C4 | 同侧重跑逐位一致、无内核非确定性（L45-47、L229-233） | `routeA_rerun_evidence.result`；`R6_recalc_report.md` §10.2 比对 A；[2026-09-26 更新] route (a) 明确为 **earlier Windows same-OS recomputation（2026-09-05/06）**，manuscript 已加归属；Linux 侧跨 OS 一致性另见 `evidence/linux_vs_windows_full764_comparison.json`（blur 3.4e-16 / red_cnn 0 / learn 1.4e-16 / ctformer 4.4e-07 / corediff 1.5e-05）；Linux vs 参考下 CTformer 亦逐位一致（worst abs 2.9e-11，`comparison_linux_full764.json`） | 只读复核同 C1 |
| C5 | 所测绝对容差均不解决（L52-53、L238-241） | [2026-09-26 更新] `comparison_linux_full764.json` → `tolerance_audit.ladder`（8 级，abs 各级 FAIL=[red_cnn,corediff]、rel@1e-6/1e-5 FAIL=[red_cnn,corediff]、rel@1e-4/1e-3 PASS=[]）；`tables/ladder.tex`（当前由 Linux artifact 生成）；Windows 历史阶梯 `ladder_from_the_committed_diffs` 保留 | `make_tables.py --check`；`python WS-1_dataset/R6_recalc/compare_linux_vs_ref.py --check` |
| C6 | 相对 1e-4 每指标声明通过全部方法、worst 6.36e-5（L52-53） | `criterion.per_metric`；`per_metric_declaration`；`recompare_per_metric.py --check` 输出；[2026-09-26 更新] `comparison_linux_full764.json` 同判据 outside=0、worst reldiff 6.36e-5（RED-CNN CNR） | 同 C1 |
| C7 | 修正为追溯性调整、非独立验证（L288-292） | `criterion.declared_on=2026-09-12`；`shipped_criterion_superseded.note`；`routeA_rerun_evidence.do_not_overwrite`；`DIRECTOR_DECISIONS.md` §2.1 | — |
| C8 | 75/方法、375 总计（L91-93） | `SEEDS/DOSES/METRICS` 常量；`per_model.*.n_checked=75` | — |
| C9 | 原判据"非不可达"、是错类型（L259-263） | `tolerance_audit.finding`（764 项 float64 ~1e-13 相对） | — |
| C10 | 两环境、参考环境=本地运行环境、复算侧=Linux（L105-157，tab:env 两列对照） | `env_pip_freeze.txt`（57 行）；`ckpt_hashes.txt`；`data_hashes.txt`/`aapm_hashes.txt`；README L54-59；[2026-09-25 更新] `evidence/env_diff_record_Linux_recalc_2026-09-25.md`（参考侧/Linux 侧字段实测）、`evidence/linux_vs_windows_full764_comparison.json`、tab:env（Windows 参考 / Linux 复算两列）；[2026-09-26 更新] Linux 输出/日志入仓 `results/linux_rerun/`（U10 关闭）、`results/comparison_linux_full764.json`（Linux vs 参考） | — |
| C11 | 第一复现尝试的 checkpoint 换用事件（L264-274） | `R6_recalc_report.md`（provenance 事件记录）；hash 级 pinning | — |
| C12 | 结论：失败判据是调查起点、按指标声明（L310-315） | 上述 C1-C11 全链；[2026-09-26 更新] Linux vs 参考下 90/375 @ abs 1e-6、375/375 PASS @ rel 1e-4（`comparison_linux_full764.json`），作为可复现性结论的直接数字；跨 OS 一致性另见 `evidence/linux_vs_windows_full764_comparison.json` | — |

---

## 8. UNRESOLVED 清单

### 任务1决策记录（2026-09-25，HEYANG_NEXT_2026-09-22 任务1收尾；2026-09-26 增补）

**Owner decision, 2026-09-25（Claude Code session on the Linux workstation, relayed in HEYANG_NEXT_2026-09-25.md）**：逐字引述：

> "keep the cross-environment framing"

统一称呼 **cross-environment kept**（不用方案字母）。**The Linux run is the paper's recomputation.** 该引述同时复制进回复索引 `heyang/HEYANG_REPLY_2026-09-20.md`（2026-09-26 更新）。

**决策执行**：recomputation 侧采用 2026-09-23/24 Linux（WSL Ubuntu 24.04.3 LTS）独立复算记录；摘要 Methods 改写为 "Linux (Ubuntu 24.04 LTS) instead of Windows, with platform-specific CUDA/cuDNN builds at the same nominal PyTorch 2.3.0+cu121 stack"（**driver 已删**，两侧驱动同为 591.86）；Methods 复算环境改为 Ubuntu/WSL2/Python 3.12.3/cuDNN 8.9.2.26；tab:env 为 Windows 参考 / Linux 复算两列对照。未削弱环境表、未恢复 pre-registration 框架。

**依据（R）**：`evidence/env_diff_record_Linux_recalc_2026-09-25.md`（参考侧字段 + Linux 侧实测：`/etc/os-release`、`.venv_r6/bin/pip freeze`、`nvidia-smi`、运行日志）；`evidence/linux_vs_windows_full764_comparison.json`（375/375 PASS @ rel 1e-4，worst reldiff 1.5e-5）；[2026-09-26] `results/linux_rerun/`（5 JSON + 5 log + freeze 入仓）与 `results/comparison_linux_full764.json`（Linux vs 参考：90/375 @ abs 1e-6、375/375 @ rel 1e-4）。

**完成标准核对**：无未经证据支持的跨环境断言 ✅（OS 轴真实不同有 R 记录；CUDA/framework 两轴如实表述为平台特定构建差异，未断言版本号不同）；ledger 记录决策依据 ✅（本行）；§7 已标 C1/C3'/C4/C10/C12 ✅。

**局限（2026-09-26 关闭）**：① ~~absolute 1e-6 失败集（115/375）、route (a) 逐位复现与容差阶梯的证据来自本机 Windows 复算，Linux 比对仅覆盖 rel 1e-4 判据——abstract Results 的失败计数不归属 Linux 复算侧~~ → **已关闭**：2026-09-26 完成 Linux vs 参考重比较（`compare_linux_vs_ref.py`，abs/rel 双判据 + 阶梯 + 基线命名/哈希），论文数字全部归属 Linux 复算侧（90/375、CTformer 翻转通过、RED-CNN/CoreDiff 失败）；② ~~Linux 侧原始日志与 5 个 `*_det_full764.json` 在 WSL（仓库外）~~ → **已关闭**：2026-09-26 已入仓 `results/linux_rerun/`（见 U10）。

| # | 项 | 缺失内容 | 影响声明 |
|---|---|---|---|
| U1 | 参考环境独立版本记录 | 作者原始运行时的 OS 具体版本 / GPU 型号数量 / 驱动 / CUDA/cuDNN / Python/PyTorch/NumPy 的独立记录（pip freeze / nvidia-smi / 容器 tag 确证）；[2026-09-25] 跨环境主张已由 Linux 复算侧 R 记录支撑（`evidence/env_diff_record_Linux_recalc_2026-09-25.md`），此处仍指参考侧（作者原始运行环境）独立存档缺失 | C10 的"参考侧独立确证"部分 |
| U2 | ASSET_MANIFEST.md SHA256 栏 | 空占位，无数值级比对 | 资产清单数值核对 |
| U3 | 参考侧 bit-identical 独立性 | 6 文件 MATCH 出自复算者报告，非独立第三方核验 | C4/C7 的独立性表述 |
| U4 | routeA_run.log 原始日志 | 在仓库外复算工作目录（`r6_recalc/routeA_run.log`），仓库内未提交 | C4 日志级证据 |
| U5 | 第三环境 | 未做实验（`manuscript.tex` L303-304 已改为 "a third environment is planned; its results are not reported here"；规划见任务 5） | 跨环境系统性未知（L299-304） |
| U6 | pre-registration 时间戳证据 | 不存在 → 全文用 "original declared criterion" | C2/C6 的"声明判据"而非"预注册" |
| U7 | 作者元数据 | author order / affiliations / ORCIDs / corresponding author（L23 TODO） | 投稿就绪 |
| U8 | CRediT / competing interests | L319/L327 TODO | 投稿就绪 |
| U9 | data/code 可用性措辞 | L319 TODO，依赖公开释放决策 | 投稿就绪 |
| U10 | Linux 复算原始日志/逐模型输出 | **[2026-09-26 关闭]** 已入仓 `WS-1_dataset/R6_recalc/results/linux_rerun/`（5 个 `*_det_full764.json` + 5 个 `*.log` + `linux_pip_freeze.txt`，SHA-256 记录于入仓提交）；新 artifact `results/comparison_linux_full764.json`（Linux vs 参考） | C1/C10 的 Linux 侧原始日志级证据（已闭合） |

---

## 9. 台账生成时的复跑记录（2026-09-22，Windows 本机，`$env:PYTHONUTF8=1`）

```text
> python Heyang-paper/make_tables.py --check
all tables current
exit=0

> python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check
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

未修改任何 artifact / manuscript / README；本台账为新增文件（`?? Heyang-paper/CLAIM_EVIDENCE.md`），未 commit（提交属任务书第 3 步范围）。

## 9b. 2026-09-26 复跑记录（Linux vs 参考，任务1收尾）

```text
> python WS-1_dataset/R6_recalc/compare_linux_vs_ref.py --check
comparison_linux_full764.json: all fields reproducible, artifact current
blur      0 diffs  PASS (abs 1e-6)
red_cnn   45 diffs FAIL (worst abs 34.26, worst rel 6.36e-5)
learn     0 diffs  PASS
ctformer  0 diffs  PASS (worst abs 2.9e-11)
corediff  45 diffs FAIL (worst abs 6.37, worst rel 1.39e-5)
overall: 90/375 diffs under original abs 1e-6; rel 1e-4 per-metric PASS (outside=0)
exit=0

> python Heyang-paper/make_tables.py --check
all tables current
exit=0
```

Linux 复算输出/日志入仓：`WS-1_dataset/R6_recalc/results/linux_rerun/`（5 JSON + 5 log + `linux_pip_freeze.txt`，U10 关闭）。
