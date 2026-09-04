---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_e1407526a4fc11f1b8ae525400287e28
    ReservedCode1: 29zKFNFIGnhd3Vb78lyx6me3t6e3h/QGHIhP+AxN4p1xTonWMmnay4+BrQKZJ2a32y9EtPMMCZsBk4BzWku4i1J/obOY8g+jJRTgJKV04CdMlFKrm6cEeH/ERRcBoSBvagmVwbUyIXuuxACPP6gh+uoHnPOIWcZ+lxlKMdd1xbuE5yICVvXT/kIyLNg=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_e1407526a4fc11f1b8ae525400287e28
    ReservedCode2: 29zKFNFIGnhd3Vb78lyx6me3t6e3h/QGHIhP+AxN4p1xTonWMmnay4+BrQKZJ2a32y9EtPMMCZsBk4BzWku4i1J/obOY8g+jJRTgJKV04CdMlFKrm6cEeH/ERRcBoSBvagmVwbUyIXuuxACPP6gh+uoHnPOIWcZ+lxlKMdd1xbuE5yICVvXT/kIyLNg=
---

# LIDC 模拟版样本级 Bootstrap 置信区间报告（SCI 投稿补强，n=764 全量口径）

> 目标：为手稿模拟版关键数字（全量 n=764 剂量-可检测性曲线 knee、每档 CNR、blur vs 模型判别分离）补充**样本级（slice 级）bootstrap 95% CI**。

> 数据源：`baselines/results/*_results_det_full764.json`（全量 detectability sweep 产出，每模型 5 个固定 seed × 3 档剂量，每档每 seed 764 test slices；逐 slice CNR 存于 `detectability.per_slice.cnr`）。本报告替代此前的 n=30 版（`lidc_simulated_bootstrap_report.md` 旧版），旧版结论（RED-CNN 0.328 / LEARN 0.291 / CTformer 未达标等）已由 n=30 小样本口径废弃。

> 重采样方法：**slice 级有放回重采样**（每剂量档 **764 distinct slices**），B=4000，固定随机种子 20260831，百分位法 2.5%-97.5%。knee 定义为 CNR=3（Rose criterion）在固定剂量网格 0.10/0.25/0.50 上的线性插值交点；若 r010 档代表值已 ≥3，knee 记为 **≤0.10**（位于最低采样剂量之下，不向外推）。

> LEARN 说明：其 slice 级 CNR 均值因个别 slice 零局部噪声方差而为 inf（5-seed 网格一致），与手稿一致使用 **slice 中位数** 作为代表值（r010/25/50 观测 6.49/12.21/21.62）。

> **修订（2026-09-04）：5-seed pooling 已移除，本版 CI 为更正后数值。**
> 此前版本按"每剂量档 764 slices/seed，5-seed pooled 后 3,820 slices"重采样。但固定 seed 集
> {42, 2023, 7, 12345, 999} 对本管线**不产生任何变异**：对每个模型、每个剂量档，五个 seed 的
> 逐 slice 向量（psnr/ssim/cnr/cho_auc/npwe）**逐字节相同**（sha256 一致）——推理在给定
> checkpoint 下是确定性的，seed 未进入任何随机环节。因此 3,820 的池实为 764 个 slice 的
> 5 份完全副本，n 被虚增 5 倍，所有百分位 CI 被压窄约 sqrt(5) ≈ 2.24 倍。
> 本版改为对 **764 个 distinct slice** 重采样；§2/§3 的 CI 相应变宽 1.7–2.4 倍。
>
> **结论未变**：所有 ≤0.10 的 knee 判定依然成立（r010 各模型 CI 下界 5.00–5.81，远高于
> Rose = 3.0），CTformer 的 knee CI 仍严格落在 r010 与 r025 之间。变化的是不确定性宽度，
> 不是方向或排序。
>
> 生成脚本：`analysis/bootstrap_lidc_sim.py`（此前仅提交了产物，未提交生成器）。
> `--pooling seed_pooled` 可复现旧版数值（已逐项核对：§1/§2/§3 全部一致），
> 结果存于 `output/lidc_simulated_bootstrap_stats_full764_seed_pooled.json` 仅供对照；
> `--pooling distinct`（默认）产出本版 `output/lidc_simulated_bootstrap_stats_full764.json`。

## 1. 各模型 knee（Rose-crossing 剂量档）95% CI

| 模型 | 观测 knee | 95% CI | not_reached 次数 (B=4000) | 说明 |
|---|---|---|---|---|
| red_cnn | ≤0.10（r010 CNR 5.19 > 3） | ≤0.10 | 0 | 4000/4000 次抽样 r010 已超 Rose，knee 在最低采样剂量之下 |
| learn | ≤0.10（r010 CNR 6.50 > 3，slice median） | ≤0.10 | 0 | 同上 |
| corediff | ≤0.10（r010 CNR 5.34 > 3） | ≤0.10 | 0 | 同上 |
| ctformer | 0.131 | [0.123, 0.139] | 0 | 4000/4000 次在 r010 与 r025 之间越过 Rose（CNR 2.57→4.61） |
| blur | ≤0.10（r010 CNR 5.75 > 3） | ≤0.10 | 0 | 同上（n=764 distinct slice 数据参与重采样） |

## 2. 各剂量档 CNR 代表值 95% CI（n=764 distinct slices/档）

