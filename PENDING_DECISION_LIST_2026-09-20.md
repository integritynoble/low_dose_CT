---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_ecb05821b4b511f19285525400638852
    ReservedCode1: eHybcplVJYTNPwWMYRVC+nezrK3lJSdukHWa5j7kBIcs+XXNhumD7Qx7GiyqjRwgxlf/Hhf9lQdVxmKAS8B1m3RsfoGk8lbTPb1Vtu3Q7LS8QObgll8FUVNY20ZvBj0MZFXFT5Hh6XlNDLDqHnXxhmp73YVy/OQpRvyT0EYnzbItkKqzWXcexALcSWA=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_ecb05821b4b511f19285525400638852
    ReservedCode2: eHybcplVJYTNPwWMYRVC+nezrK3lJSdukHWa5j7kBIcs+XXNhumD7Qx7GiyqjRwgxlf/Hhf9lQdVxmKAS8B1m3RsfoGk8lbTPb1Vtu3Q7LS8QObgll8FUVNY20ZvBj0MZFXFT5Hh6XlNDLDqHnXxhmp73YVy/OQpRvyT0EYnzbItkKqzWXcexALcSWA=
---

# PENDING_DECISION_LIST（待办决策清单）

- **生成日期**：2026-09-20
- **仓库**：`D:\ZHY\low_dose_CT-heyang`
- **分支**：`heyang`
- **基线 HEAD**：`38234986cfef043fc2b24c022265f04de1bdecd6` — "scoring tests: make bander regularization temp dir platform-agnostic (HEYANG §1)"
- **说明**：本清单仅整理未完成事项供 leader 决策，未执行任何 commit / push。

---

## 一、决策清单表

类别说明：**A** = 待 leader 决策（可推进但需授权/确认）；**B** = 外部资源阻塞（需外部条件或协作方）。

| 编号 | 类别 | 事项 | 当前状态 | 阻塞点 | 需 leader 决策内容 | 建议动作 |
|---|---|---|---|---|---|---|
| A-1 | A | 提交待决改动 | 工作区 10 M + 6 ??（web/ 含 4 文件，共 19 个文件路径）未提交 | 无（本地可提交） | 是否提交到 heyang 分支 | 确认后 `git add` + commit（禁 force / rebase / 改历史） |
| A-2 | A | push 至远端 | HEAD=3823498，领先 origin/main 26 个提交 | 需授权推送 | 是否推送远端（红线：禁 `--force`） | 确认后在 A-1 提交完成后 push heyang |
| A-3 | A | S1–S4 语义复核 | `WS-4_leaderboard/scoring/spec.md` 为 `[DRAFT]`（含 scoring/verifier.py 19 passed 等 Phase1 产物） | 需语义确认后定稿 | 确认 S1–S4 语义，是否去除 DRAFT 标记 | 复核语义 → 批准后去 DRAFT 定稿 |
| A-4 | A | `[CONFIRM]` 81 处清单确认 | 清单见 `output/CONFIRM_ITEMS_LIST_2026-09-19.md`（A 投稿门禁 53、B 操作规划 14、C 预注册默认值 14） | 需逐条或批量确认 | 逐条确认或批量 ratify；C 类 14 处（κ≥0.60 / IoU≥0.3 / OCR≥60 / HU offset）与 1.1.8 预注册一致，可一次性 ratify | 建议 C 类先批量 ratify（与 A-3 联动），再处理 A/B 类 |
| A-5 | A | vendor 权重 `git rm --cached` | 5 个 vendor 文件仍 tracked（LEARN_MODEL.mat 等共 93.4MB） | 需授权 | 是否授权 `git rm --cached` 并补充 .gitignore 规则 | 确认后执行（仅移除跟踪，不删工作区文件），补 .gitignore 防回归 |
| B-6 | B | §3 BANDER-2/6 | 待 GPU 图像机器验证 | 需 GPU 图像机器授权 + §5 协议冻结 | —（外部资源） | 等待 GPU 机器授权与 §5 冻结后执行 |
| B-7 | B | §4 完整审计 | 当前 49 ran / 48 passed / 1 skipped | 需 15 日工作站可达路径或 leader 提供替代路径（pillcam_agent 已修正为工作站共享核心目录，非独立 GitHub 仓库） | —（外部资源） | 获取可达路径后补跑完整审计 |
| B-8 | B | §5 十处 UNRESOLVED | 10 处 UNRESOLVED 待协作方认领（§5 PROTOCOL_SKELETON 94074d5 已推送） | 需 physicist / radiologist / statistician 认领 | —（外部协作） | 推动协作方认领并闭环 |
| B-9 | B | S3 live 沙箱执行 | 未接线（UNRESOLVED） | 需 Docker 容器 + 数据机 held-out 数据 | —（外部资源） | 准备容器与 held-out 数据后执行 |
| B-10 | B | 1.5 会议场地确认 | 待 RSNA / ISBI 2027 confirmation letter | 外部机构未回函 | —（外部资源） | 跟进外部 confirmation letter |
| B-11 | B | 外部数据项 | 2.5 / 2.12 / 2.13（PhysioNet / Zenodo / 数据机）、4.5 全链路重跑（GPU） | 依赖外部数据源与 GPU | —（外部资源） | 按数据源可用性与 GPU 排期推进 |

