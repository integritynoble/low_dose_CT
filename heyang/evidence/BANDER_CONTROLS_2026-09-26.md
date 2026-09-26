# BANDER_CONTROLS_2026-09-26 — BANDER-2 五 controls 在真实 AAPM 切片 + R3 同 ROI 的对照测量

- **日期**：2026-09-26
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 5a（BANDER-2；owner 已授权运行）
- **执行机器**：本机（持图机器，Windows 11）
- **红线遵守**：全程 CPU 确定性操作；未启动任何 GPU 推理 / 训练 / 昂贵重跑；未修改任何度量定义（band_energy_ratio、find_tissue_roi 协议与 R3 完全一致）；度量定义、数据树、分支代码来源均有哈希记录；仅 commit 不 push
- **状态**：COMPLETE（含负结果与局限，见 §5–§6）

---

## 1. 方法

### 1.1 度量与协议（detectability-freq-v1，未修改）

与 R3 落盘 artifact（`WS-1_dataset/R6_recalc/results/freq_aapm_real_r025_*.json`）完全一致：

- 高频带：`h(img) = img - gaussian_filter(img, sigma=1.0)`
- ROI BandER：`||h(out)_roi||^2 / max(||h(fd)_roi||^2, eps_floor)`，`eps_floor = 1e-4 × 全图 FD HF 能量`
- `find_tissue_roi`：HU [10,120] 平坦低梯度低 std 32×32 选区，seed 42，50 次尝试
- `DET_SLICES = 48`，切片采样 `step = max(1, n // 48)`
- signal-present 位置：`find_micro_peak`（高频幅度 5×5 局部极大、避开 absent ROI、距边缘 40px 内）
- 数据树：`WS-1_dataset\pipelines\_runtime\aapm_tree_v1`（aapm_hashes.txt 25 项已核）；h5 内 `recon/full_dose` 为 HU 值，经 `hu_to_norm`（[-1024,3072]→[0,1]）后进入 `find_tissue_roi`（其内部 `norm_to_hu` 转回 HU），与 R3 输入表示同一往返

### 1.2 Controls（来自 bander/control-matrix @ a42ad27 `scripts/bander_controls.py`，参数取分支默认/单测值，未调参）

| control | 参数 |
|---|---|
| blur | σ=1.0（R3 blur trap 同 σ） |
| additive Gaussian noise | σ_HU=20，seed=7（固定） |
| unsharp oversharpen | amount=1.0，σ=1.0 |
| truncated-frequency ringing | keep=0.25（FFT 各轴保留中央 25%） |
| lesion erasure in disc | disc 中心 = signal-present patch 中心，半径 10 px，σ=3.0 |

### 1.3 测量口径

每个 control × 每例（4 AAPM test 例：aapm-0003 / 0005 / 0006 / 0009）× 48 slice（= 192 ROI/control）：

- **whole-region absent**（与 R3 artifact 同口径）：`find_tissue_roi` 组织 ROI 全 32×32 patch
- **whole-region present**：`find_micro_peak` 信号 patch 全 32×32
- **lesion-local absent**：absent ROI 中心 r=10 disc 内
- **lesion-local present**：signal patch 中心 r=10 disc 内

patient-level 不确定性：每例 48 slice 的均值与 SE（std/sqrt(48)，ddof=1）；summary 为 4 例均值的均值。

### 1.4 命令与哈希

```
python C:\...\temp\bander2_real_controls.py
```

| 项 | 值 |
|---|---|
| 分支 | bander/control-matrix @ `a42ad2703594b4c3a4cd6a02396d1ae444f64dac` |
| 分支脚本（导出副本）SHA256 | `67D74945D527ADBF0CB4A2FED65D719DBBFB41E3FCA0C02A85E900C36F10B1E6` |
| 计算 driver SHA256 | `AB7C0FC70E9BC2D3E4951D68B6CA9C416693DA1FF4D36476C1A180ED9A05DB93` |
| 结果 JSON SHA256 | `AF66D0D018F665B6E8F9980A183CC4E73CE3CA2F1FC91D75ADB7C33B14281BCD` |
| 数据树哈希 | aapm_hashes.txt（25 项，含 h5：如 aapm-0003 h5 = `4197B0A1…`） |
| 真实方法值来源 | `freq_aapm_real_r025_{red_cnn,ctformer,learn,blur}.json`（R3 artifact） |

环境：Python 3.11.8、numpy 2.4.6、scipy 1.17.1、h5py 3.16.0（scipy/h5py 本次补装）；无 torch（controls 为 fd 纯函数，不需要模型推理）。

---

## 2. 对照表全文（summary：4 例均值）

| control | whole-region absent | whole-region present | lesion-local absent | lesion-local present |
|---|---:|---:|---:|---:|
| blur | 0.1399 | 0.2942 | 0.1257 | 0.2946 |
| ringing (k=0.25) | 0.1398 | 0.2338 | 0.1178 | 0.2133 |
| lesion erase (disc r=10) | **1.0000** | 0.4354 | **1.0000** | **0.0427** |
| noise (+20 HU, seed 7) | 2.3025 | 1.1074 | 2.3988 | 1.0530 |
| oversharpen (1.0, σ1) | 2.9494 | 2.3321 | 2.9975 | 2.3129 |

### 2.1 control × patient（whole-region absent，= R3 同口径主表）

| control | aapm-0003 | aapm-0005 | aapm-0006 | aapm-0009 |
|---|---:|---:|---:|---:|
| blur | 0.1402 | 0.1813 | 0.1414 | 0.0968 |
| ringing | 0.1286 | 0.1789 | 0.1435 | 0.1081 |
| lesion erase | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| noise +20HU | 1.6884 | 2.1715 | 3.2124 | 2.1376 |
| oversharpen | 2.9845 | 2.7803 | 2.8884 | 3.1443 |

