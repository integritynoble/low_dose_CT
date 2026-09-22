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

**声明**：manuscript abstract Results "The original declared criterion failed for three of five methods"（`manuscript.tex` L43-47）；Results Agreement "Under the original declared absolute criterion, 115 of 375 comparisons differed. The blur control and LEARN reproduced bit-for-bit; RED-CNN, CTformer [and CoreDiff] …"（L190-191）。

| 项 | 证据 |
|---|---|
| Artifact | `WS-1_dataset/R6_recalc/results/comparison_full764.json` → `shipped_criterion_superseded` 块：`kind=absolute`、`tolerance=1e-06`、`overall=FAIL`、`per_model_status={blur: PASS, red_cnn: FAIL, learn: PASS, ctformer: FAIL, corediff: FAIL}`、`note` 声明原判据与原判定 verbatim 保留 |
| Artifact | 同文件 `per_model.*.n_checked=75`、`n_diffs={blur:0, red_cnn:45, learn:0, ctformer:25, corediff:45}`（合计 115 = L162 的 115 之直接来源） |
| Artifact | `Heyang-paper/tables/agreement.tex`：Blur 75/0、LEARN 75/0、CTformer 75/25、RED-CNN 75/45、CoreDiff 75/45（abs. $10^{-6}$ 列）；由 `make_tables.py` 从上述 JSON 生成 |
| 命令 | `python Heyang-paper/make_tables.py --check` → `all tables current`, exit=0（2026-09-22 复跑） |
| 允许解释 | 失败事实、失败方法集合、115/375 计数均可由 artifact 直接核对 |
| 局限 | "failed" 是就 shipped absolute 1e-6 判据而言的失败；不是"不可复现"的失败。原失败判定 `shipped_criterion_superseded` 与修正后判据**并存保留**，未删除或改写 |

---

## 2. 同侧重跑（route (a)）测了什么

**声明**：manuscript Results "Re-running the recomputation side with deterministic kernels reproduced the non-deterministic run exactly: zero differing comparisons, bit-identical. No kernel non-determinism was observed in this environment … the difference against the reference is treated as a systematic cross-environment offset"（L213-217）；abstract Results 同义（L44-45）。

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

**声明**：manuscript "None of the tested absolute tolerances resolves the comparison"（L223-230、表 caption L238-240）；abstract "none of the tested absolute tolerances resolves the comparison --- it fails at $10^{-6}$ and equally at $10^{-3}$"（L45-47）；"within the range we tested loosening it does not repair it"（L53）。

| 项 | 证据 |
|---|---|
| Artifact | `comparison_full764.json` → `per_metric_declaration.ladder_from_the_committed_diffs`（8 级）：`absdiff@1e-06..1e-03` 全部 FAIL（failing=[corediff, ctformer, red_cnn]）；`reldiff@1e-06/1e-05` FAIL（[corediff, red_cnn]）；`reldiff@1e-04/1e-03` PASS（[]） |
| Artifact | `Heyang-paper/tables/ladder.tex`：与上逐行一致（Absolute 1e-6/1e-5/1e-4/1e-3 FAIL × 3 methods；Relative 1e-6/1e-5 FAIL × 2；Relative 1e-4/1e-3 PASS） |
| Artifact | 同文件 `tolerance_audit` 块：`finding` 说明指标跨 5 个数量级（cnr_mean ~5、npwe_mean ~1.56e5、worst 9.7e5），绝对 1e-6 对 npwe_mean 是 ~1e-12 相对要求；`unresolved` 说明未改变原判定 |
| 命令 | `python Heyang-paper/make_tables.py --check`（exit=0）；阶梯原始数据源 `WS-1_dataset/R6_recalc/tolerance_audit.py`（已落盘 `tolerance_audit` 块，本台账未重跑该脚本） |
| 允许解释 | 结论限于**所测集合**：absolute 1e-6/1e-5/1e-4/1e-3 与 relative 1e-6/1e-5/1e-4/1e-3 |
| 局限 | **不得推广为"无绝对容差可行"**（任务书项 ③ 红字）：未测更宽绝对容差、未测其他判据形态（如混合/按指标绝对）。"not unattainable" 方向有独立证据：`manuscript.tex` L244-247（764 项 float64 归约 ~1e-13 相对误差，绝对 1e-6 预算内舒适）支撑"判据错类型而非过严"的解读 |