| 模型 | 剂量档 | 代表值 | 95% CI | 口径 |
|---|---|---|---|---|
| red_cnn | sim_r010 | 5.192 | [5.000, 5.389] | mean |
| red_cnn | sim_r025 | 8.052 | [7.758, 8.359] | mean |
| red_cnn | sim_r050 | 10.970 | [10.560, 11.376] | mean |
| learn | sim_r010 | 6.491 | [5.809, 7.097] | median |
| learn | sim_r025 | 12.212 | [11.334, 13.850] | median |
| learn | sim_r050 | 21.621 | [18.994, 24.291] | median |
| ctformer | sim_r010 | 2.574 | [2.451, 2.702] | mean |
| ctformer | sim_r025 | 4.608 | [4.394, 4.824] | mean |
| ctformer | sim_r050 | 6.857 | [6.544, 7.175] | mean |
| corediff | sim_r010 | 5.343 | [5.141, 5.552] | mean |
| corediff | sim_r025 | 8.431 | [8.120, 8.746] | mean |
| corediff | sim_r050 | 11.540 | [11.114, 11.958] | mean |
| blur | sim_r010 | 5.746 | [5.497, 6.001] | mean |
| blur | sim_r025 | 9.384 | [8.975, 9.799] | mean |
| blur | sim_r050 | 13.045 | [12.513, 13.584] | mean |

## 3. blur vs 各模型 CNR 分离比 95% CI（n=764 distinct 配对 slice 重采样）

| 对比 | 剂量档 | 观测分离比 | 95% CI |
|---|---|---|---|
| blur vs red_cnn | sim_r010 | 1.11x | [1.089, 1.125]x |
| blur vs red_cnn | sim_r025 | 1.17x | [1.147, 1.184]x |
| blur vs red_cnn | sim_r050 | 1.19x | [1.171, 1.207]x |
| blur vs learn | sim_r010 | 0.89x | [0.837, 0.968]x |
| blur vs learn | sim_r025 | 0.77x | [0.703, 0.814]x |
| blur vs learn | sim_r050 | 0.60x | [0.550, 0.674]x |
| blur vs ctformer | sim_r010 | 2.23x | [2.180, 2.286]x |
| blur vs ctformer | sim_r025 | 2.04x | [1.983, 2.089]x |
| blur vs ctformer | sim_r050 | 1.90x | [1.840, 1.965]x |
| blur vs corediff | sim_r010 | 1.08x | [1.061, 1.090]x |
| blur vs corediff | sim_r025 | 1.11x | [1.097, 1.130]x |
| blur vs corediff | sim_r050 | 1.13x | [1.114, 1.147]x |

> 注：模拟版无 BandER 指标（BandER 为 AAPM 真实版判别指标），此处分离比使用 CNR（模拟版判别维度）。配对重采样按同 slice 索引对齐（blur 与各模型均使用同一 eval 管线的 deterministic test-slice 顺序），覆盖 764 个 distinct 配对。LEARN 用 slice 中位数口径。

## 4. 与 AAPM 患者级 bootstrap CI 对照

| 版本 | 重采样单元 | 指标 | 观测值 | 95% CI |
|---|---|---|---|---|
| AAPM 患者级 | 患者 (n=4) | blur vs red_cnn ROI BandER 分离比 | 9.17x | [7.64, 10.69]x |
| AAPM 患者级 | 患者 (n=4) | blur vs ctformer ROI BandER 分离比 | 15.59x | [13.80, 17.40]x |
| AAPM 患者级 | 患者 (n=4) | blur vs learn ROI BandER 分离比 | 9.13x | [7.57, 10.66]x |
| LIDC 模拟 slice 级 | slice (n=764/档) | blur vs 各模型 CNR 分离比 | 见 §3 | 见 §3 |

> 两条证据线独立互补：真实版在患者间（跨患者稳定性）验证 blur 恒为最差（BandER）；模拟版在 slice 间（样本不确定性）验证 knee 与 CNR 分离方向——CNR-only 判据无法区分 blur 与学习型方法（blur 在 r010 即达 Rose，且其 CNR 高于 RED-CNN/CoreDiff/CTformer、低于 LEARN median），进一步佐证 BandER 必须保留为判别维度。

## 5. 局限性

- **knee 左截断**：RED-CNN/LEARN/CoreDiff/blur 的 knee 位于最低采样剂量 r010 之下，只能报告"≤0.10"，无法给出更细的区分（如需区分需在 r010 以下增加剂量采样点）。
- **knee 插值线性假设**：knee 基于 3 个固定剂量点的分段线性插值，实际剂量-响应曲线可能非线性；CTformer 的 knee 0.131 位于 r010 与 r025 之间。
- **LEARN 口径**：LEARN 使用 slice 中位数而非均值（均值因零方差 slice 为 inf），其 knee/分离比与均值口径模型不可直接横向比较。
- **配对假设**：blur 与各模型的 slice 配对基于同一 eval 管线 deterministic slice 顺序，未做显式逐 slice 身份校验。
- **仅覆盖判别主指标**：CHO AUC 模拟版全为 1.0（无区分度），故 bootstrap 聚焦 CNR 与 knee。

## 6. 结论与建议

- n=764 全量口径下，除 CTformer 外所有方法（含 blur trap）在最低模拟剂量 r010 已越过 Rose，knee 均在 r010 以下；CTformer（重训后）为唯一 knee 落在测量范围内的模型（0.131 [0.123, 0.139]）。此前 n=30 的 knee 排序（0.328/0.292/0.291/0.253）为小样本子集伪影，已随全量 sweep 废弃。
- 该结果强化手稿论点：CNR-only 判据既不能区分 blur trap 与学习型方法，也不能在学习型方法间给出稳定的可检测性排序；判别维度必须由 BandER（AAPM 真实配对版）承担。
- 若需区分 r010 以下的 knee：需在 dose grid 增加低于 0.10 的采样档。
*（内容由AI生成，仅供参考）*
