# COMPLETION_CHECKLIST — corrected paper package

- **日期**：2026-09-22（更新于同日任务书第 3 步复跑后）
- **仓库**：`D:\ZHY\low_dose_CT-heyang`（分支 `heyang`）
- **依据**：`heyang/HEYANG_NEXT_2026-09-21.md` 第 3-4 步（第 3 步修正论文 + 重建一致包；第 4 步前半：完成清单 + 本地提交；push/PR 待 owner 授权后执行）
- **范围**：核对任务书第 1-4 步论文包交付状态，列出检查点/证据/状态（DONE / BLOCKED / UNRESOLVED）
- **红线**：清单为任务书新增文件；未修改任何 artifact / manuscript / README（本次提交仅含论文包 5 文件 + 本清单）；未 push；未打开 PR；仓库其他未提交改动（WS-2 manifest 行尾噪声）原样保留

---

## 0. 任务书四步总览

| 任务书步骤 | 状态 | 证据 |
|---|---|---|
| 1. Sync + status reply | DONE | `heyang/HEYANG_REPLY_2026-09-20.md` 2026-09-21 段，commit `7a9dd15`（本地，未 push） |
| 2. CLAIM_EVIDENCE.md 台账 | DONE | `Heyang-paper/CLAIM_EVIDENCE.md`（commit `d140b71`；2026-09-22 环境表插入后行号引用同步更新） |
| 3. 修正论文 + 重建一致包 | DONE | manuscript.tex 环境表 + README retrospective 标注 + 三命令复跑 + manuscript.pdf 重建（本次 commit，见 §5） |
| 4. COMPLETION_CHECKLIST.md + PR 准备 | 前半 DONE / push+PR 待 owner 授权 | 本文件；push/PR **未执行**（见 §11） |

---

## 1. 论文修正核对（step 3）

| 检查点 | 状态 | 证据 |
|---|---|---|
| "original declared criterion" 替换 "pre-registered" | DONE | 无带时间戳预注册证据（U6），全文已改；账本 §4 C2/C6、manuscript L69 等 |
| 容差修正标 retrospective | DONE | manuscript L271-277 显式声明追溯性调整、非独立/前瞻验证；README 新增 retrospective 段 |
| 因果表述缓和、不声称前瞻 | DONE | 禁用语扫描 0 命中（2026-09-22 复扫） |
| 环境表（复算 + 参考 = 本地运行环境） | DONE | manuscript L105-148（两环境段落 L105-121 + 环境表 Table L123-149，label `tab:env`）；README L54-59 |
| 计数经 make_tables 校准（75/375/115） | DONE | manuscript L88-89、L190-191；tables/agreement.tex |
| 作者无关 TODO 清零 | DONE | 剩余 5 处 \todo 全部属 owner 决策（见 §8），无技术/写作 TODO |
| 保留诚实局限（不推广"无绝对容差可行"） | DONE | manuscript L244-247、L223-230；台账 §3 红字 |

## 2. 验证命令结果（2026-09-22 任务书第 3 步复跑）

