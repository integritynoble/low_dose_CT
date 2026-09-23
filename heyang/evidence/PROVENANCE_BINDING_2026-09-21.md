# PROVENANCE_BINDING_2026-09-21

- **日期**：2026-09-21
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，工作区有未提交改动；未 commit / 未 push）
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 4（P1）—— 来源绑定：把 provenance 绑定到真正被评估的输入（模型字节 / 资产清单 / 病人映射），防提交 JSON 自报字段绕过或伪造
- **红线遵守**：未 commit / 未 push；未修改 `comparison_full764.json`、tolerance / score / registry 常量；verifier / CLI 改动保持向后兼容（新绑定默认关闭，显式开启）

---

## 1. 信任边界（任务书 §4 要求的先决文档）

| 事实 | 绑定载体 | 谁持有 | 本实现验证方式 |
|---|---|---|---|
| 提交 JSON 内部一致性 | `claim_bound_sha256` + `check_claim_bound_provenance` | 提交者 | JSON 对象哈希交叉验证（任务 3 已有） |
| **实际被评估的模型字节** | checkpoint 文件字节 SHA256 | **evaluator 运行环境** | `hashlib.sha256` 读文件字节，与 ASSET_MANIFEST / 提交声明交叉验证 |
| **资产清单成员与哈希** | `ASSET_MANIFEST.md`（A1 表 / `hashes/*.txt`） | 仓库/评估方 | 运行时解析 manifest 文件；缺哈希条目标 UNVERIFIED，**禁止伪造** |
| **病人 ID → slice/result 映射** | 固定 split 来源文件 | 数据/评估方 | 运行时解析固定来源（CSV / 名单），逐 patient_id 核对；无来源声明标 NO_BINDING |
| evaluator 版本 | `evaluator_version` | evaluator | 必须出现在 evidence 中，且与 claim 一致；缺失 → UNVERIFIED 不认证 |
| method / task / dose 身份 | 提交上下文 + claim | 提交方/evaluator | CLI 上下文（method/vendor/dose）与 claim 字段一致性核对 |

**关键边界**：本实现证明的是「**被评估对象的字节与清单/映射来源绑定一致**」，不是「源数据已被可信 evaluator 在 S3 上实际运行过」。live S3 运行时与授权数据源未就绪，该项标 BLOCKED（见 §7）。在可信 evaluator 实际运行于该源之前，不得声称 source-data authentication。

**绕过面（攻击模型）**：
1. 提交 JSON 声称模型 A、实际跑模型 B 字节（自报哈希仅证内部一致性）→ 运行时字节比对拒绝；
2. 提交 JSON 直接内嵌"PASS"快照绕过验证（手工编辑 board）→ save 时对每条带 claim 条目运行时重算，快照与运行时事实冲突即拒绝；
3. 资产清单哈希缺失/占位时"顺水推舟"→ 如实标 UNVERIFIED，不认证、不伪造；
4. 病人标签仅存于 JSON、无映射来源 → NO_BINDING/UNVERIFIED，不得视为已绑定。

---

## 2. 落点与理由

任务书指定审查 `scoring/verify.py::check_claim_bound_provenance` 及每个 add/save 路径；落点就近实现于 `WS-4_leaderboard/scoring/`：

| 落点 | 文件 | 职责 |
|---|---|---|
| **新增** `scoring/binding.py`（630 行） | 运行时输入绑定核心 | 三类绑定 + identity 绑定 + 组合检查 `check_input_binding` |
| 修改 `scoring/verify.py`（+55 行） | 任务书点名审查点 | 新增 `check_input_bound_provenance`，接入 S2 管线（默认 `bind_inputs=False` 保兼容） |
| 修改 `scoring/leaderboard.py`（任务 4 部分） | add/save 路径 | `add_submission` 计算绑定快照；`save()` 写盘前运行时重算防直存伪造；receipt v2 记录 input_binding 摘要 |
| 修改 `scoring/cli.py`（任务 4 部分） | CLI 暴露 | 新增只读 `provenance-check`；`verify-bundle` / `publication-status` 增加 `--bind-inputs` / `--provenance-detail` |
| 修改 `scoring/__init__.py`（+6 行） | 导出 | 导出 binding 模块与两个 check 函数 |
| **新增** `scoring/tests/test_input_binding.py`（447 行） | 测试 | 19 个用例：正向 + 攻击 |

