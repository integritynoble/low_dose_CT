# 逐项权利检查表（RIGHTS CHECKLIST）— 任务 6 发布包

- **仓库**：`D:\ZHY\low_dose_CT-heyang`（私有）
- **日期**：2026-09-26
- **口径**：对 `RELEASE_MANIFEST.md` 清单逐项核查再分发/发布权利。结论三档：**可发布**（随策展包分发）/ **需授权**（owner 明确授权后方可分发本体，当前仅列哈希）/ **不可发布**（上游许可或约束禁止再分发）。
- **原则**：作者自有代码按仓库既有许可（Apache-2.0）声明；上游数据只引用与哈希，不主张再分发权；权重受控仅哈希。

---

## 1. 结论总览

| 编号 | 资产组 | 结论 | 关键依据 |
|---|---|---|---|
| R1 | 作者自有复算/论文代码（R6 脚本、make_tables.py、loader、schema、listing） | **可发布** | 作者自有；loader/baselines 声明 Apache-2.0；发布层 CC BY 4.0 |
| R2 | baselines（pwm_ldct_baselines） | **可发布** | `baselines/LICENSE` Apache-2.0（202 行标准文本）；pyproject license=Apache-2.0 |
| R3 | 哈希锚点清单（hashes/ 5 文件） | **可发布** | 作者自产内容；不含数据本体与权重本体 |
| R4 | 复算结果 JSON（comparison_linux_full764.json 等） | **可发布** | 基于公开数据（LIDC/AAPM）的数值结果，作者自产 |
| R5 | LIDC-IDRI 派生数据树（图像） | **仅哈希，不可随包再分发** | 上游 TCIA CC BY 3.0；项目发布层 CC BY 4.0（credentialed PhysioNet 渠道） |
| R6 | AAPM 2016 数据树（图像） | **仅哈希，不可随包再分发** | 上游 TCIA/AAPM 挑战赛条款；v0.5 范围外（v1.0 roadmap），无再分发授权记录 |
| R7 | 5 个 checkpoint 权重 | **需授权（当前仅哈希）** | 训练来源 4/5 未记录；checkpoint_provenance_license.md §0 明确发送需 owner 授权 |
| R8 | 第三环境运行包（third_env/ 4 文档） | **可发布**（随包时保留受控说明） | task 5 交付物；checkpoint_provenance_license.md 为受控说明而非权重本体 |
| R9 | 论文包（manuscript/PDF/台账/表格） | **可发布**（作者区 TODO 定稿后） | 作者自有；L23/L324/L327 需 owner 输入后方可对外投稿 |
| R10 | 第三方依赖环境（env_pip_freeze.txt） | **可发布**（仅清单引用） | 各依赖自有许可（BSD/MIT/Apache 等）；随包仅列版本不附带二进制 |

---

## 2. 逐项明细

### R1 作者自有代码（可发布）

| 资产 | 结论 | 依据 |
|---|---|---|
| `R6_recalc/compare_linux_vs_ref.py` / `compare_full764.py` / `recompare_per_metric.py` / `tolerance_audit.py` | 可发布 | 作者自有；仓库代码，随策展包分发并保留 Apache-2.0 声明 |
| `R6_recalc/freq_detectability_recalc.py` / `statistical_tests_recalc.py` | 可发布 | ASSET_MANIFEST A3/A4 随附脚本，作者自有 |
| `Heyang-paper/make_tables.py` | 可发布 | 作者自有表格生成脚本 |
| `WS-1_dataset/pwm_ldct_loader`（源码树） | 可发布 | 作者自有包；组合哈希 `87BA7C4F5B0F4AA883DB0A93C48AF59D76EF0C3AF6962AA95F44E9327B9EEB84`（A2）；许可与 baselines 同仓库规范（Apache-2.0 系） |
| `WS-1_dataset/schema/*`（6 文档） | 可发布 | 作者自有规范文档，Methods 引用对象 |
| `WS-1_dataset/physionet_listing/listing.md` | 可发布 | 作者自有；页面声明 Open access / CC BY 4.0 |

### R2 baselines（可发布）

| 资产 | 结论 | 依据 |
|---|---|---|
| `baselines/LICENSE` | 可发布 | Apache License 2.0 标准文本（202 行），随包保留 |
| `baselines/pyproject.toml` | 可发布 | license = Apache-2.0；version 0.5.0 |
| `baselines/task_spec.json` | 可发布 | 作者自有协议锚点（SHA256 AE7AE799…） |
| `baselines/README.md` | 可发布 | 作者自有说明（"needs pwm_ldct_loader on the path"） |

### R3 哈希锚点清单（可发布）

| 资产 | 结论 | 依据 |
|---|---|---|
| `hashes/ckpt_hashes.txt` | 可发布 | 仅哈希文本，不含权重；与 ASSET_MANIFEST A1 一致 |
| `hashes/data_hashes.txt`（364 项） | 可发布 | 仅哈希文本；数据本体按 R5 |
| `hashes/aapm_hashes.txt`（25 项） | 可发布 | 仅哈希文本；数据本体按 R6 |
| `hashes/env_pip_freeze.txt` | 可发布 | 环境依赖版本清单，不含二进制 |
| `hashes/task_spec_hash.txt` | 可发布 | 协议锚点记录 |

### R4 复算结果 JSON（可发布）

