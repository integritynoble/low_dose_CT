# WINDOWS_COMPAT_RECEIPT_2026-09-21

- **日期**：2026-09-21
- **任务**：HEYANG_NEXT_2026-09-20.md 任务 2（P1）—— 两仓库原生 Windows 兼容性测试收据
- **机器**：Windows 11 专业版（Build 26100），非 WSL，原生 PowerShell 5.1
- **被测仓库**：
  - CT：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`，HEAD `3472815`，工作区含任务 1 未提交的 manuscript/README 修改）
  - Agent：`D:\ZHY\ldct_agent-main`（分支 `heyang`，HEAD `c2a75c5`，工作区干净）
- **共享核心**：`pillcam_agent`（research-agents）—— **本机无 checkout**（见 BLOCKED 清单）
- **红线遵守**：全程只读；未修改任何仓库文件、未安装任何依赖、未 clone、未 commit、未 push。

---

## 1. 环境记录

### 1.1 系统与工具链

| 项 | 值 |
|---|---|
| OS | Microsoft Windows 11 专业版，10.0.26100（Build 26100） |
| Shell | PowerShell 5.1（原生，非 WSL） |
| git | git version 2.52.0.windows.1 |
| Python（默认 `python`） | Python 3.11.8（`D:\Marvis\MarvisAgent\1.0.1100.580\runtime\python311\python.exe`） |
| Python 3.12（py launcher） | `C:\Users\ufl\AppData\Local\Programs\Python\Python312\python.exe` |
| Python 3.10 | `D:\Python3.10.8\python.exe` |
| pip | pip 24.0（py3.11） |

### 1.2 关键包导入矩阵（`python -c "import ..."` 逐项验证）

| 包 | py3.11（默认） | py3.12 | py3.10 |
|---|---|---|---|
| torch | FAIL（未安装） | FAIL（未安装） | FAIL（未安装） |
| torchvision | FAIL（未安装） | FAIL（未安装） | FAIL（未安装） |
| numpy | OK 2.4.6 | OK 2.4.6 | OK 2.2.6 |
| scipy | FAIL（未安装） | OK 1.18.0 | OK 1.15.3 |
| scikit-image | FAIL（未安装） | FAIL（未安装） | FAIL（未安装） |
| tifffile | FAIL（未安装） | FAIL（未安装） | FAIL（未安装） |
| pytest | OK 9.1.1 | FAIL（未安装） | OK 9.1.1 |
| jsonschema | FAIL（未安装） | — | OK 4.26.0 |
| pandas / matplotlib | FAIL | OK 3.0.3 / 3.11.0 | — |

> 说明：复算环境记录（`.venv_r6`，Python 3.12.10 + torch 2.3.0+cu121 等，见任务 1 收据）在本机未保留该 venv；本机三个解释器均无 torch / torchvision / scikit-image / tifffile。CT 仓库的 --check 脚本与测试套件不依赖这些缺失包（见 §2 实际结果），故不影响 CT 侧判定。

### 1.3 环境变量

| 变量 | 值 |
|---|---|
| LDCT_REPO | 未预设（实测时显式设为 `D:\ZHY\low_dose_CT-heyang`） |
| RESEARCH_CORE | 未设置（本机无共享核心 checkout 可指向） |
| PYTHONPATH | 未预设（仅 WS-2 pytest 按任务书在 shell 内临时设置 `src`） |

---

## 2. 逐命令实测（命令 / 退出码 / 判定）

### 2.1 low_dose_CT-heyang（root: `D:\ZHY\low_dose_CT-heyang`）

| # | 命令 | 工作目录 | 解释器 | 退出码 | 判定 | 输出摘录 |
|---|---|---|---|---|---|---|
| 1 | `python Heyang-paper/make_tables.py --check` | CT root | py3.11 | 0 | **PASS** | `all tables current` |
| 2 | `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | CT root | py3.11 | 0 | **PASS** | 5 模型全部 `PASS  outside declared: 0`；`overall: PASS`；`committed verdict matches the re-derivation` |
| 3 | `python -m pytest scoring/tests ../WS-1_dataset/analysis/tests -q -rs -p no:cacheprovider` | `WS-4_leaderboard` | py3.10 | 0 | **PASS** | `347 passed, 10 skipped in 9.54s` |
| 4 | `$env:PYTHONPATH=<...>\WS-2_framework\pwm_dose_equivalence\src; python -m pytest -o addopts= tests -q -rs -p no:cacheprovider` | `WS-2_framework\pwm_dose_equivalence` | py3.10 | 0 | **PASS** | `157 passed, 1 warning in 16.96s` |

**skip/warning 明细（如实记录，不视为失败）**：
- 命令 3 的 10 个 skip 全部来自 `scoring\tests\test_bander_regularization.py`：4 个 `session temp run scripts not present` + 6 个 `run_aapm_r4 (temp) not importable`（历史会话脚本缺失，与 Linux 基线 skip 原因一致）。
- 命令 4 的 1 个 warning：`tests/test_task_equivalence.py::test_pet_contrast_recovery_observer` — `Sample size 12 is below the small-n threshold (30) ... anti-conservative ...`（库自身统计提示，非兼容性失败）。