patient-level SE（48 ROI，ddof=1）：blur 0.004–0.010；ringing 0.011–0.016；lesion erase 0；noise 0.038–0.090；oversharpen 0.015–0.038。完整 4 口径 × 4 例均值/SE 见随附 JSON（§7）。

---

## 3. 与真实方法值并排（summary，whole-region absent 口径）

| object | ROI BandER | 与 controls 关系 |
|---|---:|---|
| blur control | 0.1399 | 最低（与真实 blur 同方向） |
| ringing control | 0.1398 | 与 blur 并列最低 |
| lesion-erase control | 1.0000 | 等于 parity（whole-region 盲视） |
| **blur（真实方法 trap）** | **0.4315** | 位于 controls 低端 |
| noise control (+20 HU) | 2.3025 | 介于 learn/red_cnn 之下 |
| oversharpen control | 2.9494 | 接近 learn/red_cnn |
| **learn（真实）** | **3.8539** | 高于全部五 controls |
| **red_cnn（真实）** | **3.8762** | 高于全部五 controls |
| **ctformer（真实）** | **6.7352** | 最高，超出所有 controls |

真实方法值（per-patient）：red_cnn {3.492, 3.433, 4.059, 4.521}；ctformer {5.116, 5.971, 8.668, 7.186}；learn {3.479, 3.408, 4.013, 4.516}；blur {0.352, 0.457, 0.523, 0.394}（来自 R3 artifact，未重跑）。

---

## 4. 关键确认：lesion erasure 在真实解剖上复现 phantom 行为

9-13 §3b 记录的 phantom 报告行为（whole-region ≈0.999 vs lesion-local 0.9992→0.0997，disc 317/65,536 px）在**真实 AAPM 病人切片 + R3 同 ROI** 上得到 **confirm**：

- whole-region absent BandER = **1.0000**（SE=0，4 例 192 ROI 全部 1.0000）：在远离 disc 的组织 ROI 上，擦除 10px disc 对全 patch 能量比的影响在输出精度下不可见；
- lesion-local present BandER = **0.0427**（per-patient 0.033–0.049）：disc 内高频能量被抹平至参考的 ~4%；
- whole-region present = 0.4354（disc 位于 signal patch 内，patch 级能量部分下降）。

**结论（测量限度内）**：ROI BandER 的 whole-region 聚合对 signal 位置的局部病灶破坏不敏感，lesion-local 口径才能反映该破坏；这支持 9-13 §3b 提出的"spatial aggregation 需要进一步调查"，且表明 R3 artifact 的 whole-region ROI BandER 不能单独作为诊断内容保持的代理。

---

## 5. 结论（测量限度内）与负结果

1. **能量反映噪声与锐化，不反映结构内容**：noise control（+20 HU）与 oversharpen control 的 BandER 均 >1（2.30 / 2.95），位于 learned 方法（3.85–3.88）之下、真实 blur（0.43）之上；与 9-14 §2.3 归因（learned 方法残差宽带噪声 + 附加高频内容主导）方向一致。
2. **ctformer 超出全部 controls**：6.735 高于 oversharpen（2.95）约 2.3×，说明其高频能量超出简单锐化放大可解释范围，指向更强的附加高频内容/伪影机制；仍属假设，未被本表单独证明。
3. **负结果（如实保留）**：
   - 五 controls 未能在 whole-region 口径下分离出"结构保持"：lesion erase 得 1.0（=parity），blur/ringing 得 ~0.14（远低于 parity）——该口径对"破坏诊断内容"与"破坏高频纹理"的方向反应与直觉相反，仅对能量量级敏感。
   - ringing 在平坦组织 ROI 上 BandER 低（0.14，与 blur 并列），其 Gibbs 伪影集中在边缘，tissue ROI 内不抬升 BandER。
4. **真实 learned 方法均高于五 controls**：3.85–6.74 超出噪声（2.30）与锐化（2.95）单独可及的范围，需二者联合或更强的机制；本表不能把"结构/噪声/伪影"分离到可归因精度（同 BANDER_DIAG_AUDIT 的结论）。

---

## 6. 局限

- controls 直接作用于 full-dose 参考（`out = ctrl(fd)`），而真实方法值为"quarter-dose 输入 → 模型输出 vs fd 参考"；两者链路不同，量级不可直接等同比较，方向可比。
- signal-present 位置由 `find_micro_peak` 在 fd 高频图上定位（R3 同逻辑），但 R3 artifact 未落盘 per-slice ROI 坐标，无法逐值回放验证坐标一致性；协议代码与参数逐字一致，ROI 选择为确定性 seed 42。
- lesion disc（r=10，σ=3.0）与 phantom 报告同参数；未扫描 disc 半径敏感性。
- 噪声 control 仅测 +20 HU 一个水平（9-14 反例中 +60 HU 更高，未重测）。
- 本测量不构成临床阈值选择、确认性剂量-任务研究或科学接受完成（协议未决前保持诊断性质）。

---

## 7. 产物与提交

- 本报告：`heyang/evidence/BANDER_CONTROLS_2026-09-26.md`
- 结果 JSON：`heyang/evidence/BANDER_CONTROLS_real_2026-09-26.json`（含 per-patient 4 口径均值/SE、control 参数、协议、哈希、命令）
- 提交：`git commit`（仅 commit 不 push），commit id 见下节。

<!-- COMMIT_ID_PLACEHOLDER -->
