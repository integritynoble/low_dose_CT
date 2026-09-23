# RELEASE_STATUS_VISIBILITY_2026-09-21

- **日期**：2026-09-21
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 3（P1）—— prototype publication states visible and testable
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，HEAD `3472815`，工作区未 commit / 未 push）
- **关联仓库**：`D:\ZHY\ldct_agent-main` 不在本任务落点内（见 §7 BLOCKED）
- **红线遵守**：未修改 BandER direction / dose margins / R6 tolerance；未引入发布服务或部署页面；未 commit / push；未安装依赖 / 未 clone 共享核心；截图与 fixtures 不含患者图像

---

## 1. 落点与理由

任务书原文指定：*Audit `WS-4_leaderboard/web/`, `scoring/verifier.py`, the CLI and saved-board receipts together.* 因此落点全部在 CT 仓库 WS-4：

| 落点 | 文件 | 改动性质 |
|---|---|---|
| 状态机（五态分类核心） | `WS-4_leaderboard/scoring/verifier.py` | 新增 `PublicationStatus`、`PUBLISH_*` 常量、`board_publication_status` / `verdict_publication_status` / `entry_publication_status` |
| CLI 必交付 | `WS-4_leaderboard/scoring/cli.py` | 新增 `publication-status` 子命令（`--leaderboard / --bundle / --json / --skip-ws1-gates`） |
| UI 可见性 | `WS-4_leaderboard/web/app.js`、`index.html`、`style.css` | 发布状态横幅 + 表格发布状态徽章列 + 五态样式 |
| fixtures / 验收 | `WS-4_leaderboard/scoring/tests/test_publication_status.py` + `tests/fixtures/publication/` | 六类验收用例 + 23 条断言 |

**理由**：
1. 任务书指定审计对象即这些文件（web、verifier、CLI、saved-board receipts），无歧义；
2. 发布状态必须同时被 CLI 与 UI 读取同一份判定逻辑，故把状态机放在 `verifier.py`（CLI/UI 共用的唯一判定源），UI 侧 `app.js` 以同一状态机语义镜像渲染（无后端服务、纯静态回退）；
3. saved-board receipts（`leaderboard.py::save()` 写的 `receipt` + `publication` 块、拒绝时写的 `<path>.failed.json`）是判定依据，故 fixtures 直接使用真实 save 语义生成。

## 2. 状态机 / 分类逻辑

### 2.1 五态定义

| 状态常量 | 输出 state | 含义 | 判定条件（按优先级） |
|---|---|---|---|
| `PUBLISH_NO_CLAIM` | `NO_CLAIM` | 无发布声称 | board 无 receipt 且无 publication 块（含空对象）；entry 为 trap / placeholder |
| `PUBLISH_MISSING_LAYER` | `MISSING_LAYER` | 缺发布层 | `trap_rank_by_vendor.verdict == "MISSING_STRATUM"`（缺 metadata / license / weights 等任一发布层以所需 vendor strata 未全覆盖为代表） |
| `PUBLISH_INCOMPLETE` | `INCOMPLETE` | 声明了但内容不完整 | receipt 存在但 publication 缺失/空；`publication.status` 为 pending 等非终态；**`status` 写 "published" 但无 referee 证据**（提交者自标 flag 不被信任）；verdict 有 SKIPPED stage（S3/S4 未跑） |
| `PUBLISH_REJECTED` | `REJECTED` | 已拒绝 | `publication.status == "rejected"`；board 旁存在 `<path>.failed.json` 拒绝保存诊断；receipt.gate 任一项 FAIL/INDETERMINATE；`trap_rank*` 判定 FAIL/INDETERMINATE；verdict 存在 violations |
| `PUBLISH_PUBLISHED` | `PUBLISHED` | 已发布 | `publication.status == "published"` 且 **`publication.referee_evidence` 含 referee / verified_at / evidence_sha256**（referee 验证证据，非提交者 flag） |

### 2.2 硬约束落实

- 任何 `pending` / `skipped` / `BLOCKED` 项：`published=False` 且 `verified=False`（测试 `test_hard_constraint_nothing_nonpublished_is_published_or_verified` 对 7 个 fixture 全量断言）。
- `unverified_flag.json`（`publication.status="published"` 但无 referee_evidence）→ `INCOMPLETE`，`published=False`、`verified=False`（负面用例，防提交者自标绕过）。
- RunBundle 级：S3（live execution）被 SKIPPED → `INCOMPLETE` 且 `published=False`；S1-S4 全部通过仅代表"可发布"，未落板保存 + referee 证据前仍为 `INCOMPLETE`（不把"验证通过"当"已发布"）。
- CLI 输出同时给出 `state` / `published` / `verified` 三个字段，任何非 `PUBLISHED` 状态三者不会出现 published/verified 为真的组合。