理由：绑定判定需同时被 ①S2 校验管线、②CLI 提交、③直接 save 三条路径共享，故独立成 `binding.py` 模块而非塞进既有 JSON 一致性校验；默认关闭开关保证任务 3 已发布的 verifier / CLI 行为不变（向后兼容红线）。

---

## 3. 三类绑定实现逻辑

### 3.1 模型字节（`check_model_bytes`）

- 从 claim/evidence 取 checkpoint 引用（`model_weights.checkpoint` 或 `model_file_sha256` 携带的文件名），无具体文件引用 → `UNVERIFIED: NO_REFERENCE`。
- **清单成员**：解析 ASSET_MANIFEST，若引用文件不在清单 → `FAIL: NOT_IN_MANIFEST`（防"换 manifest 成员"）。
- **字节比对**：`hashlib.sha256` 读运行时文件字节（`checkpoint_dir` / `bundle_dir`），与清单声明哈希比对：
  - 文件缺失 → `FAIL: FILE_MISSING`；
  - 字节哈希 ≠ 清单哈希 → `FAIL: MANIFEST_MISMATCH`（防"JSON 声称模型 A、实际跑模型 B"）；
  - 清单哈希为空/占位符（`-` / 空 / 非 64 位十六进制）→ `UNVERIFIED`（如实标记不可验证，**不伪造哈希值**，不 PASS）。
- 另与提交声明哈希（`claim.model_file_sha256`）交叉验证，声明缺失或与字节不符 → 相应 UNVERIFIED/FAIL。

### 3.2 资产清单（`check_asset_manifest_binding`）

- 运行时解析 `ASSET_MANIFEST.md`（A1 表 `| \`name.pt\` | size | source | \`HASH\` |`）或 `hashes/*.txt`（`HASH  <path>` / `name=HASH`）两种格式（`parse_asset_manifest`）。
- evidence 声明的 model_weights / data_manifest 成员逐项与 manifest 核对：
  - 成员不在清单 → `FAIL`（changed manifest membership）；
  - 成员在清单但哈希占位/缺失 → `UNVERIFIED`（不可验证，如实标记）；
  - 清单中**多余**的高危资产（如未被 evidence 引用的 checkpoint）→ 记入 unverified 提示，不 PASS 掩盖。
- 占位符哈希（`-` / 空 / 非法格式）一律解析为 `None`，**绝不猜测或补填**。

### 3.3 病人映射（`check_patient_mapping_binding`）

- 仅当 claim 声明 `bootstrap_level == "patient"`（或携带 patient bootstrap 声明）时启用：
  - 声明 `patient_source` 指向固定来源文件（如 `splits/split_assignment.csv`、`aapm_test.txt` 等），运行时读取并建立**允许的 patient_id 集合**（CSV 列解析 / 逐行名单解析）；
  - result/entry 的 `patient_ids` 逐项核对：任一不在固定来源 → `FAIL`（伪造/不一致映射）；
  - 声明了 `patient_source` 但来源文件不存在/解析为空 → `FAIL`（claim 指向不存在的源）或 UNVERIFIED（无法证实）；
  - `patient_ids` 缺失 → `FAIL`（声明了 patient bootstrap 却无映射证据）；
  - 提交 JSON 内自报映射表与固定来源冲突 → `FAIL`（JSON 不得覆盖固定来源）。
- 未声明 patient 级 bootstrap → `UNVERIFIED: NO_BINDING_DECLARED`（**NO_BINDING**，如实标注，不视为已绑定）。

### 3.4 身份绑定（`check_identity_binding`，evaluator-owned 证据）

- claim 与提交上下文（CLI 的 method/vendor/dose）三方一致核对：不一致 → `FAIL`（wrong method/task/dose binding）。
- `evaluator_version` 必须出现在 **evidence**（evaluator-owned）且与 claim 一致：evidence 缺失 → `UNVERIFIED`（不认证、不硬拒，保旧 fixture 兼容）。

### 3.5 组合与状态

`check_input_binding` 汇总四类检查 → `BindingResult{status, checks, details, violations, unverified}`：
- 任一 `FAIL` → status=FAIL（S2 硬拒 / save 拒绝 / CLI 退出 1）；
- 无 FAIL 但有 UNVERIFIED → status=UNVERIFIED（保持 pending/未验证，**不得标为已发布或已验证**）；
- 全部 PASS → status=PASS。

