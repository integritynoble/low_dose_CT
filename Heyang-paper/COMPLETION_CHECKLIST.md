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
| **[2026-09-26，任务 1 收尾] 数字归属 Linux vs 参考** | DONE | 头部注释与全部数字改由 `comparison_linux_full764.json`（Linux rerun vs reference）支撑；摘要失败 two of five（RED-CNN/CoreDiff）、90/375、CTformer 翻转通过；摘要/方法删除 "driver"；route (a) 标注 earlier Windows same-OS recomputation（2026-09-05/06）；Limitations 第三环境改 "a third environment is planned"（L302-304，结果不写入） |

## 2. 验证命令结果（2026-09-22 任务书第 3 步复跑）

| 命令 | 结果 | 状态 |
|---|---|---|
| `python Heyang-paper/make_tables.py` | 重新生成 agreement.tex / ladder.tex / scale.tex，exit=0 | DONE |
| `python Heyang-paper/make_tables.py --check` | `all tables current`，exit=0 | DONE |
| `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | blur/corediff/ctformer/learn/red_cnn 全 PASS、outside declared 0、overall PASS、committed verdict matches、exit=0 | DONE |
| `python WS-1_dataset/R6_recalc/compare_linux_vs_ref.py --check` | **[2026-09-26]** Linux 新 artifact 重算一致（abs/rel 双判据 + 阶梯 + 基线哈希均在比较器内生成），exit=0 | DONE |

**校验脚本分工（2026-09-26，见台账 §6 前注）**：Windows 历史 artifact
（`comparison_full764.json`）→ `recompare_per_metric.py --check`（验证保留证据，
应仍 PASS）；Linux 新 artifact（`comparison_linux_full764.json`）→
`compare_linux_vs_ref.py --check`。新 artifact 的 `per_model.status` 保留为 abs
判定，勿用 `recompare_per_metric.py` 直接校验（会误报 MISMATCH）。

## 3. manuscript.pdf 构建（2026-09-26 重建）

| 项 | 值 |
|---|---|
| 工具链 | MiKTeX（pdfTeX 4.23）+ bibtex（TeX 引擎在 elevated 会话被 MiKTeX 拦截，经降权计划任务 `compile_manuscript.cmd` 构建，任务已清理） |
| 编译流程 | pdflatex → bibtex → pdflatex → pdflatex，四步均 exit=0（无 error / undefined citation） |
| 产物 | `Heyang-paper/manuscript.pdf`，7 页，199,429 B（SHA256 见 §7） |
| 核验 | 无 undefined citation/reference（log 扫描）；摘要数字 "failed for two of five"、90/375、RED-CNN worst abs 34.26 与正文/表格一致；作者区 TODO 红色显示（预期，待 owner） |

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

**2026-09-23（HEYANG_NEXT_2026-09-22.md 任务 2/3/4）**：本清单所在提交为 §7 哈希与 `heyang/HEYANG_REPLY_2026-09-20.md` 索引的基线。提交内容：`heyang/evidence/` 6 证据文件入仓（已剥离 AI 水印与 frontmatter，经敏感信息扫描 0 命中）、`HEYANG_REPLY` 6 个本地绝对路径链接替换为仓库相对路径、`CLAIM_EVIDENCE.md` 4 处 ENV_RECON 引用改为仓库内相对链接、WS-4 `leaderboard.py` 补 `Set` 导入 / `verifier.py` 删除未用变量、§7 哈希按 git 存储字节重算（LF 约定）。

**2026-09-26（HEYANG_NEXT_2026-09-25.md 任务 1 收尾）**：任务 1 收尾提交链（heyang 分支，均未 push）：

| commit | 说明 |
|---|---|
| `7c53e8d` | R6: archive Linux rerun outputs/logs (U10)（`results/linux_rerun/` 5 JSON + 5 log + freeze，阶段 A） |
| `81589cc` | R6: add Linux-vs-reference comparator + artifact（`compare_linux_vs_ref.py` + `results/comparison_linux_full764.json`，阶段 B） |
| `5a12010` | paper: regenerate tables and align manuscript to Linux rerun（`make_tables.py` / `manuscript.tex` / `tables/agreement.tex` / `tables/ladder.tex` / `manuscript.pdf`，阶段 C/E/F） |
| `1b0c0c9` | paper: ledger and reply index decisions（`CLAIM_EVIDENCE.md` / `HEYANG_REPLY_2026-09-20.md` / 本清单，阶段 G/H + 行号同步） |
| `9dd8789`（rehash 提交） | paper: rehash section 7 at 1b0c0c9 (task-1 baseline)（§7 九项 SHA256 重算，基线 = 上一提交 `1b0c0c9`，阶段 I） |

## 6. 未提交改动（原样保留，不属于本次论文包）

`git status --short`（提交前快照）：

| 路径 | 状态 |
|---|---|
| `WS-2_framework/pwm_dose_equivalence/reproducibility/reproducible_manifest.json` | M（仅行尾噪声，非任务内容） |

本次论文包提交范围：`Heyang-paper/manuscript.tex`、`README.md`、`CLAIM_EVIDENCE.md`、`COMPLETION_CHECKLIST.md`、`manuscript.pdf` 共 5 文件。

## 7. artifact SHA256（可复现版，2026-09-26 任务 1 收尾提交重算）

**计算对象**：git 存储字节（仓库 `core.autocrlf=true` 规范化后，行尾 **LF**）。2026-09-26 在任务 1 收尾提交 **`1b0c0c9`** 处重算（`3fbf5bf` 曾改 9 项中 3 项、本次任务 1 改 6 项，均不可在旧基线复现）；**基线 = `1b0c0c9`**。

| 文件 | SHA256（git 存储字节） | blob SHA1 |
|---|---|---|
| Heyang-paper/manuscript.pdf | 2BCB37EB3B27E3F945CBA620DB1BD2B0E6BB9AA7EE426993F6F88D683437C229 | 48675680 |
| Heyang-paper/manuscript.tex | 7EA83F18AF97048EC013686190BF1849A45230253F36EDFCB8DABCED0ED626DD | b5f8c863 |
| Heyang-paper/README.md | 1126F5DFB706EC25BB4DEC0BC380169BC2FEA9D5E1A0BFA9B6BD54341BE4ECE9 | 9506fbc5 |
| Heyang-paper/CLAIM_EVIDENCE.md | B5B887F3DCE59DFFD0517D2248F7931C2DE4D78E3C04DBC300E9E472F4371E29 | 52979370 |
| Heyang-paper/make_tables.py | 83FD69349C2E984FF56EE5A407CAEDAAC7BA5C394CBE8AC75461AEEE38E49B3E | c10582b2 |
| Heyang-paper/references.bib | 935FB2866FCCE55668DB852F6C93C7CE09B96C01A3FCFA14784256097F7A8D75 | 8810e186 |
| Heyang-paper/tables/agreement.tex | 845B2D5340E144C56B62FAD29455393D50F49E3EED7777D6F5E2D05C90CE6E41 | 90eb2b2e |
| Heyang-paper/tables/ladder.tex | F07A8E93E84A0AC83C271FAC61F75446A0BA089FD10911CC1AB16AF91E508194 | f48bb59b |
| Heyang-paper/tables/scale.tex | 0DAFCDAAC8E7F6FE40B5317B9A22DD3C8A1957E8F81CD4AF6D8BC745BB0A1045 | e918f81d |

**复现命令**：
- blob：`git ls-files -s Heyang-paper/<file>`（第三字段）
- SHA256：`git show 1b0c0c9:Heyang-paper/<file> | sha256sum`（Windows：`(git show 1b0c0c9:Heyang-paper/<file>) | Get-FileHash -Algorithm SHA256`，二进制文件用 `cmd /c "git show 1b0c0c9:Heyang-paper/<file> > tmp"` 后取哈希）

**一致性说明**：9 项中 README.md、references.bib、tables/scale.tex 与 `21fd395` 版本逐字节一致（未变）；manuscript.pdf/manuscript.tex/make_tables.py/agreement.tex/ladder.tex 因任务 1（Linux 数字归位）变化、CLAIM_EVIDENCE.md 因台账更新变化——均为任务 1 预期改动，非意外漂移。其他关键 artifact 哈希（台账 §6.1）：task_spec `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`；5 个 checkpoint 哈希见 `WS-1_dataset/R6_recalc/hashes/ckpt_hashes.txt`。

## 8. 剩余 TODO（4 处，全部 owner 决策；2026-09-26 行号已按当前手稿同步）

| 行号 | 内容 | owner |
|---|---|---|
| L23 | author list, affiliations, ORCIDs, corresponding author | 作者 |
| L319 | 指向发布的 artifact / comparison JSON / 重推导（data/code availability 措辞） | 作者 |
| L324 | CRediT statement | 作者 |
| L327 | Per-author declaration | 作者 |

> 第三环境不再列入 TODO：owner 2026-09-25 决定执行（原生 Linux RTX 5090），
> Limitations 已改 "A third environment is planned; its results are not reported
> here"（manuscript L302-304，任务 5 承接）。

## 9. Owner 决策请求（紧凑列表；行号 2026-09-26 按当前手稿同步）

请在评审时一次性确认以下输入，每项阻断对应字段：

1. **作者顺序（author order）** — 阻断 L23 author list
2. **单位（affiliations）** — 阻断 L23
3. **ORCIDs** — 阻断 L23
4. **通讯作者（corresponding author）** — 阻断 L23
5. **CRediT 贡献声明** — 阻断 L324
6. **Per-author declarations（利益冲突/资助/伦理）** — 阻断 L327
7. **第三环境实验** — **已定**（owner 2026-09-25：原生 Linux RTX 5090 工作站，
   任务 5 承接；manuscript L302-304 已写 planned，结果不写入）
8. **artifact 公开发布决策** — 阻断 L319（data/code availability 措辞依赖此决定；
   owner 2026-09-25 已定策展发布带 DOI，措辞见 §10）

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