### 2.3 判定优先级（verifier.py `board_publication_status`）

1. `<path>.failed.json` 拒绝保存诊断 → REJECTED
2. `publication.status == "rejected"` → REJECTED
3. receipt.gate / trap_rank / trap_rank_by_vendor 任一 FAIL/INDETERMINATE → REJECTED
4. 无 receipt 且无 publication（含空对象）→ NO_CLAIM
5. `status == "published"`：有 referee_evidence → PUBLISHED；否则 → INCOMPLETE（不信任自标）
6. `trap_rank_by_vendor.verdict == "MISSING_STRATUM"` → MISSING_LAYER
7. 其余未完成（pending / 空 status 等）→ INCOMPLETE

UI（`app.js::publicationState`）按同一优先级镜像实现，并额外读取 `loadBoard` 时同源 `<src>.failed.json`，保证"被拒绝保存的板"在页面上显示 REJECTED 而非无声称。

## 3. CLI 用法与示例输出

### 3.1 命令

```text
# 板级（leaderboard / saved board）五态
python -m scoring.cli publication-status --leaderboard <board.json> [--json]

# RunBundle 级（verifier S1-S4 管线，发布前校验）
python -m scoring.cli publication-status --bundle <runbundle_dir> [--skip-ws1-gates] [--json]

# 不传 --json 时为人类可读文本；传 --json 输出机器可读 JSON（含 state/published/verified/entries/stages）
```

### 3.2 示例输出（文本模式，`--leaderboard scoring/tests/fixtures/publication/pending.json`）

```text
[leaderboard] pending.json
  publication state : INCOMPLETE
  published         : False   (hard constraint: pending is never published)
  verified          : False
  detail            : publication.status='pending'; not released
```

### 3.3 示例输出（JSON 模式，`--leaderboard .../published.json --json` 关键字段）

```json
{
  "kind": "leaderboard",
  "path": ".../published.json",
  "state": "PUBLISHED",
  "published": true,
  "verified": true,
  "receipt_present": true,
  "evidence": {"referee": "ws4-referee/v1", "verified_at": "2026-09-21T00:00:00Z", "evidence_sha256": "…"},
  "entries": [{"id": "…", "state": "NO_CLAIM", "published": false, "verified": false}, …]
}
```

## 4. UI 变更

- 页面顶部新增发布状态横幅 `#pub-banner`（类 `pub-<state>`），显示五态中文标签 + 判定 detail + 提示语：
  - 非 published：*"当前为预览/未发布视图：收据不等于发布，待定或未验证内容不会标记为已发布。"*
  - published：*"此视图基于 referee 验证证据（非提交者自标 flag）。"*
- 表格新增"发布状态"列（末列），每行渲染 `pub-badge`（trap/占位恒为 NO_CLAIM，submission 继承板级状态）。
- `style.css` 新增五态底色徽章样式。
- API 回退保持原型标注（`API_SOURCES` 仍为占位 `/api/leaderboard` → 本地 `../scoring/data/leaderboard.json`），未部署页面、未发明发布服务。

### 4.1 截图（Windows 本机 Edge headless 渲染 fixtures 静态预览页）

7 张截图对应六类验收 + 1 负面用例，位于 `output/screenshots/`：

| 文件 | 横幅状态 | 预期 |
|---|---|---|
| `no_status.png` | 未发布 · 无声称 | NO_CLAIM |
| `pending.png` | 未发布 · 不完整 | INCOMPLETE |
| `missing_strata.png` | 未发布 · 缺层 | MISSING_LAYER |
| `rejected.png` | 未发布 · 已拒绝 | REJECTED |
| `failed_gate.png` | 未发布 · 已拒绝 | REJECTED（.failed.json 诊断） |
| `published.png` | 已发布 | PUBLISHED（referee 证据） |
| `unverified_flag.png` | 未发布 · 不完整 | INCOMPLETE（自标 published 不信任） |

截图经视觉模型复核：七张横幅状态全部符合预期，无 skipped/pending 案例被标为已发布。截图仅含数值表格，无患者图像。

## 5. 测试记录（Windows 本机原生）

环境：Windows 11（Build 26100）、PowerShell 5.1、`$env:PYTHONUTF8=1`。

### 5.1 新增验收测试