---

## 二、待提交改动明细（git status --short 实测原文）

```
 M PROTOCOL_SKELETON_2026-09-15.md
 M WS-1_dataset/R6_recalc/R6_recalc_report.md
 M WS-1_dataset/SUBMISSION_CHECKLIST.md
 M WS-1_dataset/paper_draft/README.md
 M WS-1_dataset/paper_draft/manuscript.pdf
 M WS-1_dataset/physionet_listing/deposit_procedure.md
 M WS-4_leaderboard/OPTIMIZATIONS_LOG.md
 M WS-4_leaderboard/README.md
 M WS-4_leaderboard/scoring/__init__.py
 M WS-4_leaderboard/scoring/cli.py
?? WS-1_dataset/dev-setup.md
?? WS-4_leaderboard/scoring/spec.md
?? WS-4_leaderboard/scoring/tests/test_verifier.py
?? WS-4_leaderboard/scoring/verifier.py
?? WS-4_leaderboard/submission_contract.md
?? WS-4_leaderboard/web/
```

统计：**10 个已修改（M）+ 6 个未跟踪（??，其中 web/ 含 4 文件）≈ 19 个文件路径**。

### 按文件分组说明

| 分组 | 文件 | 说明 |
|---|---|---|
| 协议与流程文档 | `PROTOCOL_SKELETON_2026-09-15.md`（M） | 含 §5 dose-task protocol 相关改动 |
| WS-1 数据集 / 重算 | `WS-1_dataset/R6_recalc/R6_recalc_report.md`（M） | 含"8组→5组"两处修正 |
| 提交清单 | `WS-1_dataset/SUBMISSION_CHECKLIST.md`（M） | — |
| 论文草稿 | `WS-1_dataset/paper_draft/README.md`、`manuscript.pdf`（M） | — |
| 数据集 deposit | `WS-1_dataset/physionet_listing/deposit_procedure.md`（M）、`WS-1_dataset/dev-setup.md`（??） | — |
| WS-4 优化日志/README | `WS-4_leaderboard/OPTIMIZATIONS_LOG.md`、`README.md`（M） | — |
| WS-4 scoring 代码 | `scoring/__init__.py`、`scoring/cli.py`（M）；`scoring/verifier.py`、`scoring/spec.md`、`scoring/tests/test_verifier.py`、`submission_contract.md`（??） | WS-4 Phase1 落地产物（spec.md 为 [DRAFT]） |
| WS-4 web 前端 | `WS-4_leaderboard/web/`（??，含 index.html / app.js / style.css / README.md 4 文件） | Phase1 前端产物 |

---

## 三、建议决策顺序

1. **A-1**：确认提交待决改动到 heyang 分支（本地 commit，不 push）——先固化当前工作区基线。
2. **A-4**：C 类 14 处（κ≥0.60 / IoU≥0.3 / OCR≥60 / HU offset）与 1.1.8 预注册一致，一次性 ratify；A/B 类随后逐条处理。
3. **A-3**：S1–S4 语义复核，批准后对 scoring/spec.md 去 DRAFT 定稿（与 A-4 C 类联动确认默认值）。
4. **A-2**：A-1 提交完成后，授权后 push heyang 至远端（禁 `--force`）。
5. **A-5**：授权 `git rm --cached` 移除 5 个 vendor 文件跟踪并补 .gitignore（不删工作区文件）。
6. **B 类（B-6 ~ B-11）**：按外部资源就绪情况逐项推进，不阻塞 A 类决策。
*（内容由AI生成，仅供参考）*
