---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_6352bca2a20111f1abe1525400e6dd8f
    ReservedCode1: f7rMoSOpSH6tONK2I+mtthwD810loykQBLAdKXH1C/S/BY/37c/kt/Ox3cxFjzE2WDCnlhJPqDI+l+ltNHV47ZPeFonOGNXuqVpVF0OHrJ30AM7c43tuiDucGgi0/na4hyyCAAuCFUfHdJ2wHD5EwtqjtwX33wbTRIcV2ew5UxWhESprSXZtUV/ZnQc=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_6352bca2a20111f1abe1525400e6dd8f
    ReservedCode2: f7rMoSOpSH6tONK2I+mtthwD810loykQBLAdKXH1C/S/BY/37c/kt/Ox3cxFjzE2WDCnlhJPqDI+l+ltNHV47ZPeFonOGNXuqVpVF0OHrJ30AM7c43tuiDucGgi0/na4hyyCAAuCFUfHdJ2wHD5EwtqjtwX33wbTRIcV2ew5UxWhESprSXZtUV/ZnQc=
---

> **SUPERSEDED（口径一致性收尾 2026-08-31）**：本文为早期制定的 CTformer 重训方案（n=30 时代背景）。
> 全量口径复核后 CTformer 模拟域 knee 已达 Rose 准则，原方案不再需要作为稿件依据。
> 重训历史见 `ctformer_retrain_report.md`（已另行标注）。


# CTformer 模拟域重训方案（任务 C）

> 背景：已定位 CTformer 模拟域剂量效应不显著（knee not_reached、模拟版 PSNR≈42–43 与 blur 同级、CNR≈0.2 平坦；真实版 BandER 最高 6.735）为**训练/收敛问题**，非模型缺陷、非评估脚本问题。本方案给出可执行重训路径，含入口命令、超参差异、验收标准与回滚策略。**只读制定方案，不实际启动训练。**

---

## 1. 训练入口定位与完整重跑命令

### 1.1 统一 harness 入口（当前 checkpoint 的来源）

`WS-1_dataset\baselines\src\pwm_ldct_baselines\cli.py` 定义了 4 个子命令：`train / eval / dose-curve / vendor-loocv`；`train.py` 为训练循环（MSE + Adam，from scratch）。CTformer 通过 `models\ctformer_wrapper.py` 注册为 wrapper（**`pretrained=False`，从零训练**），官方实现 vendored 于 `baselines\vendor\ctformer\`。

CLI 用法（`baselines\README.md`）：

```bash
cd WS-1_dataset/baselines
# 训练
python -m pwm_ldct_baselines train \
    --dataset <harmonized_tree> --out checkpoints/ctformer.pt --model ctformer \
    --epochs <N> --lr 1e-4 --batch-size 1 --seed 42 [--device cuda]
# 评估（重训后必跑，产出 *_results_det.json 供剂量曲线）
python -m pwm_ldct_baselines eval \
    --dataset <harmonized_tree> --checkpoint checkpoints/ctformer.pt \
    --split test --out results/ctformer_results_det.json --seed 42