```text
cd WS-4_leaderboard
python -m pytest scoring/tests/test_publication_status.py -q -rs -p no:cacheprovider
23 passed in 0.11s   (exit=0)
```

覆盖：五态（missing status → NO_CLAIM / pending → INCOMPLETE / missing strata → MISSING_LAYER / rejected → REJECTED / failed-gate → REJECTED / valid publication → PUBLISHED）、负面用例（submitter flag 无 referee 证据 → INCOMPLETE）、硬约束（7 fixture 全量 published/verified 为 False）、entry 级（trap/占位 NO_CLAIM、submission 继承板级）、verdict 级（skipped live → INCOMPLETE + S3=SKIPPED；violations → REJECTED；S1-S4 全过仍非 published）、CLI 集成（7 fixture 参数化 JSON 输出断言 + 硬约束 + bundle skipped-live）。

### 5.2 既有回归

```text
python -m pytest scoring/tests -q -rs -p no:cacheprovider
293 passed, 10 skipped in 9.17s   (exit=0)
```

10 个 skip 与任务 2 收据一致（session 临时脚本缺失：`test_bander_regularization.py` 中 `run_aapm_r4 (temp)` 不可用），与本次改动无关。

### 5.3 CLI 实跑（7 fixture × `--json`，摘录 `state/published/verified`）

| fixture | state | published | verified | exit |
|---|---|---|---|---|
| no_status.json | NO_CLAIM | false | false | 0 |
| pending.json | INCOMPLETE | false | false | 0 |
| missing_strata.json | MISSING_LAYER | false | false | 0 |
| rejected.json | REJECTED | false | false | 0 |
| failed_gate.json | REJECTED | false | false | 0 |
| published.json | PUBLISHED | true | true | 0 |
| unverified_flag.json | INCOMPLETE | false | false | 0 |

### 5.4 fixtures 路径

`WS-4_leaderboard/scoring/tests/fixtures/publication/`：
- 板级：`no_status.json` / `pending.json` / `missing_strata.json` / `rejected.json` / `failed_gate.json`（旁有 `failed_gate.json.failed.json` 拒绝诊断）/ `published.json` / `unverified_flag.json`
- RunBundle 级：`runbundle_skipped_live/`（`method.json` / `eval.py` / `results.json`，results.json 的 claim 哈希为真实 `provenance_sha256` 计算值）

## 6. 改动文件清单（未 commit / 未 push）

### 修改（CT 仓库，任务 3 相关）

| 文件 | 行数变化 |
|---|---|
| `WS-4_leaderboard/scoring/verifier.py` | +245 |
| `WS-4_leaderboard/scoring/cli.py` | +106 |
| `WS-4_leaderboard/web/app.js` | +155/-4（含 .failed.json 支持与空对象判定修复） |
| `WS-4_leaderboard/web/index.html` | +3 |
| `WS-4_leaderboard/web/style.css` | +28 |
| **小计** | **+533 / -4** |

### 新增（CT 仓库）

| 文件 | 说明 |
|---|---|
| `WS-4_leaderboard/scoring/tests/test_publication_status.py` | 23 条测试（9370 字节） |
| `WS-4_leaderboard/scoring/tests/fixtures/publication/` | 8 个 JSON + 1 个 runbundle 目录 |

### 其他工作区改动（非本次任务，属历史遗留，未动）

`Heyang-paper/README.md`、`Heyang-paper/manuscript.tex`（任务 1）、`WS-2_framework/pwm_dose_equivalence/reproducibility/reproducible_manifest.json`（任务 2）。均未修改、未暂存。

### 未改动（红线）

BandER direction / dose margins / R6 tolerance / comparison_full764.json / recompare_per_metric.py / tolerance_audit.py / make_tables.py 常量。

## 7. BLOCKED 项

- **ldct_agent（`D:\ZHY\ldct_agent-main`）**：任务 3 落点全部在 CT 仓库 WS-4（web / verifier / CLI / saved-board receipts），任务书未要求修改 agent 仓库；其 `release-check` 属于任务 2 收据范围。该仓库因共享核心 `pillcam_agent` 缺失（`ensure_core_on_path()` 抛 ImportError）在任务 2 中整体 BLOCKED，**本任务未在 agent 内安装依赖或 clone 核心**，与本任务无关。
- **UI 静态预览页与截图**：截图通过本机 Edge headless 渲染自包含预览页生成（temp `pub_previews/*.html`，内嵌 fixture 数据 + app.js 原样逻辑），**非部署行为**；正式页面仍保持本地 JSON 回退原型，未部署。