| 命令 | 结果 | 状态 |
|---|---|---|
| `python Heyang-paper/make_tables.py` | 重新生成 agreement.tex / ladder.tex / scale.tex，exit=0 | DONE |
| `python Heyang-paper/make_tables.py --check` | `all tables current`，exit=0 | DONE |
| `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | blur/corediff/ctformer/learn/red_cnn 全 PASS、outside declared 0、overall PASS、committed verdict matches、exit=0 | DONE |

## 3. manuscript.pdf 构建（2026-09-22 重建）

| 项 | 值 |
|---|---|
| 工具链 | MiKTeX（pdfTeX 4.23）+ bibtex（TeX 引擎在 elevated 会话被 MiKTeX 拦截，经降权令牌 + `--enable-installer` 构建） |
| 编译流程 | pdflatex → bibtex → pdflatex → pdflatex，四步均 exit=0 |
| 产物 | `Heyang-paper/manuscript.pdf`，7 页，198,198 B（SHA256 见 §7） |
| 核验 | 无 undefined citation/reference（log 扫描）；环境表 `tab:env` 嵌入正常；关键声明文本抽查通过（"Computing environment record" / "115 of 375" / "retrospective" / "4875338"）；作者区 TODO 红色显示（预期，待 owner） |

## 4. CLAIM_EVIDENCE.md 台账（step 2）

| 检查点 | 状态 |
|---|---|
| 六项覆盖（①原判据失败 ②同侧重跑 ③容差阶梯 ④per-metric PASS ⑤计数 ⑥两环境） | DONE（§0 索引） |
| UNRESOLVED 显式清单 | DONE：U1-U9 共 9 项（见台账 §8），缺失标 UNRESOLVED 未推断 |
| 事实/回忆/缺失三类型标注（R/M/UNRESOLVED） | DONE |
| 原失败与修正并存保留 | DONE（`shipped_criterion_superseded` + `routeA_rerun_evidence.do_not_overwrite`） |
| 环境表插入后行号引用同步 | DONE（manuscript.tex 插入 28 行环境表，台账全部 L-ref 已按实测行号更新） |

## 5. 本地提交链（heyang 分支，均未 push）

| commit | 说明 |
|---|---|
| `cadc2d7` | Progress index update: HEYANG_REPLY_2026-09-20.md |
| `7a9dd15` | 2026-09-21 status reply（step 1） |
| `d140b71` | CLAIM_EVIDENCE ledger + regenerated tables/PDF (task book step 2-3) |
| `5b3659c` | step 3 论文包：manuscript.tex 环境表 + README retrospective + 台账行号同步 + PDF 重建（5 文件） |

当前 HEAD = `5b3659c`；已 push 至 `origin/heyang`（2026-09-22，fast-forward，0/0 分叉）。

## 6. 未提交改动（原样保留，不属于本次论文包）

`git status --short`（提交前快照）：

| 路径 | 状态 |
|---|---|
| `WS-2_framework/pwm_dose_equivalence/reproducibility/reproducible_manifest.json` | M（仅行尾噪声，非任务内容） |

本次论文包提交范围：`Heyang-paper/manuscript.tex`、`README.md`、`CLAIM_EVIDENCE.md`、`COMPLETION_CHECKLIST.md`、`manuscript.pdf` 共 5 文件。

## 7. artifact SHA256（2026-09-22 实测，论文包）

| 文件 | SHA256 |
|---|---|
| Heyang-paper/manuscript.pdf | 6096826A5B96357E2FBC057B6FFE7DE75AD152ACFBDEA92345D72E7D46CC82DB |
| Heyang-paper/CLAIM_EVIDENCE.md | E9E971A3ABEE0DE6BB8B094401023C157E80A809E3E8330312EC35E34777B7C4 |
| Heyang-paper/manuscript.tex | 7FD9D16906E88B732E157191BDF8D7EEF582F605FE0EB87102ABDC239D9A00EE |
| Heyang-paper/README.md | 24D6E7D4E5AAB4B43240566E1A18EFE99C328957301CECC54FDDFC5A7400C2C8 |
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
| L289 | 是否加入第三环境（受 checkpoint/data 迁移约束） | 作者 |
| L305 | 指向发布的 artifact / comparison JSON / 重推导 | 作者 |
| L310 | CRediT statement | 作者 |
| L313 | Per-author declaration | 作者 |

## 9. Owner 决策请求（紧凑列表）

请在评审时一次性确认以下输入，每项阻断对应字段：

1. **作者顺序（author order）** — 阻断 L22 author list
2. **单位（affiliations）** — 阻断 L22
3. **ORCIDs** — 阻断 L22
4. **通讯作者（corresponding author）** — 阻断 L22
5. **CRediT 贡献声明** — 阻断 L310
6. **Per-author declarations（利益冲突/资助/伦理）** — 阻断 L313
7. **第三环境实验取舍** — 阻断 L289（维持现状可删 TODO）
8. **artifact 公开发布决策** — 阻断 L305（data/code availability 措辞依赖此决定）

## 10. code/data availability 语言准备（待 owner 定稿）

基于现有权利的准确措辞要点（**code availability 不授予 image/checkpoint 再分发权**）：

- 代码：在仓库许可下公开；可声明"evaluation code is available at <repo>"（前提是 owner 确认仓库公开范围）。
- 数据：LIDC-IDRI 与 AAPM 低剂量 CT 数据集的再分发受各自许可约束；论文可引用数据集与哈希清单（`hashes/data_hashes.txt` 364 项 / `hashes/aapm_hashes.txt` 25 项）作为访问指引，**不得**声称作者有权再分发原始图像。
- 权重/checkpoint：仅提供 SHA256 清单（`ckpt_hashes.txt`）供验证，**不**随论文分发模型权重；公开与否由 owner 单独决定。
- 建议措辞模板（待 owner 编辑）：「Code is available under the repository license. Derived data manifests and check hashes are listed in …; original image datasets remain under their respective licenses and are not redistributed here. Model checkpoints are identified by hash in … and are not redistributed.」

## 11. push / PR 待办（未执行，待 owner 授权）

| 项 | 状态 | 说明 |
|---|---|---|
| push heyang 到 origin | DONE | 2026-09-22 授权后执行；`origin/heyang` = `5b3659c`（fast-forward，0/0 分叉） |
| 开 paper PR against main | DONE | **PR #30**：https://github.com/integritynoble/low_dose_CT/pull/30 （base `main` <- head `heyang`，Open，等待 owner 审查） |
| 更新 heyang/HEYANG_REPLY_2026-09-20.md 索引 | DONE | 2026-09-22 段已链接包与清单（见本次提交） |

---

## 总结

任务书第 1-4 步全部 DONE：论文包已提交（`5b3659c`）、已 push（`origin/heyang`）、paper PR **#30** 已开（base `main`，等待 owner 审查）；作者批准前不投稿。剩余均为 owner 决策项：8 项作者输入（§9）、第三环境取舍、artifact 公开发布。未提交的 WS-2 manifest 行尾噪声原样保留，未纳入任何提交。