| 资产 | 结论 | 依据 |
|---|---|---|
| `results/comparison_linux_full764.json` | 可发布 | Linux rerun vs reference 全量结果，论文数字支撑（COMPLETION_CHECKLIST §1/§2） |
| `results/comparison_full764.json` | 可发布 | Windows 历史 artifact，route A 证据保留 |
| `results/` 其余 28 项 JSON | 可发布（按需附送） | 复算中间结果，作者自产 |

### R5 LIDC-IDRI 数据（仅哈希，不可随包再分发）

| 资产 | 结论 | 依据 |
|---|---|---|
| LIDC 派生数据树（HDF5/annotations/metadata/splits） | **不可随包再分发**；哈希清单可发布 | TCIA LIDC-IDRI CC BY 3.0 Unported（署名 + TCIA citation 要求）；项目发布层 CC BY 4.0 通过 PhysioNet credentialed 渠道；README v0.5 仅 LIDC 1010 患者 |
| `data_manifest_LIDC_AAPM.md`（溯源与许可说明） | 可发布 | 作者自产说明文档，不含数据本体 |

### R6 AAPM 2016 数据（仅哈希，不可随包再分发）

| 资产 | 结论 | 依据 |
|---|---|---|
| AAPM 数据树（aapm-0003/0005/0006/0009 等 25 项） | **不可随包再分发**；哈希清单可发布 | 上游 TCIA/AAPM 挑战赛条款（以 TCIA 条目为准）；README 明确 AAPM 为 v1.0 roadmap，v0.5 不含 AAPM 数据树；作者侧无 AAPM 再分发授权记录 |

### R7 checkpoint 权重（需授权，当前仅哈希）

| 权重 | 结论 | 依据 |
|---|---|---|
| `red_cnn.pt` | **需授权** | 训练来源未记录；third_env 说明 §1 待 owner 补充；发送前不得复制/二次分发 |
| `learn.pt` | **需授权** | 训练来源未记录 |
| `ctformer.pt` | **需授权** | 早期大模型存档，不作为复算对照；训练来源未记录 |
| `corediff.pt` | **需授权** | 训练来源未记录 |
| `ctformer_small_retrain.pt` | **需授权** | 作者重训（有 `output/ctformer_retrain_report.md`，2026-08-28），但权重发送仍按 owner 决策；当前仅哈希 |

> 统一依据：`third_env/checkpoint_provenance_license.md` §0「权重发送第三方 = 待 owner 授权（授权前不发送）」+ `.gitignore` 忽略 `*.pt`（仓库内无权重）。

### R8 第三环境运行包（可发布，保留受控说明）

| 资产 | 结论 | 依据 |
|---|---|---|
| `THIRD_ENV_RUNBOOK_2026-09-25.md` | 可发布 | task 5 交付物，含命令序列/哈希锚点/预期时长/双判据 |
| `data_manifest_LIDC_AAPM.md` | 可发布 | 数据溯源与许可说明（两层许可叠加 CC BY 3.0 + CC BY 4.0） |
| `checkpoint_provenance_license.md` | 可发布（作为受控说明） | 文档本身为授权状态说明；不授予任何权重再分发权 |
| `THIRD_PARTY_OPERATOR_GUIDE.md` | 可发布 | 第三方操作者指南 |

### R9 论文包（可发布，作者 TODO 定稿后）

| 资产 | 结论 | 依据 |
|---|---|---|
| `manuscript.tex` / `manuscript.pdf` | 可发布（先决：L23 作者、L324 CRediT、L327 利益声明由 owner 补齐；availability 段已由任务 6 草稿替换） | 作者自有；COMPLETION_CHECKLIST §8/§9 |
| `README.md` / `CLAIM_EVIDENCE.md` / `COMPLETION_CHECKLIST.md` | 可发布 | 作者自有台账 |
| `tables/*.tex` / `references.bib` | 可发布 | 作者自有 |

### R10 第三方依赖（可发布，仅清单）

| 资产 | 结论 | 依据 |
|---|---|---|
| `env_pip_freeze.txt` 所列依赖（torch 2.3.0+cu121、numpy、scipy、pydicom、h5py 等） | 可发布（仅版本清单） | 各依赖自有许可（BSD-3-Clause / MIT / Apache-2.0 / PSF 等）；随包不附带 wheel/二进制，用户按清单自行安装 |

---

## 3. 发布前 owner 需确认事项

| # | 事项 | 阻断对象 |
|---|---|---|
| 1 | 作者信息（L23）、CRediT（L324）、利益声明（L327） | manuscript 对外投稿/发布 |
| 2 | 仓库公开范围（保持私有 or 定向授权） | availability 措辞中的"corresponding author on request"是否保留 |
| 3 | 5 个 checkpoint 是否授权发送（授权范围/接收方） | checkpoint 本体交付（当前仅哈希） |
| 4 | 复算结果 JSON 是否全量附送（28 项中间结果） | 发布包体积与范围 |
| 5 | DOI 注册渠道（不建 Zenodo，另定策展渠道） | 手稿 `[DOI PLACEHOLDER]` 回填 |

---

## 4. 结论摘要

- **可随策展包分发**：43 项（A 类，含本次 3 项发布交付物）+ 哈希锚点 5 项 + 复算结果 JSON。
- **仅哈希、不分发**：LIDC 数据树 364 项（R5）、AAPM 数据树 25 项（R6）——图像数据，上游许可约束 + 任务约束。
- **仅哈希、发送需 owner 授权**：5 个 checkpoint（R7）。
- **不纳入**：`.bak` / LaTeX 编译中间产物 / WS-4 未提交代码 / 图像与权重本体。