### 3.6 防直存绕过（save 路径）

- `add_submission`：计算绑定快照写入 `entry.provenance.input_binding` + `patient_ids`（提交时的运行时事实）。
- `save()`（写盘前）：
  1. `_save_gate_violations` 对带 claim 条目重验 claim 内部一致性 + method/vendor/dose 身份一致性 + **快照绑定状态**（快照 FAIL 即拒绝）；
  2. 对每条带 claim 条目用**当前运行时文件系统**重算 `check_input_bound_provenance`：
     - 运行时 violations → 拒绝 save，写 `*.failed.json` 诊断；
     - 无 violations → 用运行时重算结果**替换**存储快照（手改的 "ok" 快照无法存活于文件系统事实之外）；
  3. 全部通过后写 receipt v2，含 `input_binding` 摘要（entries/pass/unverified/fail 计数）。
- 无 claim 快照的历史条目不触碰（保持历史行为）。

---

## 4. CLI / 接口用法

### 4.1 `python -m scoring.cli provenance-check`（新增，只读）

```
python -m scoring.cli provenance-check --result <result.json> \
    --method <method> --vendor <vendor> --dose <dose> \
    [--checkpoint-dir <dir>] [--manifest <ASSET_MANIFEST.md>] [--splits-dir <dir>] \
    [--bundle <runbundle_dir>] [--json]
```

只读报告：status==PASS 且无 claim 违规 → 退出 0；否则退出 1。不写任何盘。

### 4.2 `verify-bundle --provenance-detail` / `--bind-inputs`（向后兼容）

```
python -m scoring.cli verify-bundle --bundle <runbundle_dir> --provenance-detail
python -m scoring.cli verify-bundle --bundle <runbundle_dir> --bind-inputs
```

- 不传 → 行为与任务 3 完全一致（S1–S4 原逻辑）；
- `--provenance-detail` → 追加只读绑定报告，不改变 S2 判定；
- `--bind-inputs` → S2 强制绑定检查，绑定 FAIL 即 REJECT。

### 4.3 `publication-status --bind-inputs`

board 读取时追加运行时绑定状态展示；仅显示，不改变已存证据。

### 4.4 Python API

```python
from scoring import check_input_bound_provenance, new_leaderboard, add_submission, save

ctx = {"checkpoint_dir": "...", "manifest_path": "...", "splits_dir": "..."}
binding = check_input_bound_provenance(result, method=..., vendor=..., dose=..., **ctx)
board = new_leaderboard()
add_submission(board, result, method=..., vendor=..., dose=..., binding_context=ctx)
save(board, "board.json", binding_context=ctx)   # save 前运行时重算
```

---

## 5. 本机 Windows 实跑记录（命令 / 退出码 / 输出摘录）

环境：Windows 11（Build 26100），默认 python 3.11.8（Marvis runtime），`$env:PYTHONUTF8=1`，工作目录 `WS-4_leaderboard`。demo fixture 置于会话中间目录 `temp/task4_demo/`（含 `checkpoints/red_cnn.pt`、`ASSET_MANIFEST.md`（真实 SHA256）、`splits/split_assignment.csv` + `aapm_test.txt`）。

### A. 有效 evaluator-produced fixture → PASS（退出 0）

```
$ python -m scoring.cli provenance-check --result task4_demo/result_valid.json \
    --method red_cnn --vendor Siemens --dose r025 \
    --checkpoint-dir task4_demo/checkpoints --manifest task4_demo/ASSET_MANIFEST.md \
    --splits-dir task4_demo/splits
input binding: PASS
  model_bytes:     PASS -- model_bytes: BOUND 'red_cnn.pt' SHA256 DF25E6F6846A... (method label 'red_cnn' differs from checkpoint name)
  asset_manifest:  PASS -- asset_manifest: 'red_cnn.pt' listed with SHA256 DF25E6F6846A...
  patient_mapping: PASS -- patient_mapping: 2 patient_id(s) bound to fixed split source '...\splits\split_assignment.csv'
  identity:        PASS -- identity: BOUND
exit=0
```

### B. 攻击：claim 改指清单外模型（changed manifest membership）→ FAIL（退出 1）

