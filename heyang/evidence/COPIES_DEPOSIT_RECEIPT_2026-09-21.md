# COPIES_DEPOSIT_RECEIPT_2026-09-21

- **日期**：2026-09-21
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 5b —— 已授权 off-machine substrate 副本与 deposit dry-run 收据（对应 HEYANG_NEXT_2026-09-13.md §4–4b）
- **红线遵守**：全程只读；未修改两仓库任何文件；未 commit / 未 push；大型二进制仅计算哈希未搬运；所有哈希为 2026-09-21 实测值

---

## 0. 副本口径

任务书 §4/§4b 定义的副本为 **v0.5 substrate（仅存在于本工作站的 LIDC 数据底座）**，即：

```
annotations/          （含 lidc_majority_vote/ 与 raw_per_reader/）
sim_lowdose/lidc/     （本机实际路径名为 hdf5/，见 §3 BLOCKED 说明）
metadata/
splits/
deident_audit.jsonl
```

- **源位置（实测确认）**：`D:\ZHY\LIDC3DDataSet\output_gpu`，共 **364 个文件**（50 `.h5` + 300 `.json` + 8 `.log` + 4 `.txt` + 1 `.sha256` + 1 `.jsonl`），与 R6 manifest `data_hashes.txt` 的 364 项完全对应。
- **目标位置**：任务书 §4b 指定的 OneDrive 共享文件夹（Teams 链接，share token 刻意不写入仓库；本机 `C:\Users\ufl\OneDrive` 下**未发现**已完成的 off-machine 副本，见 §3）。
- 另按当前任务目标补充两个仓库（`low_dose_CT-heyang` / `ldct_agent-main`）工作区的可复算交付盘点，作为收据佐证。

---

## 1. 脱敏清单（redacted manifest）

### 1.1 禁止入副本的项（源树中已确认存在）

| 项 | 数量/大小 | 脱敏依据 |
|---|---|---|
| AAPM/Mayo harmonized HDF5（`aapm-00NN_*_fd.h5`）| 10 个，共约 5.1 GB（`WS-1_dataset/pipelines/_runtime/aapm_tree_v1`）| 任务书 §4b：与 `stage_deposit.py` 拒绝 staging 的三类一致，DUA 受限，不得进入链接共享通道 |
| DICOM 文件 | 0（源树中不存在）| 任务书 §4b + `.gitignore` |
| `LNNN_*.npy/npz` | 0（源树中不存在）| 任务书 §4b + `.gitignore`（`**/L[0-9][0-9][0-9]_*.npy/npz`）|
| Mayo 数组 | 0（历史已从仓库移除，2026-09-05）| `.gitignore` 注释 + 任务书 §4b 禁止 reintroduce |
| model checkpoints（`*.pt`）| 5 个权重，约 0.37 GB（位于 `WS-1_dataset/baselines/checkpoints/`（git 未跟踪）与外部 Doubao 路径）| 红线：大二进制只算哈希不搬运；`ckpt_hashes.txt` 已记录 SHA256 |
| 私有文件系统标识 | 源树路径含 `C:\Users\ufl\Doubao\...` 等 | 任务书 §5：private filesystem identifiers 不入公开仓库 |

### 1.2 不写入仓库的项（本收据及任何产出中均不出现）

| 项 | 说明 |
|---|---|
| OneDrive/Teams share token | 任务书 §4b 刻意不写入公开仓库；本收据未包含 |
| 受限图像（DICOM / Mayo / AAPM 像素）| 全程未读取、未复制、未引用路径细节 |
| 私有文件系统标识 | 上表检查点权重外部路径仅以"外部 Doubao 路径"指代 |

### 1.3 脱敏规则依据

- 任务书 HEYANG_NEXT_2026-09-13.md §4/§4b（三类拒绝项 + share token 不入仓库）
- 任务书 HEYANG_NEXT_2026-09-20.md 任务 5（redacted manifest；share tokens / restricted images / private filesystem identifiers 不入公开仓库）
- 仓库 `.gitignore`（DUA-restricted AAPM/Mayo、`LNNN_*.npy/npz`、`WS-1_dataset/baselines/checkpoints/`、`pipelines/_runtime/`）
- `stage_deposit.py` 内置三类拒绝逻辑

