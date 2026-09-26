# Checkpoint 来源与许可说明（2026-09-25）

> **任务 5（第三环境）交付物 4/5**
> ⚠️ **本文件描述的 5 个权重为受控资产：发送第三方前需 owner 授权。**
> 未获 owner 明确授权前，第三方操作者不得接收、复制或二次分发这些权重。

---

## 0. 授权状态（必须先读）

| 项 | 状态 |
|---|---|
| 权重发送第三方 | **待 owner 授权**（授权前不发送） |
| 数据树发送第三方 | 待 owner 授权（与权重一并打包或分开发送） |
| 代码仓库（third-env/blackwell 分支） | 随授权后交付；私有仓库需访问权 |
| 本说明文档 | 已就位，供 owner 审核 |

---

## 1. 权重清单（5 个检查点 + 1 个内置 trap）

来源路径以 `ASSET_MANIFEST.md` A1（作者侧）为准；SHA256 完整值见
`R6_recalc/hashes/ckpt_hashes.txt`。

| 权重 | 大小 | 作者侧来源路径 | SHA256（前缀） | 训练来源 | 第三环境用途 |
|---|---|---|---|---|---|
| `red_cnn.pt` | 7.4 MB | `WS-1_dataset\baselines\checkpoints\red_cnn.pt` | `DF775D08…` | **训练来源未记录 / 待 owner 补充** | red_cnn eval |
| `learn.pt` | 774 KB | `WS-1_dataset\baselines\checkpoints\learn.pt` | `3EABF525…` | **训练来源未记录 / 待 owner 补充** | learn eval |
| `ctformer.pt` | 350 MB | `WS-1_dataset\baselines\checkpoints\ctformer.pt` | `AEAD0C15…` | **训练来源未记录 / 待 owner 补充**（早期大模型存档） | **不作为本复算对照** |
| `corediff.pt` | 19 MB | `WS-1_dataset\baselines\checkpoints\corediff.pt` | `41ABA674…` | **训练来源未记录 / 待 owner 补充** | corediff eval |
| `ctformer_small_retrain.pt` | 9.7 MB | `WS-1_dataset\baselines\checkpoints\ctformer_small_retrain.pt` | `78C0C59C…` | **有训练记录**：`output\ctformer_retrain_report.md`（2026-08-28；compact variant embed_dim 192/depth 6/2.42M params，AdamW lr 1e-4，batch 4，20,000 steps，seed 42；初始在 CPU 训练，后续 GPU cu128 评估） | **CTformer 复算实际权重（model 字段 ctformer_small）** |

**blur**：内置 trap（`get_model("blur")` 固定高斯核），**无需权重**。

> **诚实披露**：除 `ctformer_small_retrain.pt` 外，仓库内**没有**其余 4 个权重的
> 训练记录（无训练脚本/日志/报告）。此处如实标注「训练来源未记录 / 待 owner
> 补充」，**不编造**训练来源。若 owner 后续补充训练记录，应更新本表并重新登记
> 哈希锚点（若有变化）。

---

## 2. 代码许可（baselines 仓库）

`WS-1_dataset/baselines/`（`pwm_ldct_baselines` 训练/评估框架）：

- **License**：**Apache License 2.0**（`baselines/LICENSE`，202 行标准文本）。
- `pyproject.toml`：`license = { text = "Apache-2.0" }`，version 0.5.0。
- 依赖声明：`numpy>=1.21`、`torch>=1.12`、`pwm_ldct_loader>=0.5.0`；
  optional `lpips` / `dev`。第三环境分支在此基础上增加 Blackwell 环境说明
  （见交付物 2/5 diff 摘要）。

**loader 包**（`pwm_ldct_loader`）：editable 安装的两个本地包之一；其许可与
baselines 同仓库规范（Apache-2.0 系），具体以仓库 LICENSE 为准。

---

## 3. 上游数据溯源链（LIDC-IDRI）

| 层 | 对象 | 许可/条款 |
|---|---|---|
| TCIA 原始数据 | LIDC-IDRI DICOM（`.tcia` manifest + NBIA Data Retriever 下载） | **CC BY 3.0 Unported**（署名 + 遵循 TCIA citation 要求） |
| 项目加工层 | PWM-LDCT v0.5 HDF5 树 / 清单 / 标注对齐（`physionet_listing/`） | **CC BY 4.0**（项目发布许可） |

两层许可叠加：任何下游使用同时受 CC BY 3.0（上游）与 CC BY 4.0（项目自身）
约束。详见 `data_manifest_LIDC_AAPM.md` §2。

---

## 4. 训练数据与协议锚点（不随权重改）

- 权重产出的训练/评估协议锚点：`task_spec.json`
  （SHA256 `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`）。
- CTformer 复算使用 `ctformer_small_retrain.pt`（on-board 实际协议，
  model 字段 `ctformer_small`），**不是** `ctformer.pt`（R6 复算 §7.3 已确认）。
- 权重 SHA256 锚点文件：`R6_recalc/hashes/ckpt_hashes.txt`（第三方校验用）。

---

## 5. 授权后交付清单（owner 勾选）

- [ ] 5 个权重（`red_cnn.pt / learn.pt / ctformer.pt / corediff.pt / ctformer_small_retrain.pt`）打包 + SHA256 清单
- [ ] `task_spec.json`
- [ ] 数据树（LIDC sim 364 项 + AAPM 25 项，或授权范围的子集）
- [ ] 仓库访问权（分支 `third-env/blackwell`）
- [ ] 本说明随包交付（含授权签署/记录）