```
$ python -m scoring.cli provenance-check --result task4_demo/result_attack.json ...（同参数）
input binding: FAIL
  model_bytes: FAIL -- model_bytes: NOT_IN_MANIFEST
  asset_manifest: FAIL -- asset_manifest: NOT_IN_MANIFEST
  FAIL: model_bytes: model 'ctformer.pt' is not a member of ASSET_MANIFEST (changed manifest membership: the claim names a checkpoint the manifest does not list)
  FAIL: asset_manifest: asset manifest binding: 'ctformer.pt' is not listed in ASSET_MANIFEST (changed manifest membership)
exit=1
```

### C. 攻击：提交后 checkpoint 文件字节被篡改 → FAIL（退出 1）

```
$ python -m scoring.cli provenance-check --result task4_demo/result_valid.json ...（改 red_cnn.pt 字节后）
input binding: FAIL
  model_bytes: FAIL -- model_bytes: MANIFEST_MISMATCH
  FAIL: model_bytes: model bytes changed: 'red_cnn.pt' SHA256 6B472E65EB4D... != ASSET_MANIFEST DF25E6F6846A... (the file bytes actually present are not the manifest's checkpoint)
exit=1
```

### D1. 直存：伪造 PASS 快照 + manifest 哈希为占位符 → 降级 UNVERIFIED（可写 pending，不认证）

```
D1 direct-save forged PASS snapshot, placeholder manifest hash:
  recomputed input_binding.status = UNVERIFIED
  checks = {'model_bytes': 'UNVERIFIED', 'asset_manifest': 'UNVERIFIED', 'patient_mapping': 'PASS', 'identity': 'PASS'}
  receipt.input_binding = {'entries': 1, 'pass': 0, 'unverified': 1, 'fail': 0}
  -> snapshot replaced by runtime recompute; result stays UNVERIFIED/pending, never certified
```

### D2. 直存：伪造 PASS 快照 + 字节被篡改（真实清单哈希）→ save 拒绝 + failed 诊断

```
D2 direct-save forged PASS snapshot + tampered checkpoint bytes refused (ValueError):
  board not publishable: entry 'forged-entry': runtime input binding contradicts the provenance snapshot:
    model_bytes: model bytes changed: 'red_cnn.pt' SHA256 95640EF8D3B8... != ASSET_MANIFEST DF25E6F6846A...
  failed diagnostic written: board_forged_tampered.json.failed.json = True
```

### E. verify-bundle --provenance-detail（任务 3 fixture `runbundle_skipped_live`，向后兼容只读）→ 退出 1（如实反映未绑定）

```
S1: PASS   S2: PASS   S3: SKIPPED   S4: SKIPPED
input binding:
  model_bytes: FAIL -- NOT_IN_MANIFEST
  asset_manifest: FAIL -- NOT_IN_MANIFEST
  patient_mapping: UNVERIFIED -- NO_BINDING_DECLARED
  identity: UNVERIFIED -- UNVERIFIED
exit=1
```

（fixture 的 `model.pt` 不在本机 manifest → 如实 FAIL，不伪造绑定。）

### F. verify-bundle --bind-inputs（强制绑定）→ REJECT（退出 1）

```
verify-bundle: REJECT (S2: 2 violation(s))
  - model_bytes: model 'model.pt' is not a member of ASSET_MANIFEST ...
  - asset_manifest: asset manifest binding: 'model.pt' is not listed in ASSET_MANIFEST ...
```

### 全量回归

```
$ python -m pytest scoring/tests ../WS-1_dataset/analysis/tests -q -rs -p no:cacheprovider
389 passed, 10 skipped in 9.10s
exit=0
```

（10 skipped 均为历史 session 脚本缺失，与任务 2 收据一致。）

---

## 6. 测试记录（test_input_binding.py，19 用例）

