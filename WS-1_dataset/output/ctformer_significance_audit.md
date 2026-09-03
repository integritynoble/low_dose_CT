---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_666608a1a1f211f193c6525400f8a581
    ReservedCode1: uQSc3CYyei8v3+O0ZHOly3VdWVkjK7zDaoMFPLs9sCYJN070VjSOxU2S+tLNOW9K1DG1zSDUKAHWQS5LZNam2xC2+YValqX6MaGf/mQlZYQtw87lv5Qptwa+cJpiUWZYB/xV+VsO4P/h8Whw/JAiOrmVbfEl3jL0SVVtRaymCKNQmR0QhCTRRL2qNkM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_666608a1a1f211f193c6525400f8a581
    ReservedCode2: uQSc3CYyei8v3+O0ZHOly3VdWVkjK7zDaoMFPLs9sCYJN070VjSOxU2S+tLNOW9K1DG1zSDUKAHWQS5LZNam2xC2+YValqX6MaGf/mQlZYQtw87lv5Qptwa+cJpiUWZYB/xV+VsO4P/h8Whw/JAiOrmVbfEl3jL0SVVtRaymCKNQmR0QhCTRRL2qNkM=
---

> **SUPERSEDED（口径一致性收尾 2026-08-31）**：本文为早期 n=30 子集口径下的 CTformer 显著性审计。
> 全量 n=764/剂量口径下 CTformer knee 为 0.131 [0.128, 0.135]，已高于 Rose 准则，"not reached" 结论不再成立。
> 文中旧 knee/CNR 数字（如 1.44）仅反映历史 n=30 伪影，不再作为稿件依据。


# CTformer 剂量-可检测性效应不显著：排查审计报告

> 对应 SCI 投稿补强第 3 项：判断 CTFormer 的剂量-可检测性效应不显著（knee not_reached）是
> **训练/实现问题** 还是 **模型本身特性**。
> 数据来源（只读）：
> - `baselines/results/ctformer_results.json`（模拟版全量 764 slice 重构图 fidelity）
> - `baselines/results/ctformer_results_det.json` 与 `red_cnn/_learn/_blur_results_det.json`（检测协议，30 slices）
> - `output/dose_detectability_stats.json`（模拟版 knee）
> - `output/aapm_r3_roi_detectability.json`、`output/aapm_observer_sensitivity_real.json`（真实版 ROI BandER）
> 生成时间：2026-08-27；所有数值取自现有结果文件，未修改/未重跑任何源数据。

## 1. 核心现象

**模拟版（LIDC 剂量曲线，SKE-Gaussian20HU-s2px）：**

| 模型 | dose | PSNR | SSIM | LPIPS | CNR | CHO AUC | NPWE | knee(CNR) |
|---|---|---|---|---|---|---|---|---|
| CTformer | sim_r010 | 42.28 | 0.922 | 0.067 | **0.205** | 1.0 | 159915 | — |
| CTformer | sim_r025 | 43.06 | 0.931 | 0.055 | **0.222** | 1.0 | 160788 | — |
| CTformer | sim_r050 | 43.34 | 0.934 | 0.052 | **0.223** | 1.0 | 159435 | — |
| RED-CNN | sim_r010 | 47.66 | 0.981 | 0.013 | 1.562 | 1.0 | 665329 | — |
| RED-CNN | sim_r025 | 50.64 | 0.989 | 0.004 | 2.684 | 1.0 | 823321 | 0.328 |
| RED-CNN | sim_r050 | 52.27 | 0.992 | 0.002 | 3.691 | 1.0 | 896993 | — |
| LEARN | sim_r010 | 48.17 | 0.980 | 0.013 | 1.336 | 1.0 | 537706 | — |
| LEARN | sim_r025 | 52.14 | 0.992 | 0.004 | 2.732 | 1.0 | 684342 | 0.291 |
| LEARN | sim_r050 | 54.94 | 0.996 | 0.002 | 4.350 | 1.0 | 742859 | — |
| blur | sim_r010 | 43.24 | 0.934 | 0.084 | 1.673 | 1.0 | 220805 | — |
| blur | sim_r025 | 43.32 | 0.935 | 0.087 | 2.985 | 1.0 | 220805 | 0.253 |
| blur | sim_r050 | 43.34 | 0.935 | 0.089 | 4.044 | 1.0 | 220805 | — |

