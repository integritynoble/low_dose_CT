# manuscript.tex 变更摘要：指标判别表 + 模拟 bootstrap CI 整合

> **[superseded 2026-08-31]** 本文档为 n=30 子集口径时期的插入总结，其中 knee 数值（RED-CNN 0.328 / LEARN 0.292 / CoreDiff 0.291 / blur 0.253、CTformer max CNR 0.223 未达）已被全量 n=764 sweep 取代：新结论见 `lidc_simulated_bootstrap_report.md` 与手稿 tab:lidc_sim_knee_ci（RED-CNN/LEARN/CoreDiff/blur knee ≤0.10，CTformer 0.131 [0.128, 0.135]）。以下为历史记录，保留供追溯。

> 生成时间：2026-08-28
> 源手稿：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\paper_draft\manuscript.tex`（编辑后 766 行，原 726 行）
> 数据来源：`output/metrics_discrimination_compare.md`、`output/lidc_simulated_bootstrap_report.md`

## 1. 变更总览

| 变更项 | 插入位置 | 新增表编号 | 注释标记 |
|---|---|---|---|
| 模拟版 slice 级 bootstrap CI（knee 95% CI + 方向对照论述） | Technical Validation 中 v0.5 模拟 dose-detectability 段（`fig:dose_detectability` 之后、`Published task specification` 段落之前） | **Table 12**（`tab:lidc_sim_knee_ci`） | `% Added: simulated bootstrap CI (Sci prep)` |
| 指标判别对比表（BandER vs CNR/CHO/NPWE 判别力） | AAPM real-paired validation 子节（R3 表 `tab:aapm_r3_roi_detectability` 之后、R4 段落之前） | **Table 14**（`tab:metrics_discrimination`） | `% Added: metrics discrimination table (Sci prep)` |

表编号衔接验证（从 `manuscript.aux` 提取，无重复、无跳号）：
- Table 12 = `tab:lidc_sim_knee_ci`（新增）
- Table 13 = `tab:aapm_r3_roi_detectability`（原有）
- Table 14 = `tab:metrics_discrimination`（新增）
- Table 15 = `tab:aapm_spread`（原有）
- Table 16 = `tab:aapm_delta_r`（原有）

## 2. 各变更内容摘录

### 2.1 模拟 bootstrap CI（Table 12）

**正文论述（新增段落，约 340 词）：**
- 对模拟版 knee 做 slice 级 bootstrap（B=4000，百分位 2.5–97.5%，按 5-seed pooled 的每剂量档 30/150 slices 有放回重采样）。
- 学习型基线 CI 窄且互不重叠：RED-CNN 0.328 [0.313, 0.344]、LEARN 0.292 [0.277, 0.305]、CoreDiff 0.291 [0.271, 0.308]——模拟 knee 排序在 slice 抽样下稳健。
- CTformer 在 4000 次重采样中均未达 Rose 阈值（max CNR 0.223）；blur knee 0.253 最低但仅有聚合值（blur 无随机性，仅 seed-42 数据）。
- **方向对照关键论述**：模拟版 CNR 判据下模型/blur 分离比仅 0.06–1.07×（多数档位 blur CNR 反而更高，因光滑去噪抬升 CNR 却破坏病灶细节），与 AAPM 真实版 BandER 方向相反（blur 分离 8.9–15.6×、P=1.0000）。slice 级 bootstrap 从反向证实：**仅靠 CNR 无法区分 blur 与学习型方法，必须依赖 BandER 作为判别维度**。

**Table 12 内容（knee CI）：**

| Model | Observed knee | 95% CI | Not reached (B=4000) | Remark |
|---|---|---|---|---|
| RED-CNN | 0.328 | [0.313, 0.344] | 0 | |
| LEARN | 0.292 | [0.277, 0.305] | 0 | |
| CoreDiff | 0.291 | [0.271, 0.308] | 0 | |
| CTformer | --- | --- | 4000 | max CNR 0.223 < Rose 3.0 |
| Gaussian blur (trap) | 0.253 | aggregate only | --- | single value (seed 42) |

### 2.2 指标判别对比表（Table 14）

**R3 正文追加（一句交叉引用）：**
- 直接量化各指标判别力：ROI BandER 将 blur 与学习型基线分离 8.9–15.6×，且每次 draw 均判 blur 最差（P=1.0000；192/192 slice 二项符号检验 p≈1.6e-58）；CNR 方向反转（blur 最高）、CHO 饱和、NPWE 差异 <1%。

**新增论述段（表前，约 200 词）：**
- BandER 是唯一同时满足 (i) 大幅分离（8.9–15.6×）、(ii) 4000 次 bootstrap draw 恒判 blur 最差（flip count 0）、(iii) 统计显著（二项符号检验 p≈1.6e-58）的指标。
- 插入式指标在真实解剖上按构造失效：CNR 方向反转（blur 0.17 vs 模型 0.09–0.10）、CHO AUC 全饱和 1.000、NPWE 数值巨大（~2.2e5）且模型间差异 <1%。
- 该表是"以频域协议替代失效插入式指标"的直接定量证据。

**Table 14 内容（判别力量化）：**

| Index | blur value | model range (min–max) | separation | blur worst? | Identifies trap? |
|---|---|---|---|---|---|
| ROI BandER (freq.) | 0.432 | 3.854–6.735 | 8.9–15.6× | Yes (always) | Yes |
| CNR | 0.17 | 0.09–0.10 | 1.6–1.9× (reversed) | No (blur highest) | No |
| CHO (AUC) | 1.000 | 1.000 | 1.0× (saturated) | No | No |
| NPWE | 220,805 | 222,630–223,915 | 1.008× (<1%) | Borderline (<1%) | No |
| TM-AUC (reference) | 0.990 | 0.990 | 1.0× | No | No |

## 3. 编译验证结果

- 编译流程：`pdflatex`(×3) + `bibtex`，降权 `runas /trustlevel:0x20000` 执行（管理员权限 pdflatex/bibtex 被安全策略拒绝）。
- **输出：manuscript.pdf，32 页**（1773758 bytes）。
- **硬错误：无**（三遍均无 `!` / Error / Fatal）。
- **undefined reference：无**（末遍 `compile_new3.log` 无任何 `Reference ... undefined` / `multiply defined`；首遍的 undefined 已在第二、三遍解析后消失）。
- **无未定义 citation 警告**。
- 编译日志（中间产物）：`paper_draft/compile_new1.log`、`compile_new2.log`、`compile_new3.log`、`compile_bib.log`。

## 4. 相关文件

- 手稿（已修改）：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\paper_draft\manuscript.tex`
- 编译产物：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\paper_draft\manuscript.pdf`（32 页）
- 源数据：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\output\metrics_discrimination_compare.md`
- 源数据：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\output\lidc_simulated_bootstrap_report.md`