---

## 4. 修正后 per-metric PASS：日期与追溯性

**声明**：manuscript Discussion "the per-metric amendment is therefore a retrospective adjustment based on the observed differences, not an independent or prospective validation of the amended tolerance"（L275-277）；"The criterion failed … only then was the criterion amended retrospectively, after the mismatch had been observed"（L271-274）；abstract Results "A relative criterion at $10^{-4}$, declared per metric … admits every method, with a worst observed relative difference of $6.36\times10^{-5}$"（L48-50）。

| 项 | 证据 |
|---|---|
| Artifact | `comparison_full764.json` → `criterion`：`declared_on="2026-09-12"`、`declared_in="R6独立复算操作指南.md §4, revision of 2026-09-12; Director decision 2026-09-11 §2.1 route (b)"`、`per_metric`：psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean 均 `{kind: relative, tol: 1e-4}`、`n` `{kind: absolute, tol: 0.0}`、`derived_by="R6_recalc/recompare_per_metric.py"` |
| Artifact | 同文件 `per_metric_declaration`：`declared_on=2026-09-12`；`why_the_old_criterion_misfired` 给出具体反例（ctformer 在最差相对 4.41e-07 时因 npwe_mean 绝对差 0.0335 被判 FAIL → 判据单位缺陷而非模型事实） |
| 复跑 | 2026-09-22 复跑 `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`：5 方法全部 PASS、`outside declared: 0`、`overall: PASS`、`committed verdict matches the re-derivation`、exit=0 |
| 追溯性 | `shipped_criterion_superseded.note`（保留原判据 verbatim）+ `routeA_rerun_evidence` 构成"先失败→再检验→后修正"链；`DIRECTOR_DECISIONS.md` §2.1（L98-99）裁定 route (b) 并要求两个证据块保持原样 |
| 允许解释 | per-metric PASS 是 **2026-09-12 声明判据**下的结论；2026-09-22 复核确认已落盘判定与重推导一致 |
| 局限 | 该修正**不是独立或前瞻验证**（manuscript L275-277 已声明）；是观察失配后对判据的追溯调整。pre-registration 时间戳证据不存在，故全文用 "original declared criterion" 而非 "pre-registered"（修正记录见 ENV_RECON §3 M1/M4/M8-M10/M15/M17/M19 与 README R1） |

---

## 5. 比较计数：按方法/种子/剂量/指标推导

**声明**：manuscript Methods "75 comparisons per method --- 5 seeds × 3 dose levels × 5 reported quantities --- and 375 in total across the five methods"（L88-89）；Results "115 of 375 comparisons differed"（L190-191）。

| 项 | 证据 |
|---|---|
| 维度常量 | `WS-1_dataset/R6_recalc/compare_full764.py`：`SEEDS=["42","2023","7","12345","999"]`（5）、`DOSES=["sim_r010","sim_r025","sim_r050"]`（3）、`METRICS=["psnr","ssim","cnr_mean","cho_auc_mean","npwe_mean"]`（5）→ 5×3×5 = 75 per method |
| 计数 | `comparison_full764.json` → `per_model.*.n_checked=75`，5 方法 × 75 = **375 total**；`per_model.*.n_diffs` 之和 = 0+45+0+25+45 = **115**（原始判据下） |
| 交叉核验 | `Heyang-paper/tables/agreement.tex` 每方法 "Comparisons = 75" 列；`make_tables.py --check` exit=0 确认生成表与 artifact 一致 |
| 旧 TODO 替换 | manuscript 原 TODO "5 methods × 3 dose levels × 5 reported quantities = 75 comparisons per method"（乘法把 5 methods 误放 per-method）已替换为上述正确推导（ENV_RECON §2.2 / §3 M5）；README R5 同步 |
| 允许解释 | 75/375/115 均可由常量与 JSON 字段逐项复算 |
| 局限 | 计数是"被检查的比较项数"，不等于"差异项数"（后者按判据不同为 0/25/45 级）；115 是 shipped absolute 1e-6 下的差异项数，非 per-metric 修正后值（修正后 outside declared 均为 0） |