| 用例 | 期望 | 结果 |
|---|---|---|
| 有效 fixture：模型/清单/病人/身份全 PASS | PASS | PASS |
| add_submission + save 全链路通过（receipt input_binding 摘要） | PASS | PASS |
| 攻击：checkpoint 文件字节篡改 | FAIL（MANIFEST_MISMATCH） | FAIL |
| 攻击：evidence 改指清单外模型（成员变化） | FAIL（NOT_IN_MANIFEST） | FAIL |
| 占位符清单哈希（`-`） | UNVERIFIED，不伪造 | UNVERIFIED |
| 攻击：method 上下文与 claim 不一致 | FAIL | FAIL |
| 攻击：dose / vendor / evaluator_version 不一致 | FAIL / UNVERIFIED（缺证据不硬拒） | 符合 |
| 病人 bootstrap 声明无来源 | UNVERIFIED（NO_BINDING） | UNVERIFIED |
| 攻击：patient_id 不在固定来源 | FAIL | FAIL |
| 攻击：JSON 自报映射与固定来源矛盾 | FAIL | FAIL |
| 无 bootstrap 声明 | UNVERIFIED（NO_BINDING_DECLARED） | UNVERIFIED |
| 攻击：直存伪造 PASS 快照（字节篡改） | save 拒绝 + failed 诊断 | 拒绝 |
| 占位 manifest 直存伪造快照 | 降级 UNVERIFIED 可写不认证 | 降级 |
| 提交后字节变更再 save | save 拒绝 | 拒绝 |
| 无 binding_context 的旧 board save | 保持历史行为 | 通过 |

开发过程「先红后绿」：首跑 6 failed / 13 passed（暴露 ①`_save_gate_violations` 未传 patient_ids 致 bootstrap 声明误报、②伪造快照 entry 缺 evaluator_version/task 字段）；修正 leaderboard 与 fixture 后 19 passed。修正后全量 389 passed / 10 skipped。

---

## 7. BLOCKED 项

| 项 | 原因 |
|---|---|
| live S3 运行时绑定验证 | 需要容器/数据机运行时与授权数据源；本机无 torch/GPU 依赖，无法运行实际推理。文件级哈希校验无需 GPU（hashlib 读字节即可），已在本机完成 |
| 真实参考 checkpoint 清单绑定 | 仓库真实 checkpoint 位于受控机器，本机仅有 demo 字节级 fixture；真实绑定需在资产机器执行同一 `provenance-check` |
| source-data authentication 声明 | 按任务书：可信 evaluator 未在该源实际运行前，不得如此描述；本实现只证明字节/清单/映射一致性 |

---

## 8. 改动文件清单（任务 4 范围；未 commit / 未 push）

| 文件 | 类型 | 行数 |
|---|---|---|
| `WS-4_leaderboard/scoring/binding.py` | 新增 | 630 |
| `WS-4_leaderboard/scoring/tests/test_input_binding.py` | 新增 | 447 |
| `WS-4_leaderboard/scoring/verify.py` | 修改 | +55（check_input_bound_provenance + S2 接入） |
| `WS-4_leaderboard/scoring/leaderboard.py` | 修改 | 任务 4 部分（add/save 绑定快照 + 运行时重算 + receipt v2；其余为任务 3 内容） |
| `WS-4_leaderboard/scoring/cli.py` | 修改 | 任务 4 部分（provenance-check + --bind-inputs/--provenance-detail；其余为任务 3 内容） |
| `WS-4_leaderboard/scoring/__init__.py` | 修改 | +6（导出） |

**工作区其余未提交改动不属于本任务**：`Heyang-paper/manuscript.tex` / `README.md`（任务 1）、`WS-2_framework/.../reproducible_manifest.json`、`web/app.js|index.html|style.css`、`scoring/verifier.py`（任务 3）、`tests/test_publication_status.py`、`tests/fixtures/publication/`（任务 3）。全部改动均保留在 `heyang` 工作区，未 commit / 未 push / 未删除文件。

---

## 9. 结论

- **落点**：`WS-4_leaderboard/scoring/`（新增 `binding.py`，接入 verify.py S2、leaderboard.py add/save、cli.py）。
- **三类绑定闭环**：模型字节（运行时 SHA256 文件字节 vs 清单/声明）、资产清单（运行时解析 manifest，占位哈希标 UNVERIFIED 不伪造）、病人映射（绑定固定来源文件，JSON 不得覆盖；无来源标 NO_BINDING）——全部基于运行时实际计算，不信任 JSON 自报；校验失败状态反映为 FAIL/UNVERIFIED，绝不标为已验证/已发布。
- **攻击用例测试结果**：19 个测试全通过（改模型字节拒 / 改 manifest 成员拒 / 错 method-task-dose 绑定拒 / 缺源或不一致病人映射拒 / 直存伪造快照拒 / 占位哈希降级 UNVERIFIED / 有效 fixture 通过）；全量回归 389 passed / 10 skipped。
