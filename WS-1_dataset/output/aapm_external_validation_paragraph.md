---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_62a2c053a20111f193c6525400f8a581
    ReservedCode1: kc101tPVrLKOppL0SUYnjKUPpvXKpSmWy0iBGaZDju44EkHvWUh08hGMSFDfVLIWJOTOZ90G9LYFKVYftdmWyvHvSshRo3upJNrhAuqxkaJ+nfVdOItvvGyOWlpe53ykl/C17H/pPwecOBorc9fmQMvE8ql657bt/39LRWbdQCYJf2h3K20bguta3b8=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_62a2c053a20111f193c6525400f8a581
    ReservedCode2: kc101tPVrLKOppL0SUYnjKUPpvXKpSmWy0iBGaZDju44EkHvWUh08hGMSFDfVLIWJOTOZ90G9LYFKVYftdmWyvHvSshRo3upJNrhAuqxkaJ+nfVdOItvvGyOWlpe53ykl/C17H/pPwecOBorc9fmQMvE8ql657bt/39LRWbdQCYJf2h3K20bguta3b8=
---

# AAPM 独立验证正面论证段落（任务 B）

> 用途：直接入稿的 Discussion / Methods（Results）段落，回应审稿人"仅 10 例能否支撑一般性结论"的质疑。
> 使用说明：正文首选英文版（期刊为 SCI 英文稿），中文版供内部理解与返修沟通；两版段落结构与要点一一对应。

---

## 英文版（English, ~300 words, journal-ready）

To address the concern that the AAPM evaluation rests on ten patients, we note three points regarding the role of this cohort in our study. First, the AAPM 2016 Low-Dose CT Grand Challenge provides one of the few publicly available paired acquisitions in which the same patient is scanned at both routine and reduced tube current. Such genuine same-patient paired data are exceptionally difficult to collect prospectively, which is precisely why prior benchmarks in this field remain dominated by large but simulated cohorts. Second, we deliberately used this cohort as an *independent external* validation set: no AAPM data participated in model training or hyper-parameter tuning, and the detectability ranking we observe on it is consistent with the LIDC-based simulated evaluation. The agreement across data domains—one large purely simulated set and one small but genuinely paired real set—constitutes cross-domain evidence that the reported behavior is not driven by a particular simulation artifact. Third, although the cohort comprises ten patients, it supports statistically meaningful paired comparisons at the per-ROI and per-patient level; within-patient pairing removes inter-subject anatomical variability, and the paired sign tests / patient-level bootstrap (B = 4000) we report already yield significant results (e.g., separation ratios of 9.17–15.59× with confidence intervals bounded away from unity for the Group A models vs. the blur trap). We therefore do not claim generality on the basis of sample size alone. Instead, we argue from *consistency across data domains* together with *internal statistical robustness*, and we treat the AAPM cohort as confirmatory external validation rather than as an estimate of population-level effect size. A larger paired cohort is a clear direction for future work.

---

## 中文版（中文对照，供理解与返修沟通）

为回应"AAPM 仅 10 例能否支撑一般性结论"的质疑，我们就该队列在本研究中的定位说明三点。

其一，AAPM 2016 低剂量 CT 挑战赛提供了极少数公开可得的"同一患者按常规剂量与低剂量分别扫描"的配对数据（same-patient paired acquisition）。这类真正同患者的配对扫描在临床上极难前瞻性获得，这正是该领域既有基准长期以大规模模拟队列为主的原因。

其二，我们有意将该队列作为**独立外部验证集**使用：AAPM 数据未参与任何模型的训练与超参调整，且在其上观测到的可检测性排序与基于 LIDC 的模拟评估方向一致。两个数据域——一个为大规模纯模拟、一个为规模小但真实同患者配对——结论一致，构成跨数据域（cross-domain）证据，说明观测行为并非由特定模拟伪影驱动。

其三，虽然该队列仅 10 例患者，但它在逐 ROI 与逐患者层面提供了可做统计检验的配对比较：同患者配对消除了受试者间解剖差异，且我们报告的配对符号检验与患者级 bootstrap（B=4000）已给出显著结果（如 Group A 模型相对 blur 陷阱的分离比 9.17–15.59×，置信区间远离 1）。

因此，我们**不以规模宣称一般性**，而是以"跨数据域一致性 + 内部统计稳健性"支撑结论：将 AAPM 队列定位为验证性外部证据而非总体效应量估计。更大规模配对队列的收集是明确的后续方向。

---

## 要点自检对照（两大质疑逐一回应）

| 质疑 | 论证落点 | 字数 |
|---|---|---|
| 10 例规模小 | 配对扫描稀缺性 → 定位为独立外部验证集；逐 ROI/逐患者配对检验有统计效力 | 英语段落第 1/2/3 句 |
| 一般性 | 不以规模论，以跨域一致性（模拟 vs 真实同向）+ 内部显著性（分离比 CI >1、P 值）支撑 | 第 4/5 句 |
| 佐证数字 | 分离比 9.17 / 15.59 / 9.13×、B=4000、患者级 bootstrap | 第 3 句末尾 |
