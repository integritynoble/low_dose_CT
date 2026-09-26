---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_429c1573b99211f1a1bf52540064ee0f
    ReservedCode1: yE95V+qUMlwWIJ5ghMzvPzrA6KrRatwpIkuCb/NXC7YeDI9mZUOG259U+5zhi5b0wIzHmA7+i2BWa5VJUYVEvVZ2FgwD7oCl1tPK5VFdb211JbmDpe0k9tVo8+2AJbE++WI/Mg24zshm35elEkeEuIWxGDdG9eM844kUhuou3FXIk6nT5/zGENfCkuE=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_429c1573b99211f1a1bf52540064ee0f
    ReservedCode2: yE95V+qUMlwWIJ5ghMzvPzrA6KrRatwpIkuCb/NXC7YeDI9mZUOG259U+5zhi5b0wIzHmA7+i2BWa5VJUYVEvVZ2FgwD7oCl1tPK5VFdb211JbmDpe0k9tVo8+2AJbE++WI/Mg24zshm35elEkeEuIWxGDdG9eM844kUhuou3FXIk6nT5/zGENfCkuE=
---

# Heyang progress reply — 26 September 2026

本文件为 `third-env/blackwell` 分支阶段性汇报（对应 [HEYANG_NEXT_2026-09-25.md](HEYANG_NEXT_2026-09-25.md)
任务 4/5/6 收尾与 0925 wrap-up）。状态取值仅限 IN PROGRESS / DONE / BLOCKED；
证据均指认真实文件、commit hash 与实测结果。

- **CT checkout**: `D:\ZHY\low_dose_CT-heyang` 分支 `third-env/blackwell`，HEAD
  `66680c2`（checkpoint 溯源补充，本批随汇报一起 push）
- **本批提交链**：`78ca452` → `9297981` → `dd694fa` → `6a82550` → `9d2cdc9` →
  `57a6411` → `66680c2`（共 7 个提交 + 本次汇报/标注提交）
- **未推送**：以上 7 个提交此前均在本地，本次随汇报文件一并 push 到
  `origin/third-env/blackwell`

## Progress index

| Task | Status | Commit / evidence | Remaining blocker | ETA |
|---|---|---|---|---|
| 5 — 第三环境运行包（third-env/blackwell） | DONE | `78ca452`：Blackwell 支持 + 运行包四文档入仓于 `WS-1_dataset/R6_recalc/third_env/`（THIRD_ENV_RUNBOOK / data_manifest_LIDC_AAPM / checkpoint_provenance_license / THIRD_PARTY_OPERATOR_GUIDE）；checkpoint 未搬运仅哈希，等待 owner 授权传输 | 权重传输需 owner 授权；运行在 owner 工作站执行 | 2026-09-26（文档）；运行待授权 |
| 4（补充） — patient-mapping docstring + pyflakes cleanup | DONE | `9297981`：`binding.py` patient-mapping docstring；pyflakes 清理（hashlib、TASK_LABEL） | 无 | 2026-09-26 |
| 6 — 策展发布包 + availability 声明 | DONE | `dd694fa`：发布包三文件于 `WS-1_dataset/R6_recalc/release/`（RELEASE_MANIFEST 43 项 A 类 + RIGHTS_CHECKLIST 10 组 + AVAILABILITY_STATEMENT_draft，DOI 占位）；`manuscript.tex` availability 段替换；COMPLETION_CHECKLIST §7 重哈希 | Zenodo/公共仓库/release tag 未建；DOI 未回填（占位） | 发布动作待 owner 决策 |
| 0925 wrap-up（tasks 5/6 状态、§7 rehash） | DONE | `6a82550`：COMPLETION_CHECKLIST §7 在 `dd694fa` 重算；HEYANG_REPLY 索引标 tasks 5/6 DONE、backlog BLOCKED | 无 | 2026-09-25 |
| BANDER-2 — 五 controls 在真实 AAPM 切片 + R3 同 ROI 对照 | DONE | `9d2cdc9` + `57a6411`：BANDER_CONTROLS_2026-09-26.md（五 controls，CPU 确定性，48 ROI patient-level SE：blur 0.004–0.010、ringing 0.011–0.016） | 无 | 2026-09-26 |
| checkpoint 溯源补充（推断标注） | DONE | `66680c2`：checkpoint_provenance_license.md 从 4 个 .pt 文件内读出真实元数据（seed=42；red_cnn/learn/ctformer steps=2662、corediff steps=20000），确认均为本地 train.py 2026-08-19 产物；超参为推断标注，无日志佐证 | 不重训（owner 2026-09-26 决定）；超参如需实证需 owner 提供训练日志 | 2026-09-26 |
| 本批收尾 — 汇报 + AIGC 标注 | DONE | 本文件 + BANDER_CONTROLS_2026-09-26.md AIGC frontmatter/提示行；随全批提交 push | 无 | 2026-09-26 |

## 本批改动文件清单

- `WS-1_dataset/R6_recalc/third_env/`（4 文档，task 5，commit `78ca452`）
- `WS-4_leaderboard/scoring/binding.py`（task 4 补充，commit `9297981`）
- `WS-1_dataset/R6_recalc/release/`（3 文档，task 6，commit `dd694fa`）
- `Heyang-paper/manuscript.tex`、`Heyang-paper/COMPLETION_CHECKLIST.md`
  （task 6 同步，commit `dd694fa`）
- `heyang/HEYANG_REPLY_2026-09-20.md`（0925 wrap-up 索引，commit `6a82550`）
- `heyang/evidence/BANDER_CONTROLS_2026-09-26.md`（BANDER-2 对照报告，commit
  `9d2cdc9`/`57a6411` + 本次 AIGC 标注）
- `WS-1_dataset/R6_recalc/third_env/checkpoint_provenance_license.md`
  （溯源补充，commit `66680c2`）

## Not pushed → 本次已 push

本批 8 个提交（7 个既有 + 本汇报/标注提交）随本次 push 一并推送到
`origin/third-env/blackwell`；PR #30（paper package，head `heyang`）仍 Open
待 owner 审查，不在本批。

## Owner 待办（不影响本批）

1. checkpoint 权重传输授权（task 5）。
2. 训练日志若可提供，可将 4 个权重的超参从"推断"转"实证"（可选，owner 已决定
   暂不重训）。
3. DOI 回填与发布动作（task 6）。
4. 8 项论文 owner 决策（作者元数据等，见 COMPLETION_CHECKLIST.md §9）。
*（内容由AI生成，仅供参考）*