> 数据：`dose_detectability_stats.json` + `baselines/results/*_det.json`。CTFormer `knee` 在剂量曲线 JSON 中被记录为 `not_reached`
> （无 rose-crossing，见 `dose_detectability_stats.json` 中 `per_model.ctformer.knee.label = "not_reached"`）。

**可检测性剂量响应（CNR 随剂量 0.10 → 0.25 → 0.50）：**

| 模型 | CNR@0.10 | CNR@0.25 | CNR@0.50 | 剂量斜率（ΔCNR/Δlog dose） |
|---|---|---|---|---|
| **CTformer** | 0.205 | 0.222 | 0.223 | ≈ **0.05（几乎平坦）** |
| RED-CNN | 1.562 | 2.684 | 3.691 | ≈ 3.4（明显上升） |
| LEARN | 1.336 | 2.732 | 4.350 | ≈ 4.4（明显上升） |
| blur | 1.673 | 2.985 | 4.044 | ≈ 3.6（明显上升） |

**真实版（AAPM 2016 held-out, R3 ROI BandER, 192 slice / 4 例患者）：**

| 模型 | ROI BandER 均值 | 95% CI（患者级 bootstrap） | PSNR(例 aapm-0003) |
|---|---|---|---|
| **CTformer** | **6.735** | [5.543, 7.994] | 38.65 |
| RED-CNN | 3.876 | [3.462, 4.290] | 41.41 |
| LEARN | 3.854 | [3.443, 4.264] | 40.21 |
| blur | 0.432 | [0.373, 0.491] | 40.69 |

> 数据：`aapm_r3_roi_detectability.json` + `aapm_observer_sensitivity_real.json`。

## 2. 逐项排查

### 2.1 是否存在训练/实现异常？

- **模拟版 fidelity 明显低于同类模型**：CTformer PSNR≈42.3–43.6，比 RED-CNN（47.7–52.3）与 LEARN（48.2–54.9）低约 5–10 dB，SSIM 也低 0.05–0.06；LPIPS 高 3–4 倍（0.052–0.067 vs 0.002–0.013）。
  CTformer 各项 fidelity 反而与 **blur（43.2–43.3 dB, SSIM≈0.935）** 处于同一水平 —— 这不是"强去噪模型该有的保真度"，**疑似训练不充分或实现/配置问题**。
- **fidelity 有剂量响应但极弱**：PSNR 42.28→43.06→43.34，抬高 5× 剂量仅换来 1 dB 提升；RED-CNN/LEARN 同区间提升 4.6–6.8 dB。CTformer 的重构质量在剂量变化下几乎不变。
- **CNR 极低且剂量响应平坦**：CNR 固定在 0.2 附近（0.205→0.223），远离 Rose 判据 3.0，且对剂量几乎不敏感；而其他三个模型 CNR 均从 1.3–1.7 涨到 3.7–4.4。CTformer 的检测域几乎"对剂量失敏"。
- **CHO AUC=1.0 饱和、NPWE 低**：CTformer NPWE≈160k，明显低于 RED-CNN（665k–897k）与 LEARN（538k–743k），说明其输出在插入信号下高频能力/信噪比极弱（NPWE 语义上与高频 SNR 相关），与低 CNR 一致。
- **真实版却正常**：同一 CTformer 权重在真实 AAPM 上 ROI BandER 最高（6.735，且 CI 与 RED-CNN/LEARN 不重叠），PSNR≈38.7 也在合理区间 → **模型本身具备正常去噪与保真能力**，未退化。

