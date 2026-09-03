---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_67687940a1f211f1abe1525400e6dd8f
    ReservedCode1: qgW8/832put/ude2MWIVoAFO4aIqQT+Ius9+nOU2US/38SywtKR43BkUTZAugJKsawmqGDMB7hHsuvyP2VFZSzIa6iOIc3QrynA+IvKam9J+g5ONvatqZlLdOx+xFxHRJGvRdt6Nqr7DCtglTDO1ZmaXOfmJP7CWPZ572ny9WShvXA6SXj53RQ5cClI=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_67687940a1f211f1abe1525400e6dd8f
    ReservedCode2: qgW8/832put/ude2MWIVoAFO4aIqQT+Ius9+nOU2US/38SywtKR43BkUTZAugJKsawmqGDMB7hHsuvyP2VFZSzIa6iOIc3QrynA+IvKam9J+g5ONvatqZlLdOx+xFxHRJGvRdt6Nqr7DCtglTDO1ZmaXOfmJP7CWPZ572ny9WShvXA6SXj53RQ5cClI=
---

# Bootstrap 置信区间补强报告（SCI 投稿补强第 4 项）

> **[superseded 2026-08-31]** 本文档模拟版部分基于 n=30 子集口径（knee 0.328/0.291/0.253、CTformer 未达标），已被全量 n=764 sweep 取代；模拟版 slice 级 bootstrap 新结论见 `lidc_simulated_bootstrap_report.md`（RED-CNN/LEARN/CoreDiff/blur knee ≤0.10，CTformer 0.131 [0.128, 0.135]）。AAPM 真实版患者级 bootstrap 部分不受影响。以下为历史记录，保留供追溯。

> 目标：为手稿关键数字（knee 0.328/0.291/0.253、ROI BandER 分离比 8.9-15.6x、observer P(blur 末位)=1.0000 等）补充 95% 置信区间。

> 数据源（只读）：`aapm_r3_roi_detectability.json`（患者级 ROI BandER）、`aapm_dose_detectability.json`（患者 x 剂量档）、`aapm_observer_sensitivity_real.json`（slice-level bootstrap 结果）、`dose_detectability_stats.json`（模拟版聚合）。

> 重采样方法：AAPM 真实版按**患者级有放回重采样（n=4 例患者, B=4000 次）**；模拟版因仅存聚合剂量点、无逐 slice/sample 值，无法做样本级 bootstrap，详见 §4。

> 生成时间：2026-08-27；随机种子固定；Bootstrap 百分位法 2.5%-97.5%。


## 1. AAPM 真实版：各模型 ROI BandER 均值与 95% CI（患者级重采样）

统计对象：每患者 48 ROI 的 ROI BandER 均值，共 4 例患者（aapm-0003/0005/0006/0009）。对 4 例患者有放回重采样 4000 次，每次以重采样患者的 BandER 均值作为统计量。

| 模型 | 观测均值 | 95% CI | 备注 |
|---|---|---|---|
| red_cnn | 3.878 | [3.462, 4.290] | 真实模型 |
| ctformer | 6.725 | [5.543, 7.994] | 真实模型 |
| learn | 3.849 | [3.443, 4.264] | 真实模型 |
| blur | 0.431 | [0.373, 0.491] | blur 陷阱（最低） |

> 解读：blur 与任一模型的 95% CI 完全不重叠，分离统计稳健。n=4 患者样本较小，CI 偏宽，但 4000 次重采样下 blur 始终为最小值。


## 2. AAPM 真实版：blur vs 模型 分离比 95% CI（患者级重采样）

与手稿 '分离 8.9-15.6x' 对应：对每个患者计算 ratio = 模型ROI BandER / blur ROI BandER，再对 4 例患者重采样 4000 次。

| 对比 | 观测分离比 | 95% CI |
|---|---|---|
| blur<sub>最低</sub> vs red_cnn | 9.17x | [7.64, 10.69]x |
| blur<sub>最低</sub> vs ctformer | 15.59x | [13.80, 17.40]x |
| blur<sub>最低</sub> vs learn | 9.13x | [7.57, 10.66]x |

> 解读：即使取下界，分离仍 >=6.6x（blur/red_cnn、blur/learn）或更高，结论方向不变。