---

## 2. 文件数 / 校验和

### 2.1 v0.5 substrate（副本主体）

**源目录**：`D:\ZHY\LIDC3DDataSet\output_gpu`，实测 **364 个文件 / 24.4 GB（仅 h5 合计）**

| 类别 | 文件数 | 说明 |
|---|---|---|
| `.h5` | 50 | hdf5/test 9 + train 32 + val 9；LIDC 模拟低剂量（`lidc-*_fd.h5`）|
| `.json` | 300 | annotations/lidc_majority_vote 50 + annotations/raw_per_reader 200 + metadata 50 |
| `.log` | 8 | 构建日志 |
| `.txt` | 4 | pid.txt + splits/{test,train,val}.txt |
| `.sha256` | 1 | manifest.sha256（303 项，仅覆盖 annotations/metadata/splits）|
| `.jsonl` | 1 | deident_audit.jsonl |

**SHA256 全量清单**：`[checksums_substrate_364_2026-09-21.txt](<C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\checksums_substrate_364_2026-09-21.txt>)`（364 项全量实测，与 R6 manifest `data_hashes.txt` 逐项比对 364/364 MATCH）

### 2.2 仓库工作区盘点（可复算交付视角）

| 仓库 | 分支 / HEAD | git 跟踪文件数 | 未提交变更 |
|---|---|---|---|
| `D:\ZHY\low_dose_CT-heyang` | heyang `3472815abcfa7c6faf2679a75f27e5c9cf250e83` | **888** | 15 项（既有本地工作，未 commit/push，见 §3）|
| `D:\ZHY\ldct_agent-main` | heyang `c2a75c5953aecd911877f8a667efd9d29a384b3d` | **39** | 0 项（干净）|

**CT 仓库按顶层目录**：WS-1_dataset 605 / WS-2_framework 85 / WS-3_reference_method 68 / WS-4_leaderboard 55 / WS-2b_pet_phantom 13 / Heyang-paper 9 / data_acquisition 9 / .github 7 / pwm_integration 5 / scripts 2 / 其他根级文档若干。

**CT 仓库大文件（git 跟踪）**：`WS-1_dataset/baselines/vendor/LEARN/examples/LEARN_TrainingCodes/proMatrix_64.mat`（81.0 MB，vendor 附带素材）。其余跟踪文件均 <10 MB；checkpoint 权重未被 git 跟踪。

**agent 仓库**：39 个跟踪文件全部 <10 MB。

**SHA256 清单**：
- CT 关键 artifact/清单/脚本：`[checksums_ct_key_artifacts_2026-09-21.txt](<C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\checksums_ct_key_artifacts_2026-09-21.txt>)`
- agent 全量跟踪文件：`[checksums_ldct_agent_2026-09-21.txt](<C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\checksums_ldct_agent_2026-09-21.txt>)`

关键 artifact 哈希摘要（完整见清单文件）：

| artifact | SHA256（实测）|
|---|---|
| `WS-1_dataset/R6_recalc/results/comparison_full764.json` | `065b7b99f9123c8ebabd9907140f6da7a3f43055affad5edb08ee7f3ee25c852` |
| `Heyang-paper/manuscript.tex` | `0068cab87def19472ddf737b74073c170780ac0d18c4fc744130f45e782835d1` |
| `WS-1_dataset/physionet_listing/stage_deposit.py` | `fc08533686bd9baf0fdeefd01182b1adfe2beeceb7ac7fdd40fbcc71a28f2873` |
| `WS-1_dataset/R6_recalc/hashes/data_hashes.txt` | `1f41b875e68861a5a73de4d2d4ab7ab467d4d831691515f23accb82383bf8a6b` |

---

## 3. 验证结果