```

> 说明：RUN_PLAN.md §4/README 均以 `python -m pwm_ldct_baselines …` 为规范入口；容器版为 `docker run --gpus all … pwm-ldct-baselines:v0.5 train/eval …`（依赖 `baselines/Dockerfile.baseline` 镜像）。

### 1.2 官方 CTformer 原生训练入口（vendor 参照，非本仓库实际路径）

`baselines\vendor\ctformer\main.py` + `solver.py`：官方为 patch 训练、多 GPU，默认超参见 §2.2。**本仓库统一 harness 未使用该入口**，而是 wrapper + 统一 train.py，这本身是差异来源之一（见 §2.2 对照表）。

---

## 2. 当前检查点 / 日志 / 超参差异

### 2.1 当前检查点

| 项 | 值 |
|---|---|
| 检查点 | `WS-1_dataset\baselines\checkpoints\ctformer.pt` |
| 大小 / 时间 | 334.1 MB，2026-08-19 21:32（与 red_cnn/learn 同日同批训练） |
| 训练元数据 | 盘点环境无 torch，未能反序列化 `{seed,steps}`；**unified train.py 只保存 `{model,state_dict,seed,steps}`，未持久化 epochs/lr/batch** → 重训时必须显式记录 |
| 现网分布式检测 | 见 `results\ctformer_results_det.json`：模拟档 PSNR≈52/50/47（r050/r025/r010）、CNR≈3.69/2.68/1.56（red_cnn 对照），ctformer 对应档 PSNR 42–43、CNR≈0.2 平坦 |

### 2.2 超参差异对照（关键疑点）

| 维度 | 本仓库统一 harness（train.py / 现用 ctformer.pt） | 官方 CTformer（vendor main.py） |
|---|---|---|
| 输入 | 整图 512×512 | patch 训练：patch_n=4 × patch_size=64 |
| 有效 batch | CLI 默认 1（512×512 整图） | patch_n×batch_size = 4×16 = 64 patches |
| lr | 1e-4（Adam，harness 默认） | **1e-5**（Adam，官方默认） |
| 训练量 | epochs/step 由 CLI 指定（未记录） | num_epochs=4000（iterations 为主，decay_iters=8000） |
| 种子 | seed 42，单卡/多卡自动 | 多 GPU（CUDA_VISIBLE_DEVICES=2,3） |
| 损失 | MSE（[0,1] 归一空间） | MSE（HU 空间，norm_range -1024..3072） |

**差异推断**：CTformer 参数量大（embed_dim 768、depth 12、token_dim 1024、kernel/stride 32，→334 MB），而统一 harness 默认 `lr=1e-4, batch=1` 仅跑数 epoch（现网 smoke/短训曲线），在该配置下 512×512 整图、批大小 1 的优化非常困难——这恰好解释模拟版 PSNR 停在 42–43、CNR 平坦、收敛不足。重训重点：**提高有效批量（patch 或更大 batch）、按官方 lr=1e-5 量级、加大训练步数**，并全程记录超参。

---

## 3. 验收标准（重训后判定收敛达标）

对照 RED-CNN / LEARN / 现网 det json，全部满足才判定达标：

1. **保真：PSNR/SSIM 接近 RED-CNN/LEARN 同级**
   - 参考：red_cnn 全剂量模拟档 PSNR≈52.3(r050)/50.6(r025)/47.7(r010)、SSIM≈0.992/0.989/0.981（`red_cnn_results_det.json`）。
   - 达标线：ctformer 同 dose 档 PSNR 差距 **≤2 dB**、SSIM 差距 **≤0.01**（现网 42–43/0.98 距达标有实质差距）。
2. **剂量效应：CNR 随剂量单调上升**
   - 由 `eval` 的 `detectability.cnr_mean` 判断，须满足 `cnr(r050) > cnr(r025) > cnr(r010)`（现网约 0.2 平坦，不通过）。
3. **knee 可达 Rose**：r050 档 `cnr_mean ≥ 3.0`（Rose 判据），`dose-curve` 输出 knee ≠ not_reached（`dose_detectability_stats.json` 核验）；此条是审稿关注的核心。
4. **不回归真实版**（可选加分项）：重训后真实版 BandER 不低于现用检查点（现 6.735 [5.54,7.99]），避免顾此失彼。
5. **固定种子集**：正式入稿数值必须跑 `eval --seeds 42,2023,7,12345,999 --out ..._seedset.json` 取均值±区间（RUN_PLAN §8），曲线从种子集均值重建。

> 补充：仅重训并不自动改变检出的 flat CNR 成因归属；重训同时建议按任务 A 落盘逐 slice `cnr_values`，以便给剂量曲线附 bootstrap CI。

---

## 4. 算力 / 时间预估与回滚策略

### 4.1 算力与时间

- RUN_PLAN §3 预估：transformer 类 **12–24 GPU h**（单卡收敛）；本地仅 RTX 4060 Laptop 8 GB（<16 GB 下限、512 整图 batch=1 勉强），**正式重训建议数据中心 GPU（A100/H100/V100 ≥16 GB）**。
- 建议先小步试点（如 1/10 步数验证 PSNR 上升趋势）再全量。

### 4.2 回滚策略（重训失败不丢失现用基线）

1. 重训前备份：
   ```bash
   Copy-Item checkpoints/ctformer.pt checkpoints/ctformer_pre_retrain.pt
   ```
2. 重训输出**新文件名**（勿覆盖旧档），先临时评估：
   ```bash
   python -m pwm_ldct_baselines eval --dataset <tree> --checkpoint checkpoints/ctformer_retrain.pt --split test --out results/ctformer_retrain_det.json --seed 42
   ```
   对照 §3 标准核验 `ctformer_retrain_det.json`。
3. 达标：将 `ctformer_retrain.pt` 替换为正式 `ctformer.pt`（或同步引用），重建 `dose-curve` 与 `dose_detectability_stats.json`，更新手稿 `tab:baselines_v05` / `tab:detectability_v05`。
4. 未达标：删除 `ctformer_retrain.pt`，用备份恢复：
   ```bash
   Copy-Item checkpoints/ctformer_pre_retrain.pt checkpoints/ctformer.pt -Force
   ```
   现网 `ctformer_results_det.json` 与剂量曲线保持不变，身份/引用路径零改动。
5. 每次尝试将存档命名为 `ctformer_retrain_run<N>`，记录训练命令、超参、验收结果，便于审计。

---

## 5. 待确认项（执行前需决策）

- 数据树：使用本地已落柄的 LIDC 合成树还是 v1.0 全量 GIS 树（RUN_PLAN 指出 v0.5 树未落地，本地为合成树）。
- 超参组：优先尝试「patch_n=4 × patch_size=64 + lr=1e-5 + 增长步数」或「整图 512 + lr=1e-4 + 大 batch + 多 epochs」两条路线之一，跑 pilot 对比后定全量。
- 种子集全量评估安排在收敛后（每模型 5 seeds × 3 dose）。
