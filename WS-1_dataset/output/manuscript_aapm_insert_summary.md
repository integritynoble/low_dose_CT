---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_2aff641da22411f1bc17525400826444
    ReservedCode1: ggFKPivgNFhENNbly+8CLx2pANOaWYh0M4y2Qy2fKTu8GUYRmrObqSm9IrbsJ6HUKMLjNlqZGghTKHUliTtPfud13FumwYUcQPx0HrDzZOSOHLtLP3pkzGdfT/KwN4nGH0pwsth+tylHcw7XzcUvLcTHt9wWj1Y+FDnEW5rFmPJoibZwSZo9roiaiWM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_2aff641da22411f1bc17525400826444
    ReservedCode2: ggFKPivgNFhENNbly+8CLx2pANOaWYh0M4y2Qy2fKTu8GUYRmrObqSm9IrbsJ6HUKMLjNlqZGghTKHUliTtPfud13FumwYUcQPx0HrDzZOSOHLtLP3pkzGdfT/KwN4nGH0pwsth+tylHcw7XzcUvLcTHt9wWj1Y+FDnEW5rFmPJoibZwSZo9roiaiWM=
---

# 手稿变更摘要 — AAPM 独立验证论证段落写入

- 日期：2026-08-27
- 手稿：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\paper_draft\manuscript.tex`
- 论证来源：`D:\ZHY\low_dose_CT-heyang\WS-1_dataset\output\aapm_external_validation_paragraph.md`（英文版段落）
- 性质：SCI 投稿补强第 1 步（AAPM 外部验证正面论证入稿）

## 1. 插入位置

- **所在节**：`Technical Validation` → `Real-paired validation on AAPM 2016 (held-out test)` 小节
- **具体位置**：该小节末尾 "In summary, the real-paired validation chain (R1--R6 + WS-2) closes on a consistent message..." 结语段落**之后**，紧接在 `\section*{Usage Notes}` 之前。
- **插入方式**：新增独立正文段落（非脚注 / 非审稿回复备注），加注释行标明出处，未改动任何既有段落、编号、交叉引用（`\label` / `\ref` / 表图编号均未变）。

## 2. 插入内容（摘录）

LaTeX 转义处理：`B = 4000` → `$B = 4000$`；范围连字符 → `--`（`9.17--15.59$\times$`）；`*强调*` → `\emph{}`；`vs.` → `vs.\ `（防吞空格）；仅含英文，语种与手稿一致。

```latex
% Added: AAPM external validation justification (Sci submission prep)
To address the concern that the AAPM evaluation rests on ten patients, we note
three points regarding the role of this cohort in our study. First, the AAPM
2016 Low-Dose CT Grand Challenge provides one of the few publicly available
paired acquisitions in which the same patient is scanned at both routine and
reduced tube current. ... Second, we deliberately used this cohort as an
\emph{independent external} validation set: no AAPM data participated in model
training or hyper-parameter tuning, and the detectability ranking we observe
on it is consistent with the LIDC-based simulated evaluation. ... Third,
although the cohort comprises ten patients, it supports statistically
meaningful paired comparisons at the per-ROI and per-patient level; ... the
paired sign tests / patient-level bootstrap ($B = 4000$) we report already
yield significant results (e.g., separation ratios of 9.17--15.59$\times$ with
confidence intervals bounded away from unity for the Group A models vs.\ the
blur trap). ... A larger paired cohort is a clear direction for future work.
```

要点结构：① 同患者配对扫描稀缺性 → 为何该领域以大规模模拟为主；② 独立外部验证集定位（未参与训练/调参、与 LIDC 模拟评估方向一致 → 跨数据域一致性证据）；③ 10 例仍支撑逐 ROI / 逐患者配对检验 + B=4000 bootstrap（分离比 9.17–15.59×，CI 远离 1）；④ 不以规模论一般性，以跨域一致性 + 内部统计稳健性定位为确认性外部验证。

## 3. 编译状态

- **编译结果：成功**
- **工具链**：MiKTeX（pdflatex），`pdflatex → bibtex → pdflatex` 两次编译完成
- **输出**：`manuscript.pdf`（30 页，1,763,007 字节）
- **日志检查**：全文无 `!` 硬错误，无 undefined reference / citation 警告
- 注：编译环境需降权运行（当前终端为管理员权限触发 MiKTeX "security risk" 拦截，通过 `runas /trustlevel:0x20000` 完成编译）

## 4. 其他说明

- 手稿为英文稿，按语种一致性要求仅插入英文版论证，未插入中文对照（中文版保留在来源 md 供返修沟通用）。
- 未改动手稿其他任何部分；本摘要即任务要求的变更记录，作为产出物供备案与后续 SCI 补强步骤引用。
*（内容由AI生成，仅供参考）*