---

## 6. 两个计算环境

### 6.1 复算（recomputation）环境 — 字段全部 R

| 字段 | 值 | 日志/artifact 来源 |
|---|---|---|
| OS | Windows | `manuscript.tex` L109-110；`R6_recalc_report.md` §2 |
| GPU | 2× NVIDIA RTX 4090 | 同上；`R6_recalc_report.md` §10.1（cuda:0/cuda:1） |
| 驱动 | 591.86 | `manuscript.tex` L110 |
| Python | 3.12.10 | `manuscript.tex` L109；`env_pip_freeze.txt` 内 `python` 版本由 venv 重建记录（R6独立复算操作指南.md） |
| PyTorch | 2.3.0+cu121 | `manuscript.tex` L109；freeze 内 torch 行 |
| torchvision | 0.18.0+cu121 | `manuscript.tex` L113 |
| NumPy | 1.26.4 | `manuscript.tex` L110、L113；freeze |
| scipy / scikit-image / tifffile | 1.13.1 / 0.23.2 / 2024.9.20 | `manuscript.tex` L114 |
| mkl | 2021.4.0（SHA256 校验 wheel） | `env_pip_freeze.txt`（mkl @ file://…sha256=ceef3caf…） |
| 依赖冻结 | 57 行 | `WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt` |
| 源码基线 | commit `4875338` | `manuscript.tex` L117；freeze 内 `-e git+…@4875338…` |
| task_spec | SHA256 `AE7AE799…` | `hashes/task_spec_hash.txt` |
| checkpoints | 5 权重 SHA256（red_cnn=DF775D08…/learn=3EABF525…/ctformer=AEAD0C15…/corediff=41ABA674…/ctformer_small_retrain=78C0C59C…） | `hashes/ckpt_hashes.txt` |
| 数据 manifest | LIDC sim 364 项 / AAPM held-out 25 项 | `hashes/data_hashes.txt`、`hashes/aapm_hashes.txt`；`manuscript.tex` L155 |
| route (a) 内核设置/耗时 | cudnn.deterministic=True 等 4 项；585.4/422.8/1824.1 min rc=0 | `R6_recalc_report.md` §10.1（L240-245） |

### 6.2 参考（reference）环境 — 身份裁定 R、独立记录 UNRESOLVED

| 项 | 状态 | 依据 |
|---|---|---|
| 身份裁定 | R：owner 裁定参考环境 = 本地运行环境（"the reference environment, in which the original results were produced, is the local run environment"） | `manuscript.tex` L110-111；`README.md` L54-59 |
| 版本字段 | R（以本地 project-runtime record 填充）：Windows / 2×RTX 4090 / 591.86 / Py3.12.10 / torch2.3.0+cu121 / numpy1.26.4 等 | `manuscript.tex` L111-117；`README.md` L54-57 |
| 作者原始运行时独立记录 | **UNRESOLVED**：无原始 pip freeze / nvidia-smi 存档 / 容器 tag 确证文件 | 仓库全仓 grep 无；ENV_RECON §1.2 |
| 作者标称容器 tag | M（标称非确证）：`pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime` | `R6_recalc_report.md` §2 记录为"作者标称" |
| ASSET_MANIFEST.md SHA256 栏 | UNRESOLVED：空占位，仅存在性核对 | `R6_recalc_report.md` §1 步骤 0 |
| 参考侧 bit-identical 证明独立性 | UNRESOLVED：复算快照 6 文件 MATCH 出自复算者报告，非独立第三方核验 | ENV_RECON §1.2 |

---

## 7. 中央声明 → 证据总表

