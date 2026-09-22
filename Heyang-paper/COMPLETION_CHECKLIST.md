# COMPLETION_CHECKLIST — corrected paper package

- **日期**：2026-09-22
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`）
- **依据**：`heyang/HEYANG_NEXT_2026-09-21.md` 第 4 步（前半：完成清单 + 本地提交；push/PR 待 owner 授权后执行）
- **范围**：核对任务书第 1-4 步论文包交付状态，列出检查点/证据/状态（DONE / BLOCKED / UNRESOLVED）
- **红线**：本清单为新增文件；未修改任何 artifact / manuscript / README；未 push；未打开 PR；工作区其他未提交改动原样保留

---

## 0. 任务书四步总览

| 任务书步骤 | 状态 | 证据 |
|---|---|---|
| 1. Sync + status reply | DONE | `heyang/HEYANG_REPLY_2026-09-20.md` 2026-09-21 段，commit `7a9dd15`（本地，未 push） |
| 2. CLAIM_EVIDENCE.md 台账 | DONE | `Heyang-paper/CLAIM_EVIDENCE.md`（192 行，commit `d140b71`） |
| 3. 修正论文 + 重生成包 | DONE | manuscript.tex/README 修正、tables 重生成、manuscript.pdf 重建（commit `d140b71`） |
| 4. COMPLETION_CHECKLIST.md + PR 准备 | 前半 DONE / push+PR 待 owner 授权 | 本文件；push/PR **未执行**（见 §11） |

---

## 1. 论文修正核对（step 3）

| 检查点 | 状态 | 证据 |
|---|---|---|
| "original declared criterion" 替换 "pre-registered" | DONE | 无带时间戳预注册证据（U6），全文已改；ENV_RECON §3 M1/M4/M8-M10/M15/M17/M19、README R1 |
| 容差修正标 retrospective | DONE | manuscript L243-249 显式声明追溯性调整、非独立/前瞻验证 |
| 因果表述缓和、不声称前瞻 | DONE | 禁用语扫描 0 命中（2026-09-22 复扫） |
| 环境表（复算 + 参考 = 本地运行环境） | DONE | manuscript L105-117；README L54-59 |
| 计数经 make_tables 校准（75/375/115） | DONE | manuscript L88-89、L162-163；tables/agreement.tex |
| 作者无关 TODO 清零 | DONE | 剩余 5 处 \todo 全部属 owner 决策（见 §8），无技术/写作 TODO |
| 保留诚实局限（不推广"无绝对容差可行"） | DONE | manuscript L195-202、L216-219；台账 §3 红字 |

## 2. 验证命令结果（2026-09-22 复跑）

| 命令 | 结果 | 状态 |
|---|---|---|
| `python Heyang-paper/make_tables.py` | 重新生成 agreement.tex / ladder.tex / scale.tex，exit=0 | DONE |
| `python Heyang-paper/make_tables.py --check` | `all tables current`，exit=0 | DONE |
| `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | blur/corediff/ctformer/learn/red_cnn 全 PASS、outside declared 0、overall PASS、committed verdict matches、exit=0 | DONE |

## 3. manuscript.pdf 构建

| 项 | 值 |
|---|---|
| 工具链 | MiKTeX 25.12（pdfTeX 4.23）+ bibtex（TeX 引擎在 elevated 会话被 MiKTeX 拦截，经降权调用 + `--enable-installer` 构建） |
| 编译流程 | pdflatex → bibtex → pdflatex → pdflatex，四步均 exit=0 |
| 产物 | `Heyang-paper/manuscript.pdf`，6 页，196,214 B（SHA256 见 §7） |
| 核验 | PASS3 无 undefined citation/reference；Table 1 嵌入正常；引用 [1]-[4] 解析；作者区 TODO 红色显示（预期，待 owner） |

## 4. CLAIM_EVIDENCE.md 台账（step 2）

| 检查点 | 状态 |
|---|---|
| 六项覆盖（①原判据失败 ②同侧重跑 ③容差阶梯 ④per-metric PASS ⑤计数 ⑥两环境） | DONE（§0 索引） |
| UNRESOLVED 显式清单 | DONE：U1-U9 共 9 项（见台账 §8），缺失标 UNRESOLVED 未推断 |
| 事实/回忆/缺失三类型标注（R/M/UNRESOLVED） | DONE |
| 原失败与修正并存保留 | DONE（`shipped_criterion_superseded` + `routeA_rerun_evidence.do_not_overwrite`） |

## 5. 本地提交链（heyang 分支，均未 push）

| commit | 说明 |
|---|---|
| `cadc2d7` | Progress index update: HEYANG_REPLY_2026-09-20.md |
| `7a9dd15` | 2026-09-21 status reply（step 1） |
| `d140b71` | CLAIM_EVIDENCE ledger + regenerated tables/PDF (task book step 2-3)（4 文件：CLAIM_EVIDENCE.md / README.md / manuscript.pdf / manuscript.tex） |

当前 HEAD = `d140b71`；upstream = `origin/heyang`，未推送提交含上述及更早同步链。

## 6. 未提交改动（原样保留，不属于本次论文包）

`git status --short` 共 13 行（9 M + 4 ??）：