### 2.2 ldct_agent-main（root: `D:\ZHY\ldct_agent-main`，`LDCT_REPO` 已显式设置）

| # | 命令 | 退出码 | 判定 | 输出摘录（截断） |
|---|---|---|---|---|
| 5 | `python -m ldct_agent.cli check` | 1 | **BLOCKED** | `ImportError: ldct_agent needs its shared core, 'research-agents', and it is neither installed nor beside this checkout. Either: pip install -e . / git clone ... pillcam_agent / RESEARCH_CORE=<path>` |
| 6 | `python -m ldct_agent.cli board` | 1 | **BLOCKED** | 同上 ImportError（`ldct_agent\__init__.py:21 ensure_core_on_path()`） |
| 7 | `python -m ldct_agent.cli gate-audit` | 1 | **BLOCKED** | 同上 ImportError |
| 8 | `python -m ldct_agent.cli tolerance audit` | 1 | **BLOCKED** | 同上 ImportError |
| 9 | `python -m ldct_agent.cli release-check` | 1 | **BLOCKED** | 同上 ImportError |
| 10 | `python -m unittest discover -s tests -v` | 1 | **BLOCKED** | 10 个测试模块全部 `_FailedTest ... ERROR`（import 阶段即失败，同一缺失核心错误） |

**入口存在性验证**：`ldct_agent\cli.py` 源码中 `board` / `gate-audit` / `tolerance`(audit) / `release-check` / `check` 子命令均已注册（argparse `add_subparsers`），命令名非编造；阻断发生在 `ldct_agent\__init__.py` 的 `ensure_core_on_path()`，早于任何子命令逻辑。

---

## 3. BLOCKED 清单

| 项 | 原因 | 解除条件 |
|---|---|---|
| ldct_agent 全部命令（unittest + 5 个 CLI） | 共享核心 `pillcam_agent`（research-agents）在本机**不存在**：未 pip 安装、无 sibling checkout（`D:\ZHY\pillcam_agent`、`~/pwm/pillcam_agent` 均 MISS）、`RESEARCH_CORE` 无可指向路径。集成记录（`docs/CT_INTEGRATION_2026-09-20.md`）确认该核心是"existing authorized workstation core"（head `7a20d469…`），README 亦声明 GitHub 安装 URL 未验证、不得作为安装途径 | 提供/恢复授权核心 checkout 并设 `RESEARCH_CORE=<path>` 后重跑 |
| 任何 GPU 推理 / 模型运行类命令 | 本机无 NVIDIA 环境（三解释器均无 torch），且任务书红线禁止安装依赖；任务 2 命令清单本身不含推理命令 | 在授权的 2×RTX 4090 机器执行（属任务 5a 范畴） |
| 涉及未授权数据集的项 | 本机无 LIDC/AAPM 数据根；`config.DATA_ROOTS` 声明为空属设计使然（agent 是 verifier，不读数据），任务 2 命令清单未触发 | —（不属于本任务可解） |

**说明**：BLOCKED 是"缺前置条件未测"，不是"测试失败"；ldct_agent 代码本身未在本机执行过任何业务逻辑，不能给出 PASS/FAIL 之外的真实判定。

---

## 4. 与 Linux 基线对比

| 套件 | Linux 基线（集成记录） | Windows 本机 | 差异说明 |
|---|---|---|---|
| CT scoring + WS-1 analysis（pytest） | 347 passed / 10 skipped | 347 passed / 10 skipped | **一致**；skip 原因相同（历史会话脚本缺失） |
| WS-2（pytest） | 157 passed | 157 passed（+1 warning） | **一致**；warning 为库内统计提示 |
| make_tables.py --check / recompare_per_metric.py --check | 通过（exit 0） | 通过（exit 0） | **一致** |
| ldct_agent（unittest + CLI） | 53 passed / 1 skipped（核心经 RESEARCH_CORE 提供） | BLOCKED（核心缺失） | 无法对比；本机缺授权核心 checkout |

---

## 5. 总结论

1. **`low_dose_CT-heyang`：原生 Windows 可用（PASS）**。任务书指定的 4 条命令全部实跑通过：2 个 --check exit 0、347 passed / 10 skipped（WS-4+WS-1）、157 passed（WS-2）。测试套件仅依赖 numpy/scipy/pytest/jsonschema，均在本机 py3.10/py3.11 可用；无 torch/skimage/tifffile 不影响这些命令。
2. **`ldct_agent-main`：未验证（BLOCKED）**。所有入口（unittest 与 CLI）在 import 阶段因共享核心 `pillcam_agent` 缺失而阻断（exit 1），与代码质量无关；解除条件为提供授权核心 checkout 并设 `RESEARCH_CORE`。核心 head 无法记录（本机无 checkout）。
3. 全程只读：未修改任何仓库文件、未安装依赖、未 clone、未 commit、未 push。

**需要 owner 提供**：授权共享核心 `pillcam_agent` checkout 路径（或允许将其恢复至本机），方可完成 ldct_agent 侧 Windows 收据。