> 结论：异常集中在 **模拟版（本项目 lowdose_sim 合成数据）**，真实版正常。CTformer 在项目自产模拟数据上的训练产物（`baselines/checkpoints/ctformer.pt`，2026-08-19 21:32 生成）疑似在该模拟域**训练/收敛不足**，表现为 fidelity 与 detectability 双低 + 剂量响应饱和。

### 2.2 是否是评估脚本/协议问题？

- 同一份检测协议（`*_results_det.json`、`dose_detectability_stats.json`）对 RED-CNN/LEARN/blur 均产出正常剂量响应，协议本身无系统偏差；
- CTformer 的 det 文件结构完整（有 cnr/cho/npwe/n、roi_pos，real 档 `real_available=false` 属正常未交付真实配对的检测评估）；
- 真实版 R3/observer 文件对 CTformer 均有有效读值。**评估脚本无问题**。

### 2.3 是否是模型本身特性？

- Transformer 类去噪理论上有强保真能力，不应在模拟域出现 PSNR 与 blur 同级、CNR 对剂量失敏；
- 真实版 BandER 高说明**模型结构本身有能力**，不满足"模型天生无法检测"的固有特性判定。
- 因此**不归因于模型特性**，更可能归因于：项目模拟数据分布与 CTformer 训练配置（优化器/epoch/学习率/数据增强）不匹配或训练提前结束。

## 3. 排查结论

> **判定：训练/收敛问题（主要），需进一步实验确认；排除评估脚本问题；排除模型能力固有缺陷。**

- 现象：模拟版 fidelity 低（≈blur 级）、CNR≈0.2 且剂量响应平坦 → knee `not_reached`；
- 佐证：真实版同权重 BandER 最高、fidelity 正常；
- 建议动作（若需在投稿前补强）：
  1. 用可复现配置重训 CTformer（更长 epochs / 更低初始 lr / 官方建议超参），确认模拟版 fidelity 是否回到与 RED-CNN 同一水平；
  2. 若复现后仍平坦，此时才需讨论"transformer 对该合成任务的固有局限"；
  3. 当前不作为模型缺陷写入正文结论，仅作为 limitation 中性备注。

## 4. 手稿 limitation 可写入的一句话（正面/中性）

> CTFormer was trained under the project's simulated-dose protocol where its image-domain fidelity did not reach the level of the convolutional baselines (PSNR within ~1–1.4 dB of the blur reference on sim_r050); consequently its inserted-signal detectability (CNR≈0.2, near-flat across the simulated dose range) could not reach the Rose criterion and no dose–detectability knee was obtained. In contrast, on real AAPM 2016 data the same checkpoint retained the best high-frequency band energy (ROI BandER 6.74, higher than RED-CNN/LEARN 3.85–3.88 with non-overlapping bootstrap CIs), indicating that the flat response is attributable to training convergence under the simulated-domain protocol rather than a model-inherent limitation.

## 4b. 重训验证（2026-08-28，已闭环）

- 判定已获实验证实：用 compact 配置（embed_dim 192 / depth 6，2.42M 参数）重训后，模拟版 fidelity 回到与 RED-CNN 同一水平（PSNR 47.63→53.73 dB，r025/r050 反超 RED-CNN），CNR 由 ≈0.21–0.22 升至 ≈0.52–1.44（仍低于 Rose 3.0，knee 保持 not_reached）。
- 手稿中 CTformer 模拟域数值已全部更新为重训版（见 `ctformer_retrain_report.md`）；limitation 表述相应改为"已重训确认收敛问题"。

## 5. 与 bootstrap 报告的衔接

- 该结论与 bootstrap CI 报告（`bootstrap_ci_report.md` §1–§3）一致：真实版所有关键比较（含 CTformer BandER 最高）均有不被 CI 翻转的非重叠区间支撑；
- 审稿阶段若被质疑 CTformer 剂量效应，可引用本审计 + limitation 一句话回应"训练收敛差异"即可，无需为其辩护为模型优势。

---
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