| 路径 | 状态 |
|---|---|
| `WS-2_framework/pwm_dose_equivalence/reproducibility/reproducible_manifest.json` | M |
| `WS-4_leaderboard/scoring/__init__.py` / `cli.py` / `leaderboard.py` / `verifier.py` / `verify.py` | M（5 文件） |
| `WS-4_leaderboard/web/app.js` / `index.html` / `style.css` | M（3 文件） |
| `WS-4_leaderboard/scoring/binding.py` | ?? |
| `WS-4_leaderboard/scoring/tests/fixtures/publication/` | ?? |
| `WS-4_leaderboard/scoring/tests/test_input_binding.py` | ?? |
| `WS-4_leaderboard/scoring/tests/test_publication_status.py` | ?? |

## 7. artifact SHA256（2026-09-22 实测，论文包）

| 文件 | SHA256 |
|---|---|
| Heyang-paper/manuscript.pdf | 552518715CB02AAE24ED771D3CBC612F330829C9B1D1034C4892EFB41335B1DF |
| Heyang-paper/CLAIM_EVIDENCE.md | ED2A7538A5CB5640D0DDA84570C1EBF6399D300EA12A517490ECC535AB1973E4 |
| Heyang-paper/manuscript.tex | 3FB65D5B47FE3E26F775E5857615F2EAA36FB1A17F0376759082881AEA736705 |
| Heyang-paper/README.md | 21B2612A994326D28350923013C11B6FAFAB191969347243C2BF777B21AD0B1D |
| Heyang-paper/make_tables.py | C450699E76B5019B42B00B1F6742C4177EDAE29C429597BC4AE684A9F6EAC738 |
| Heyang-paper/references.bib | 79430D8DBF24C88289ADC3DE1FAC30F2F35E5D8763F71AB068F28C7F42CA7E1C |
| Heyang-paper/tables/agreement.tex | 04794EAE360F7816D68F94CFC1AE4773979CB276E3B48D9496098FAE10BABDA3 |
| Heyang-paper/tables/ladder.tex | BBA99F885559CC1FE4943A001B6D2EA6CA5BA5F2C1608B0FD9DB87042206CFF7 |
| Heyang-paper/tables/scale.tex | 2E1BE9DB359864B9A0B417D77CF088CAA789D6CE3969794A206CF5A23B0A680C |

其他关键 artifact 哈希（台账 §6.1）：task_spec `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`；5 个 checkpoint 哈希见 `WS-1_dataset/R6_recalc/hashes/ckpt_hashes.txt`。

## 8. 剩余 TODO（5 处，全部 owner 决策）

| 行号 | 内容 | owner |
|---|---|---|
| L22 | author list, affiliations, ORCIDs, corresponding author | 作者 |
| L261 | 是否加入第三环境（受 checkpoint/data 迁移约束） | 作者 |
| L277 | 指向发布的 artifact / comparison JSON / 重推导 | 作者 |
| L282 | CRediT statement | 作者 |
| L285 | Per-author declaration | 作者 |

## 9. Owner 决策请求（紧凑列表）

请在评审时一次性确认以下输入，每项阻断对应字段：

1. **作者顺序（author order）** — 阻断 L22 author list
2. **单位（affiliations）** — 阻断 L22
3. **ORCIDs** — 阻断 L22
4. **通讯作者（corresponding author）** — 阻断 L22
5. **CRediT 贡献声明** — 阻断 L282
6. **Per-author declarations（利益冲突/资助/伦理）** — 阻断 L285
7. **第三环境实验取舍** — 阻断 L261（维持现状可删 TODO）
8. **artifact 公开发布决策** — 阻断 L277（data/code availability 措辞依赖此决定）

## 10. code/data availability 语言准备（待 owner 定稿）

基于现有权利的准确措辞要点（**code availability 不授予 image/checkpoint 再分发权**）：

- 代码：在仓库许可下公开；可声明"evaluation code is available at <repo>"（前提是 owner 确认仓库公开范围）。
- 数据：LIDC-IDRI 与 AAPM 低剂量 CT 数据集的再分发受各自许可约束；论文可引用数据集与哈希清单（`hashes/data_hashes.txt` 364 项 / `hashes/aapm_hashes.txt` 25 项）作为访问指引，**不得**声称作者有权再分发原始图像。
- 权重/checkpoint：仅提供 SHA256 清单（`ckpt_hashes.txt`）供验证，**不**随论文分发模型权重；公开与否由 owner 单独决定。
- 建议措辞模板（待 owner 编辑）：「Code is available under the repository license. Derived data manifests and check hashes are listed in …; original image datasets remain under their respective licenses and are not redistributed here. Model checkpoints are identified by hash in … and are not redistributed.」

## 11. push / PR 待办（未执行，待 owner 授权）

| 项 | 状态 | 说明 |
|---|---|---|
| push heyang 到 origin | 未执行 | 本地提交 `d140b71`（及 `7a9dd15`、`cadc2d7` 等）均在本地；任务硬约束"禁止 push"，需 owner 明确授权 |
| 开 paper PR against main | 未执行 | 需先 push；PR 拟包含 Heyang-paper 论文包 4 文件 + 本清单，标题建议 "Corrected Heyang paper package (CLAIM_EVIDENCE + regenerated tables/PDF)" |
| 更新 heyang/HEYANG_REPLY_2026-09-20.md 索引 | 未执行 | 任务书第 4 步要求链接包与清单；属 PR 准备后段，待授权 |

---

## 总结

论文包四步中第 1-3 步与第 4 步前半已 DONE（HEAD `d140b71`，未 push）；剩余均为 owner 决策/授权项：8 项作者输入（§9）、push/PR（§11）、第三环境取舍、artifact 公开发布。未提交的 WS-2/WS-4 13 行改动原样保留，未纳入任何提交。