| # | 声明（位置） | 支撑 artifact 与字段 | 命令 |
|---|---|---|---|
| C1 | 5 方法、764 slices、3 剂量、独立操作者复算（abstract Methods L34-41） | `compare_full764.py` DOSES/METRICS；`data_hashes.txt`（364）；`ckpt_hashes.txt`；`manuscript.tex` L107-109 | `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` |
| C2 | 原始声明判据为 absolute 1e-6（abstract Methods L37-38；L69） | `comparison_full764.json` `tolerance=1e-06`、`shipped_criterion_superseded.kind=absolute` | 同 C1 |
| C3 | 原判据下三方法失败、115/375 不同（L43、L190-191） | `shipped_criterion_superseded.per_model_status`；`per_model.*.n_diffs`（115）；`tables/agreement.tex` | `make_tables.py --check` |
| C4 | 同侧重跑逐位一致、无内核非确定性（L44-45、L213-217） | `routeA_rerun_evidence.result`；`R6_recalc_report.md` §10.2 比对 A | 只读复核同 C1 |
| C5 | 所测绝对容差均不解决（L45-47、L223-230） | `ladder_from_the_committed_diffs`（8 级）；`tables/ladder.tex` | `make_tables.py --check` |
| C6 | 相对 1e-4 每指标声明通过全部方法、worst 6.36e-5（L48-50） | `criterion.per_metric`；`per_metric_declaration`；`recompare_per_metric.py --check` 输出 | 同 C1 |
| C7 | 修正为追溯性调整、非独立验证（L271-277） | `criterion.declared_on=2026-09-12`；`shipped_criterion_superseded.note`；`routeA_rerun_evidence.do_not_overwrite`；`DIRECTOR_DECISIONS.md` §2.1 | — |
| C8 | 75/方法、375 总计（L88-89） | `SEEDS/DOSES/METRICS` 常量；`per_model.*.n_checked=75` | — |
| C9 | 原判据"非不可达"、是错类型（L244-247） | `tolerance_audit.finding`（764 项 float64 ~1e-13 相对） | — |
| C10 | 两环境、参考环境=本地运行环境（L105-117） | `env_pip_freeze.txt`（57 行）；`ckpt_hashes.txt`；`data_hashes.txt`/`aapm_hashes.txt`；README L54-59 | — |
| C11 | 第一复现尝试的 checkpoint 换用事件（L249-258） | `R6_recalc_report.md`（provenance 事件记录）；hash 级 pinning | — |
| C12 | 结论：失败判据是调查起点、按指标声明（L296-302） | 上述 C1-C11 全链 | — |

---

## 8. UNRESOLVED 清单

| # | 项 | 缺失内容 | 影响声明 |
|---|---|---|---|
| U1 | 参考环境独立版本记录 | 作者原始运行时的 OS 具体版本 / GPU 型号数量 / 驱动 / CUDA/cuDNN / Python/PyTorch/NumPy 的独立记录（pip freeze / nvidia-smi / 容器 tag 确证） | C10 的"参考侧独立确证"部分 |
| U2 | ASSET_MANIFEST.md SHA256 栏 | 空占位，无数值级比对 | 资产清单数值核对 |
| U3 | 参考侧 bit-identical 独立性 | 6 文件 MATCH 出自复算者报告，非独立第三方核验 | C4/C7 的独立性表述 |
| U4 | routeA_run.log 原始日志 | 在仓库外复算工作目录（`r6_recalc/routeA_run.log`），仓库内未提交 | C4 日志级证据 |
| U5 | 第三环境 | 未做实验（`manuscript.tex` L289 TODO） | 跨环境系统性未知（L287-288） |
| U6 | pre-registration 时间戳证据 | 不存在 → 全文用 "original declared criterion" | C2/C6 的"声明判据"而非"预注册" |
| U7 | 作者元数据 | author order / affiliations / ORCIDs / corresponding author（L22 TODO） | 投稿就绪 |
| U8 | CRediT / competing interests | L309-313 TODO | 投稿就绪 |
| U9 | data/code 可用性措辞 | L304-305 TODO，依赖公开释放决策 | 投稿就绪 |

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
