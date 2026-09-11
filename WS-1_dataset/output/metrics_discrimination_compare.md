---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_3d91be42a1e811f1abe1525400e6dd8f
    ReservedCode1: Sxmyepw7H9sBxp2ZtDxV+dBL0gTnnfjHMmMoTwkt2eQeM/lx/y6h+vkEMVMgw6UIdi5wzFUZq5pQkTZICYf2kGb05u319RWIcjo9yJXpwbHzc8qUpViaC2/rSW+T7YD3VL4+QRPTFC5eZrJhGhgSXu+ahGY6P5XQSfhIUUcky78bc/26EfKlf6n1Ggs=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_3d91be42a1e811f1abe1525400e6dd8f
    ReservedCode2: Sxmyepw7H9sBxp2ZtDxV+dBL0gTnnfjHMmMoTwkt2eQeM/lx/y6h+vkEMVMgw6UIdi5wzFUZq5pQkTZICYf2kGb05u319RWIcjo9yJXpwbHzc8qUpViaC2/rSW+T7YD3VL4+QRPTFC5eZrJhGhgSXu+ahGY6P5XQSfhIUUcky78bc/26EfKlf6n1Ggs=
---

# 新指标 (BandER) vs 旧指标 (CNR/CHO/NPWE) 定量判别力对比

> 对应 SCI 投稿补强第 1 项：提供"新指标 vs 旧指标对 blur 陷阱的定量判别力"对比表。
> 数据来源（只读）：`baselines/results/*.json`、`output/dose_detectability_stats.json`、`output/aapm_r3_roi_detectability*`、`output/aapm_paired_baselines_v2*`。
> 生成时间：2026-08-27；所有数值取自上述源文件聚合值，未修改源数据。

## 1. 核心对比表（AAPM 真实配对版，R3 ROI 协议，held-out test 4 例）

表 1：各模型在真实解剖数据上的指标值（每患者均值；CNR/CHO/NPWE 为旧插入式指标，ROI BandER 为新频域指标）

| 模型 | 数据域 | CNR | CHO (AUC) | NPWE | ROI BandER | 指标判 blur 方向 |
|---|---|---|---|---|---|---|
| RED-CNN | AAPM real | 0.10 | 1.000 | 223915 | **3.876** | BandER: 非最差 |
| CTformer | AAPM real | 0.09 | 1.000 | 222908 | **6.735** | BandER: 非最差 |
| LEARN | AAPM real | 0.10 | 1.000 | 222630 | **3.854** | BandER: 非最差 |
| CoreDiff | AAPM real | —（未交付真实配对 det 评估，仅模拟 fidelity） | | | | |
| **blur（陷阱）** | AAPM real | **0.17** | 1.000 | 220805 | **0.432** | **BandER: 判定为最差** |

表 2：模拟版（LIDC 剂量曲线，n=764 全量口径，dose_detectability_stats.json / lidc_simulated_bootstrap_stats_full764.json，knee=rose-crossing ratio）

| 模型 | 数据域 | CNR@r=0.25 | knee (rose-cross) | 备注 |
|---|---|---|---|---|
| RED-CNN | LIDC sim | 8.05 | ≤0.10 | r010 已超 Rose（CNR 5.19） |
| CTformer | LIDC sim | 4.61 | 0.131 [0.128, 0.135] | 重训后 r025 起越过 Rose（r010 2.57 仍低于） |
| LEARN | LIDC sim | 12.21（slice median） | ≤0.10 | r010 已超 Rose（6.50） |
| blur | LIDC sim | 9.38 | ≤0.10 | r010 已超 Rose（5.75） |

## 2. 判别力量化

表 3：各指标对"blur vs 4 个真实模型"的判别力（AAPM 真实版）

| 指标 | blur 聚合值 | 模型聚合值（min–max） | 分离比 | 判定 blur 为最差？ | 识别 blur 陷阱 |
|---|---|---|---|---|---|
| **ROI BandER**（新） | 0.432 | 3.854 – 6.735 | **8.9 – 15.6×** | 是（恒最差） | **是** |
| CNR | 0.17 | 0.09 – 0.10 | 1.6–1.9×（方向反） | 否（blur 反而最高） | 否 |
| CHO (AUC) | 1.000 | 1.000 | 1.0×（全饱和） | 否（无差别） | 否 |
| NPWE | 220805 | 222630 – 223915 | 1.008×（~0.8%） | 勉强最低但差异 <1% | 否（不可用） |
| TM-AUC（参考） | 0.990 | 0.990 | 1.0× | 否 | 否 |

统计判别佐证（observer 敏感度，`aapm_observer_sensitivity_real.json`）：
- slice-level bootstrap (4000 次)：P(blur 末位) = **1.0000**，flip_count = 0（blur 从未反超任意模型）
- 二项符号检验：blur 低于各模型 p = **1.59e-58**（192/192 slice 对齐），判别力统计显著

## 3. 结论

- **BandER（频域高频带能量保留比）是唯一在本项目数据上成功识别 blur 陷阱的定量指标**：真实解剖 ROI BandER 将 blur 与真实模型分离 8.9 – 15.6×，blur 在所有模型中恒为最差，且统计检验显著（P=1.0, p≈1.6e-58）。
- **插入式指标（CNR/CHO/NPWE）在真实解剖上无判别力**：CHO AUC 全模型饱和 1.000；CNR 方向反转（blur 反而最高，因 blur 抑制噪声而提高对比度信噪比）；NPWE 数值巨大且模型间差异 <1%，均无法识别 blur 陷阱。模拟版（n=764 全量）同样无判别力：所有方法（含 blur）在 r010 即已越过 Rose、knee 均为 ≤0.10，CNR/knee 无法区分 blur 与学习型方法，仅 CTformer 因重训后 r010 未达标给出唯一可测 knee（0.131）。
- **blur 陷阱同时伴随最高 fidelity（SSIM 0.965）与最低 detectability（BandER 0.432）**，进一步证明 fidelity 指标不能替代 detectability 评估，须以 BandER 为主指标报告。

## 4. 入稿位置建议

该表建议插入手稿 **Results 章节 R3（noise-ROI detectability）附近**（如 §3.3 或 Results 中 R3/R5 段落的对比小节），作为"新协议替代失效插入式指标"的直接定量证据；表 2（模拟版 knee）可作补充附于正文或附录。
