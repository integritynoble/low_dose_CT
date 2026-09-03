---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_6189f845a20111f193c6525400f8a581
    ReservedCode1: pCi00jO+q43Z4MVwLQu4hYcUGcLtRCsbfV1hL/HzQbcrXO38IYagqay7LC5P3XGtDs4treDa01DjFpUfl0NWBxGnLYMtZ9ab/R6vjOGZusiHrI85Zotn/rHppFQ/cN/NczmdwAwlPcqnJqHq9BT35y6izy25oYBv36QKHiznYj6Br1dqRN7HtmqqqvA=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_6189f845a20111f193c6525400f8a581
    ReservedCode2: pCi00jO+q43Z4MVwLQu4hYcUGcLtRCsbfV1hL/HzQbcrXO38IYagqay7LC5P3XGtDs4treDa01DjFpUfl0NWBxGnLYMtZ9ab/R6vjOGZusiHrI85Zotn/rHppFQ/cN/NczmdwAwlPcqnJqHq9BT35y6izy25oYBv36QKHiznYj6Br1dqRN7HtmqqqvA=
---

> **SUPERSEDED（口径一致性收尾 2026-08-31）**：本文为早期 30-slice 子集 bootstrap 可行性探查方案。
> 已由全量 n=764/剂量 bootstrap 完成并落地，最新结果见 `lidc_simulated_bootstrap_report.md` 与 `lidc_simulated_bootstrap_stats_full764.json`。
> 文中 n=30 相关数字与结论不再作为稿件依据。


# LIDC 模拟版逐样本数据可行性探测（任务 A）

> 目的：回应审稿人"AAPM 10 例规模小"质疑，评估能否用 LIDC 大规模模拟样本做样本级 bootstrap 置信区间。
> 结论先行：**现有 `*_results_det.json` 无逐样本明细，不可直接 bootstrap；但逐样本值在评估管线内部已逐 slice 计算，最小改动即可落盘，无需重跑训练。**

---

## 1. 现有结果文件的结构（已逐文件解析）