## 3. 按剂量档的患者级 BandER 均值 95% CI

统计对象：aapm_dose_detectability.json 中每患者每剂量档的 ROI BandER（48 ROI 均值），患者级重采样。

| 剂量档 | 模型 | 观测均值 | 95% CI |
|---|---|---|---|
| sim_r010 | red_cnn | 8.139 | [3.739, 14.368] |
| sim_r010 | ctformer | 12.496 | [6.290, 21.682] |
| sim_r010 | learn | 8.222 | [3.773, 14.619] |
| sim_r010 | blur | 0.352 | [0.206, 0.526] |
| real_r025 | red_cnn | 3.880 | [3.462, 4.290] |
| real_r025 | ctformer | 6.750 | [5.543, 7.994] |
| real_r025 | learn | 3.855 | [3.443, 4.264] |
| real_r025 | blur | 0.432 | [0.373, 0.491] |
| sim_r050 | red_cnn | 2.157 | [1.429, 3.246] |
| sim_r050 | ctformer | 5.031 | [3.133, 7.715] |
| sim_r050 | learn | 2.165 | [1.428, 3.270] |
| sim_r050 | blur | 0.183 | [0.140, 0.226] |

> 解读：各剂量档下 blur 均显著最低（CI 不重叠）；CTformer 在高剂量档 (sim_r050) 的 BandER 最高。


## 4. 模拟版 knee：无法做样本级 bootstrap（数据限制说明）

手稿模拟版 knee（RED-CNN 0.328 / LEARN 0.291 / blur 0.253）来自 `dose_detectability_stats.json`，其存储格式为**每模型 3 个剂量档（0.1/0.25/0.5）的聚合 CNR 均值**，未保留逐 slice/sample 的 CNR 原始值，因此**无法从现有存储对模拟版 knee 做患者/样本级 bootstrap**。

可用替代与限制：

- 各模型 *_results_det.json 保存了检测子集（30 slices）的 `cnr_mean / cnr_std / n`，可给出**每剂量档 CNR 的近似 95% 误差带**（t 分布），但**不是 bootstrap**，且无法传播到 knee （knee 由两点线性插值得到，无逐样本曲线）。

- 建议后续：重跑剂量曲线时输出每 slice 的 CNR 明细（或保留 seedset 多训结果），即可对 knee 直接 bootstrap。

- 既有 slice-level bootstrap：`aapm_observer_sensitivity_real.json` 已存有 B=4000 次 slice-level bootstrap 的 P(blur 末位) 结果（见 §5），该部分是真实可用的 bootstrap 证据。


## 5. Observer 指标评价

| 指标 | 数值 | CI / 说明 |
|---|---|---|
| P(blur 末位)，slice-level | 1.0000 | 既有 4000 次 slice 重采样，blur 恒为最差；flip_count={'red_cnn': 0, 'ctformer': 0, 'learn': 0}（0 次反超） |
| P(blur 最低)，患者级 | 1.0000 | 本报告患者级重采样佐证 (4/4 例患者 blur 全最低，B=4000) |
| 二项符号检验 p | <1e-50 | blur 低于各模型 192/192 aligned slice（既有，p=1.59e-58） |

> slice-level 提供逐 slice 证据，患者级提供跨患者稳定性证据，两者目的一致：blur 恒为 detectability 最差。


## 6. 结论摘要

- 拿到 95% CI 的指标：真实版各模型 ROI BandER 均值、blur-vs-模型分离比、按剂量档 BandER、observer 患者级 P(blur 最低)。

- 拿到既有 CI 类证据（非本次新增 bootstrap）：slice-level 4000 次 bootstrap P(blur 末位)=1.0000、二项符号检验 p=1.59e-58。

- 数据限制拿不到 bootstrap CI 的指标：**模拟版 knee**（仅存聚合 CNR 剂量点，无逐样本值）。

- 审稿回复建议：模拟版 knee 备注 '基于固定剂量点插值的点估计，CI/BB 需逐 slice 输出后补充'，真实版全部关键结论已有 bootstrap CI 支撑，不影响主结论。
*（内容由AI生成，仅供参考）*