| # | 验证项 | 结果 | 证据 |
|---|---|---|---|
| V1 | substrate 全量 SHA256 与 R6 manifest 一致性 | **PASS**（364/364 MATCH）| `data_hashes.txt` 逐项实测比对，mismatch=0 |
| V2 | substrate 内嵌 manifest.sha256 一致性 | **PASS**（303/303 MATCH）| `output_gpu/manifest.sha256` 逐项实测比对 |
| V3 | checkpoint 权重 SHA256 与 `ckpt_hashes.txt` 一致性 | **PASS**（5/5 MATCH）| corediff/ctformer/ctformer_small_retrain/learn/red_cnn 实测比对 |
| V4 | task_spec 哈希与 `task_spec_hash.txt` | **PASS**（`AE7AE799…2D4C`）| `WS-1_dataset/baselines/task_spec.json` 实测 |
| V5 | deposit dry-run（`stage_deposit.py --dry-run`）| **PASS（含 1 个缺失警告）** | 无 DUA 拒绝（源树 0 个受限类）；报告 missing `sim_lowdose/lidc`（见 M1）|
| V6 | 两仓库 git 状态 | **CT：非干净（15 项未提交）/ agent：干净** | CT 未提交项均为既有本地工作（Heyang-paper prose 修改 + WS-4 scoring/web 开发），符合红线不 commit/push；agent 0 项 |
| V7 | off-machine 副本状态 | **BLOCKED** | 本机 `C:\Users\ufl\OneDrive` 下未发现已完成的 v0.5 substrate 副本；share token 不在仓库/本机可读取（任务书 §4b 刻意不写入） |

### 缺失/拒绝清单（dry-run missing / refused）

| 项 | 类型 | 说明 |
|---|---|---|
| `sim_lowdose/lidc`（deposit 期望路径）| **缺失（命名差异）** | 源树中 50 个 `.h5` 实际位于 `hdf5/`（test/train/val）而非 `sim_lowdose/lidc/`；`stage_deposit.py` 按期望路径报告 missing。需 owner 确认：组装 deposit 时是否将 `hdf5/` 映射/重命名为 `sim_lowdose/lidc/`，或调整 staging 规则 |
| OneDrive 目标副本 | **缺失/未完成（BLOCKED）** | 本机未发现已落盘的 off-machine 副本；任务书明确"未检查收据不得声称副本已完成"，故如实标注 BLOCKED |
| `aapm-00NN_*_fd.h5`（10 个）| **拒绝入副本** | DUA 受限（任务书 §4b + stage_deposit.py 拒绝逻辑）；仅计算哈希未搬运 |
| DICOM / `LNNN_*.npy/npz` / Mayo 数组 | **拒绝入副本（源树 0 个）** | 同上三类；`.gitignore` 亦排除 |
| model checkpoints（`*.pt`，5 个）| **拒绝入副本** | 大二进制（约 0.37 GB）+ 外部私有路径；`ckpt_hashes.txt` 已记录 |
| OneDrive/Teams share token | **拒绝写入任何产出** | 任务书 §5 |

---

## 4. 结论

- **副本口径**：任务书 §4/§4b 定义的 v0.5 substrate（`D:\ZHY\LIDC3DDataSet\output_gpu`，364 文件 / h5 合计 24.4 GB）。
- **文件数**：substrate 364；CT 仓库 888（跟踪）；agent 仓库 39（跟踪）。
- **校验和**：substrate 364/364、manifest.sha256 303/303、checkpoint 5/5、task_spec 1/1 全部实测 MATCH；3 份 checksums 清单已落盘（输出目录）。
- **验证**：V1–V5 PASS；V6 CT 有 15 项既有未提交本地工作（不 commit/push）；V7 off-machine 副本 **BLOCKED**（本机未发现 OneDrive 副本）。
- **缺失/拒绝**：deposit dry-run 报 `sim_lowdose/lidc` 命名差异缺失（需 owner 决策）；10 个 AAPM fd.h5、DICOM/npy-npz/Mayo、checkpoint、share token 均拒绝入副本。

**状态判定**：收据本身 **COMPLETE**（证据充分）；副本动作 **BLOCKED**（目标不可达/未落盘，缺 OneDrive 共享访问）。未将科学验收或任何 PASS 扩展为超出本任务范围的结论。
