# BANDER_DIAG_AUDIT_2026-09-21

- **日期**：2026-09-21
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，HEAD `3472815`，工作区干净）
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 5a（BANDER 诊断清点与补充）
- **红线遵守**：全程只读；未启动任何新推理 / GPU 训练 / 重跑昂贵计算；未 commit / 未 push / 未修改仓库任何文件；仅在本输出目录写此报告
- **说明**：本报告为 Agent 侧 5a 交付物（诊断证据清点 + BANDER-2/6 对照整理）；5b（离线拷贝收据）为独立交付，不在此报告范围内

---

## 1. 9-14 已有证据清点（HEYANG_REPLY_2026-09-14.md）

回复文件本身已入仓跟踪：`D:\ZHY\low_dose_CT-heyang\HEYANG_REPLY_2026-09-14.md`（148 行，写于 `heyang` @ `b520f9ab`）。

任务书 5a 要求恢复该回复背后的 driver、参数、checkpoint 选择、per-patient 数值输出与输入/输出哈希。逐项状态如下（R = 仓库可恢复；S = session-only，不可恢复；标注来源路径）：

| 证据项 | 状态 | 证据形态 | 证据文件 / 来源（绝对路径） |
|---|---|---|---|
| §1(b) BandER 设计原意（ratio against reference，1.0 为 parity；leaderboard 降序为自身引入，非设计来源） | R（完整） | 文本 + 引用原文 | 9-14 回复 §1；`WS-1_dataset\baselines\task_spec.json:66`、`WS-1_dataset\schema\detectability_task_spec.md:93`、`WS-4_leaderboard\scoring\leaderboard.py:313-329`（git blame → `54c58ca6`，2026-08-23） |
| §1 噪声注入器反例（~183 at +20 HU、~1598 at +60 HU） | R（回复正文记录） | 数字 | `scripts\prepare-bander-direction-fix.py`（只读分析，`72ba063` 引入） |
| §2(a) 推理重跑 driver：`a_rerun_diag.py`、`selfcheck_final.py` | **S（不可恢复）** | 脚本 | 会话 scratch `C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_745ff6c6840d4212ae08918d2177f660\temp\` —— **目录已不存在**，脚本未入仓 |
| §2(a) 参数（协议 verbatim） | R（完整） | 代码常量 | `WS-1_dataset\R6_recalc\freq_detectability_recalc.py`：`highfreq_hu`（HF_SIGMA=1.0）、`find_tissue_roi`（PATCH=32、seed 42）、`DET_SLICES=48`、`eps_floor = 1e-4 × full-image FD HF energy`；与 `bander/control-matrix` 分支 `scripts\bander_controls.py` docstring 同定义 |
| §2(a) checkpoint 选择 | R（完整） | 哈希 + 文本 | `baselines\checkpoints\red_cnn.pt` / `ctformer.pt` / `learn.pt` + blur（5×5 Gaussian σ=1）；**ctformer.pt 非 ctformer_small_retrain.pt**（9-14 §2.1 记录，per-slice 相对偏差 1.4e-06 vs 41%）；5 权重 SHA256：`WS-1_dataset\R6_recalc\hashes\ckpt_hashes.txt` |
| §2(a) per-patient 数值输出（4 例 × 48 ROI） | R（完整） | JSON（落盘 artifact） | `WS-1_dataset\R6_recalc\results\freq_aapm_real_r025_{red_cnn,ctformer,learn,blur}.json`：`per_patient.*.roi_band_energy_ratio` 与 `ber_per_slice`（48/例）；9-14 §2.2 自检显示 re-run 与 artifact 全局 max rel dev 7.5e-05（red_cnn）、0（learn/blur） |
| §2(a) 输入（npy）哈希 | **S（不可恢复）** | — | 输入 `...\r6_recalc\data\aapm_test_fd` / `aapm_test_ld` 位于会话 scratch（见 9-14 §4），scratch 已删除，npy 字节哈希未落盘；仅数据树级哈希可恢复：`WS-1_dataset\R6_recalc\hashes\aapm_hashes.txt`（aapm_tree_v1 25 项）、`data_hashes.txt`（LIDC 364 项） |
| §2(a) 输出图哈希 | **S（不可恢复）** | — | 输出图仅会话 scratch；9-14 未记录输出哈希，以与 artifact 的 per-slice 比较作为可复现性证据（max rel dev 见上） |
| §2.3 归因表（R_flat/R_edge/slope/ρ、能量账 α²、敏感性） | R（回复正文记录，可复核） | 表 + 数字 | 9-14 回复 §2.3 全文；依赖的 `roi_band_energy_ratio` / `alpha` 可由 `freq_aapm_real_r025_*.json` 复核 |
| §3 前提修正（3 learned + blur trap，非 4 learned；23/36） | R（完整） | JSON | `WS-1_dataset\output\aapm_lidc_cross_vendor_spread.json`：`per_vendor.*.patients[].models[].freq_roi.roi_band_energy_ratio`（5 vendor 组、12 例、36 个 learned 数值：GE 2/6、Philips 6/6、Siemens 1/6、Toshiba 2/6、AAPM-Siemens-real 12/12 超 2×，合计 23/36）；`updated_at 2026-08-22` |
| §2.3 中间产物 `s3a_selfcheck_final.json`、`s3a_table.json`、`dump_lines*.py` | **S（不可恢复）** | 中间 JSON/脚本 | 会话 scratch（同上，目录已不存在） |

**小结**：9-14 的**结论性证据（设计原意、归因数字、前提修正）与可复核的落盘 artifact（per-patient BandER、vendor spread）全部可恢复**；**不可恢复**的仅为 session-only 材料——推理 driver 脚本、输入 npy 与输出图及其哈希、中间自检 JSON。这些已在回复 §4 明示为 scratch，且 9-14 通过"re-run vs artifact per-slice 一致"完成了可复现性锚定，故不构成证据链断裂，但输入/输出字节级哈希确属缺失，应在 5b/后续交付中如实声明。

---

## 2. BANDER-2 对照整理 —— **BLOCKED（需新计算）**

### 2.1 当前证据状态

- **真实方法值侧（对照组基准）**：已有落盘 artifact —— `freq_aapm_real_r025_{red_cnn,ctformer,learn,blur}.json`，即 R3 所用同一批 AAPM 真实 quarter-dose 切片与组织 ROI（4 例 × 48 ROI = 192 ROI/对象，协议 detectability-freq-v1）上的 ROI BandER。
- **五 controls 侧**：`bander/control-matrix` 分支（`a42ad2703594b4c3a4cd6a02396d1ae444f64dac`）的 `scripts\bander_controls.py` 已实现五个纯函数 control（blur / additive Gaussian noise（固定 seed）/ unsharp oversharpen / truncated-frequency ringing / lesion erasure in disc）+ 10 个单测，**BANDER-1 已完成**（9-13 §3b：phantom 上做，勿重做）。
- **缺口**：五 controls 在**真实病人切片 + R3 同 ROI** 上的 ROI BandER **无任何落盘产物**（分支树中仅代码与测试，无结果 JSON/日志；9-14 未重跑该分支实验）。仅有的 phantom 结果在 9-13 §3b 中口头记录（lesion erasure whole-region ≈0.999 vs lesion-local 0.9992→0.0997，disc 317/65,536 px），未落盘，不可作为对照表使用。

### 2.2 对照结构（已定义，待授权执行后填数）

对照目标：与已提交真实方法值直接可比的 control-vs-BandER 表。数据来源与协议：
- 切片/ROI：R3 artifact 同切片同组织 ROI（`freq_detectability_recalc.py` 的 `find_tissue_roi`：PATCH=32、seed 42、DET_SLICES=48、HU 10–120 平坦低梯度低 std 选区，协议未修改）
- 度量：`band_energy_ratio(out_hu, fd_hu, mask)` = Σ o_hf² / max(Σ fd_hf², 1e-4×full-image FD HF energy)，与 artifact 同定义
- 对象：5 controls × 4 AAPM 例 × 48 ROI（192 ROI/control）；含 signal-present/absent 例、lesion-local 与 whole-region 两口径、patient-level 不确定性（每例 48 ROI 的均值/SE）
- 输出：control × patient 的 ROI BandER 表 + 与真实方法值（red_cnn 3.876 / ctformer 6.735 / learn 3.854 / blur 0.432）并排对照；负结果照实保留

### 2.3 BLOCKED 原因与所需资源

- **状态**：BLOCKED（本任务红线"严禁启动任何新的推理/重跑昂贵计算"；BANDER-2 虽然理论上是 CPU 确定性图像操作，但仍属**新计算**，且需在持图机器上按授权执行，故本任务不代为执行）。
- **所需资源/前提**（均已在机器上具备，仅缺授权执行）：
  1. 授权在本机（持图机器）运行 `bander/control-matrix`（a42ad27）`scripts\bander_controls.py` 五个纯函数；
  2. 数据树 `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pipelines\_runtime\aapm_tree_v1`（aapm_hashes.txt 25 项已核）；
  3. 与 R3 同切片/同 ROI 的掩膜生成（复用 `freq_detectability_recalc.py`，不重写口径）；
  4. 按 9-15 §3 报告契约输出 per-patient 值、patient-level 不确定性、source/checkpoint 哈希与命令。
- **对照结论**：因缺数据，无法在测量限度内回答"能量反映结构 / 噪声 / 伪影"的 control 归因；该项待 BANDER-2 授权执行后补充。

---

## 3. BANDER-6 对照整理 —— **COMPLETE（基于已有落盘 artifact，无新计算）**

### 3.1 对照结构

**问题**：过高的高频能量是否只是模拟器伪影（LIDC project-simulated 特有）？对照：同一固定测量协议（detectability-freq-v1：HF_SIGMA=1.0、PATCH=32、seed 42、DET_SLICES=48、eps_floor=1e-4×full-image FD HF energy）下，每方法在 LIDC-simulated 与 AAPM noise-inserted 两队列的 ROI BandER 并排对比。

**数据来源（全部为 2026-09-02 落盘 artifact，未重跑）**：
- LIDC project-simulated（8 例）：`WS-1_dataset\R6_recalc\results\freq_lidc_{red_cnn,ctformer,learn,blur}.json`
- AAPM challenge noise-inserted（projection-domain quarter-dose，4 例）：`WS-1_dataset\R6_recalc\results\freq_aapm_real_r025_{red_cnn,ctformer,learn,blur}.json`

### 3.2 对照表（summary_mean = per-patient 均值）

| method | LIDC project-simulated（8 例） | AAPM noise-inserted（4 例） | 方向（两队列一致？） |
|---|---:|---:|---|
| blur control（trap） | 0.1184 | 0.4315 | 最低 ✓ |
| RED-CNN | 1.5282 | 3.8762 | >1 ✓ |
| LEARN | 1.4893 | 3.8539 | >1 ✓ |
| CTformer | 7.6868 | 6.7352 | 最高 ✓ |

逐病人值（ROI BandER）：
- LIDC：red_cnn {0.935, 1.592, 0.820, 2.648, 0.475, 1.379, 3.692, 0.683}；ctformer {1.048, 10.020, 8.588, 10.363, 9.607, 2.728, 10.830, 8.312}；learn {0.941, 1.612, 0.737, 2.642, 0.305, 1.388, 3.713, 0.576}；blur {0.054, 0.091, 0.034, 0.180, 0.064, 0.190, 0.308, 0.027}
- AAPM real r025：red_cnn {3.492, 3.433, 4.059, 4.521}；ctformer {5.116, 5.971, 8.668, 7.186}；learn {3.479, 3.408, 4.013, 4.516}；blur {0.352, 0.457, 0.523, 0.394}

### 3.3 结论（测量限度内）

1. **"高频能量偏高"并非 LIDC 模拟数据独有**：learned 方法在两队列均显著高于 parity（1.0）且高于 blur trap；CTformer 两队列均为最高（LIDC 7.69 / AAPM 6.74），blur trap 两队列均为最低。
2. **跨队列方向一致，量级差异存在**：red_cnn/learn 在 LIDC 侧接近 parity（1.53 / 1.49），在 AAPM noise-inserted 侧 3.85 / 3.85；两队列的绝对量级不可直接作伪影大小归因——队列间混淆了 cohort（vendor / 解剖 / 协议混合）、剂量生成过程（projection-domain noise insertion vs project simulation）、病人数与 ROI 数（8 vs 4 例）。
3. **能量反映的机制（结合 9-14 §2.3 归因）**：两队列一致显示 learned 方法携带的 ROI 高频能量**主要与参考正交**（red_cnn/learn 正交份额 85.7%），且与未去噪低剂量输入的份额一致，指向**残差宽带噪声主导**；CTformer 在两队列均为最高且超出输入能量，与**附加高频内容（锐化/伪影）**一致。但无 BANDER-2 control 对照，本表**不能**把"结构 / 噪声 / 伪影"三者分离到可归因精度——这正是 BANDER-2 待补的角色。
4. **PSNR 归一化未复核**：9-13 §3b 表格中的 PSNR 差（blur 0.02 dB vs RED-CNN 12.45 dB 等）未在本任务中重新核验归一化/重建设置；本表仅使用 BandER，不作 PSNR 结论。
5. **负结果保留**：未发现任何 learned 方法在任一队列落入 blur 之下；trap 分离两队列均成立（与 `aapm_lidc_cross_vendor_spread.json` gate verdict=PASS 一致）。

### 3.4 局限（PARTIAL 子项）

- **matched controls 未覆盖全部**：BANDER-6 要求"each cohort's matched controls"——两侧仅有 blur trap 这一 control 数值落盘（LIDC 0.118 vs AAPM 0.432）；noise / oversharpen / ringing / lesion-erase 在两队列的数值**未落盘**（属 BANDER-2 同一新计算缺口）。此项随 BANDER-2 授权执行后补齐。
- **LIDC 四 vendor 分组未在本表展开**：freq_lidc 产物仅按病人 id 存值，vendor 分组维度在 `aapm_lidc_cross_vendor_spread.json`（GE 2 例 / Philips 2 / Siemens 2 / Toshiba 2 / AAPM-Siemens-real 4），其 per-vendor ROI BandER 与 freq_lidc 口径不同（前者为 vendor 侧测量，后者为 8 例 LIDC-sim）；完整 vendor 级对照属 BANDER-4，不在 5a 范围。

---

## 4. 缺失项与待办清单

| # | 缺失项 | 类型 | 需要什么 | 归属任务 |
|---|---|---|---|---|
| D1 | 9-14 推理 driver 脚本（a_rerun_diag.py 等）与中间 JSON | S（不可恢复） | 接受缺失，已由 per-slice artifact 一致锚定 | 5a 清点（如实声明） |
| D2 | 9-14 输入 npy / 输出图字节哈希 | S（不可恢复） | 接受缺失；数据树级哈希可恢复（aapm_hashes.txt / data_hashes.txt） | 5a 清点（如实声明） |
| D3 | BANDER-2：五 controls 在真实切片 + R3 同 ROI 的 ROI BandER 表 | BLOCKED（需新计算） | 授权在本机运行 `bander/control-matrix`（a42ad27）`scripts\bander_controls.py`（CPU 确定性操作；数据树 aapm_tree_v1 已在）；输出 per-patient + lesion-local/whole-region + patient-level 不确定性 + 哈希 + 命令 | 5a 补充 / 待 owner 授权 |
| D4 | BANDER-6 matched controls 全部 control 两侧数值 | BLOCKED（随 D3） | 同 D3 | 5a 补充 |
| D5 | LIDC 四 vendor 级 control 对照 | BLOCKED（需新计算） | 同 D3 在 LIDC 树执行（BANDER-4 范围） | BANDER-4（不在 5a） |
| D6 | 5b 离线拷贝收据（脱敏 manifest / 计数 / 校验 / dry-run 缺失拒绝清单） | 独立交付 | 13-Sep §§4-4b 授权动作；本报告不含 | 5b |

---

## 5. 汇总状态

| 交付物 | 状态 | 说明 |
|---|---|---|
| 9-14 已有证据清点 | **COMPLETE**（含 D1/D2 如实声明不可恢复） | 结论性证据与落盘 artifact 全部可恢复 |
| BANDER-2 对照 | **BLOCKED** | 缺五 controls 真实切片测量（新计算，待授权） |
| BANDER-6 对照 | **COMPLETE**（PARTIAL 子项：matched controls 不全） | 基于已有 freq_lidc / freq_aapm_real_r025 落盘产物整理，无新计算 |
| 5b 拷贝收据 | 不在本报告范围 | 独立交付 |

**科学验收红线**：以上均不构成临床阈值选择、确认性剂量-任务研究或科学接受完成；协议未决前这些保持诊断性质。