读取 `WS-1_dataset\baselines\results\` 下的 `red_cnn_results_det.json` / `learn_results_det.json` / `ctformer_results_det.json`（三个文件结构一致），根键为：

```
model / split / seed / task / per_dose
```

`per_dose` 按剂量档存储（`sim_r010` / `sim_r025` / `sim_r050` / `real`），每个模拟档内含：

| 字段 | 内容 | 是否逐样本 |
|---|---|---|
| `psnr` / `ssim` / `lpips` | 该 dose 档平均保真指标（标量） | 否（聚合） |
| `n` | 评估 slice 数 | — |
| `detectability.cnr_mean` / `cnr_median` / `cnr_std` | 检测子集的 CNR 聚合统计 | 否（聚合） |
| `detectability.cho_auc_mean` / `npwe_mean` | CHO AUC / NPWE 聚合 | 否（聚合） |
| `detectability.n_slices` | 检测子集 slice 数 | — |
| `detectability.roi_pos` / `task` / `observer` | 协议参数声明 | — |

**关键事实：三个模型、每个剂量档都只有聚合统计值（`cnr_mean` / `cnr_std` / `median` 各一标量），没有任何 `per_slice` / `per_image` / `cnr_values` 数组字段。**

样本量现状：检测子集每个 dose 档 `n_slices = 30`（每模型 3 个模拟 dose 档 × 30 slice）。即当前落盘数据即使持久化逐 slice 值，每个模型×剂量档也只有 30 个样本可重采样；LIDC 大规模样本优势需在完整 test split + 取消 slice 上限后才能在 bootstrap 中体现。

---

## 2. 能否做 LIDC 模拟版 bootstrap —— 可行，但需一次最小改动

### 2.1 关键发现：逐样本值在管线里"已经算出来，只是没存盘"

`baselines\src\pwm_ldct_baselines\observers.py` 的 `evaluate_detectability()` 在内部按 slice 循环调用 `model_detectability()`，并在返回 dict 中**已经包含逐 slice 数组**：

```python
# observers.py, evaluate_detectability 的 return
return {
    "cnr_mean": float(np.mean(cnrs)),
    "cnr_median": float(np.median(cnrs)),
    "cnr_std": float(np.std(cnrs)),
    "cnr_values": [float(v) for v in cnrs],   # <-- 已算出，但 eval.py 落盘时丢弃
    ...
}
```

而 `baselines\src\pwm_ldct_baselines\eval.py` 的 `_eval_loader()` 构造 `results["detectability"]` 字典时只挑选了 `cnr_mean / cnr_median / cnr_std / cho_auc_mean / cho_auc_median / npwe_mean / n_slices / roi_pos`，**把 `cnr_values` 这一逐 slice 数组丢弃了**。

### 2.2 结论

- **现网 JSON：不能**直接样本级 bootstrap（无逐样本数据）。
- **管线能力：可以**。逐 slice CNR 已在内存逐张算出，只需把 `cnr_values` 一起写盘；一旦落盘，即可对每模型×剂量档的 30 个逐 slice CNR 做有放回重采样（bootstrap），求：
  - 每模型 knee 前后各 dose 档的 CNR 均值 CI；
  - blur vs 模型分离比（如 `cnr_model / cnr_blur` 或差值）的 bootstrap CI。
- 重采样无需重跑训练，仅需重跑一次评估（`eval`，见 §3 命令）。

### 2.3 预估样本量与注意点

- 当前每 dose 档 `n_slices = 30` → bootstrap 可行（B=1000–4000），但 30 个样本的 CI 宽度有限，只能佐证不拔高。
- 要兑现"LIDC 大规模样本"论证，需在数据树完整时：①取消评估的 slice 上限；②全量 test split 评估后逐 slice 落盘，此时单模型可贡献数百至数千个 slice 级样本，逐患者/逐 slice 的 bootstrap CI 才具备统计说服力。
- 上述限制应在论文中如实表述：30-slice 子集的 CI 为初步证据，全量树评估后更新。

---

## 3. 最小改动点（具体到文件与字段）

统计聚合发生在 **`eval.py`（评估落盘）** 与 **`dose_curve.py`（读聚合做剂量曲线）**；`pipelines\pwm_ldct_prep\lowdose_sim.py` 是低剂量模拟数据生成脚本，不做统计、**无需改动**。

### 改动 1：`baselines\src\pwm_ldct_baselines\eval.py` — 把逐 slice 值写入 JSON

`_eval_loader()` 内构造 `detectability` 字典处（当前只写聚合），追加：

```python
res["detectability"] = {
    ...  # 现有字段保持不变
    "cnr_values": det["cnr_values"],      # observers.py 已返回，直接透传落盘
    "psnr_values": ps_values,             # 若需要逐 slice 保真值，把 ps/ss 累加改为 list append
    "ssim_values": ss_values,
}
```

具体最小动作：`_eval_loader` 循环中把 `ps += M.psnr(out, full)` 改为追加列表；`det["cnr_values"]` 已可由 `evaluate_detectability` 返回，无需改 observers.py。

『det values 已在内存』，因此**总改动量 ≈ 只改 eval.py 一个文件、十余行**。

### 改动 2（可选）：新写 bootstrap 脚本（建议放 `baselines\src\pwm_ldct_baselines\` 或 output 旁）

```python
# per_model × per_dose: cnr_values
for b in range(B):
    resample = np.random.choice(cnr_values, size=len(cnr_values), replace=True)
    means.append(resample.mean())
CI = np.percentile(means, [2.5, 97.5])
# 分离比 CI: 每轮用 blur 与模型各自的 resample 均值求比值/差值
```

### 重跑命令（无需重训）

```bash
cd WS-1_dataset/baselines
python -m pwm_ldct_baselines eval --dataset <harmonized_tree|本地合成树> \
    --checkpoint checkpoints/ctformer.pt --split test \
    --out results/ctformer_results_det_per_slice.json --seed 42
```

重跑后以 `*_det_per_slice.json` 为新数据源做 bootstrap，并以 `dose-curve` 重建剂量曲线（聚合均值不变，仅新增 CI 信息）。

---

## 附：数据链路核对

| 层 | 文件 | 逐样本状态 |
|---|---|---|
| 模拟数据生成 | `pipelines/pwm_ldct_prep/lowdose_sim.py` | 不涉及统计，无需改 |
| 评估（计算+落盘） | `baselines/src/.../eval.py` | 逐 slice 已计算、落盘时聚合 → **改动点** |
| 逐 slice 检测计算 | `baselines/src/.../observers.py` | 已返回 `cnr_values`，无需改 |
| 剂量曲线 | `baselines/src/.../dose_curve.py` | 读聚合，输出 `dose_detectability_stats.json`（仅聚合，与既往一致） |
*（内容由AI生成，仅供参考）*
