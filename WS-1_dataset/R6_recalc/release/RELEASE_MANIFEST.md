# RELEASE_MANIFEST — 策展发布包文件清单（任务 6）

- **仓库**：`D:\ZHY\low_dose_CT-heyang`（私有；当前分支 `third-env/blackwell`，HEAD `78ca452`）
- **日期**：2026-09-26
- **性质**：策展发布（curated release）清单。**不创建** Zenodo 记录 / 公共仓库 / release tag；仓库保持私有；**图像数据不分发**；**checkpoint 仅列哈希**（发送需 owner 授权）。
- **哈希口径**：SHA-256，基于**工作区文件字节**（Windows CRLF 检出，与 git 存储 LF 字节不同；如需 git 存储字节口径见 `Heyang-paper/COMPLETION_CHECKLIST.md` §7）。核验命令（PowerShell）：`Get-FileHash -Algorithm SHA256 <path>`。
- **清单状态**：A 类"随策展包分发"文件共 43 项（含本次新增 3 项发布交付物）；B 类"仅哈希、不分发"资产 = LIDC 数据树 364 项 + AAPM 数据树 25 项 + 5 个 checkpoint。

---

## 0. 总览

| 类别 | 数量 | 分发方式 |
|---|---|---|
| A1 论文包（Heyang-paper） | 11 | 随策展包分发（作者区 TODO 定稿后） |
| A2 R6 复算代码与文档 | 10 | 随策展包分发 |
| A3 哈希锚点清单（hashes/） | 5 | 随策展包分发 |
| A4 第三环境运行包（third_env/） | 4 | 随策展包分发（受控，见 §1.4 注） |
| A5 baselines 代码与许可 | 4 | 随策展包分发（保留 Apache-2.0） |
| A6 schema 规范文档 | 6 | 随策展包分发 |
| A7 PhysioNet listing | 1 | 随策展包分发 |
| A8 复算结果 JSON（核心） | 2 | 随策展包分发 |
| A9 发布交付物（本次新增） | 3 | 随策展包分发（本清单 / 权利检查表 / 可用性声明草稿） |
| B1 LIDC 数据树（图像） | 364 项 | **仅哈希**，数据本体不分发（TCIA CC BY 3.0） |
| B2 AAPM 数据树（图像） | 25 项 | **仅哈希**，数据本体不分发（TCIA 条款） |
| B3 模型权重（checkpoint） | 5 项 | **仅哈希**，发送需 owner 授权（训练来源见 §2） |

---

## 1. A 类 — 随策展包分发

### 1.1 A1 论文包（Heyang-paper/）

| 路径（相对仓库根） | 纳入理由 | SHA-256 |
|---|---|---|
| `Heyang-paper/manuscript.tex` | 论文手稿（v0.5；availability 段已替换为任务 6 草稿，DOI 占位） | `A67ADB6CC17BB9005ADE10D7D4F38B008DDE1AE07AAE4651574614982FCA98B6` |
| `Heyang-paper/manuscript.pdf` | 手稿编译产物（7 页，2026-09-26 重建） | `2BCB37EB3B27E3F945CBA620DB1BD2B0E6BB9AA7EE426993F6F88D683437C229` |
| `Heyang-paper/README.md` | 论文包说明（含 retrospective 标注） | `1126F5DFB706EC25BB4DEC0BC380169BC2FEA9D5E1A0BFA9B6BD54341BE4ECE9` |
| `Heyang-paper/CLAIM_EVIDENCE.md` | 声明-证据台账（六项覆盖 + U1–U9） | `FB98F97B6A50730D63AC1F9D547E24E56881704122D7AB9A46A8E4D017A95D85` |
| `Heyang-paper/COMPLETION_CHECKLIST.md` | 完成清单与剩余 TODO 台账（本次已同步 availability 行号） | `1D67676FDF359B8B7CE468972EAC3A0992936574F1B1CC157CC66B534D10F4CC` |
| `Heyang-paper/make_tables.py` | 论文表格生成脚本（agreement/ladder/scale） | `30D7A27C745C41FAFD0EC17B804AD6B2FEF8022EF339CFD7637C6CF3E382C8CA` |
| `Heyang-paper/references.bib` | 参考文献库 | `79430D8DBF24C88289ADC3DE1FAC30F2F35E5D8763F71AB068F28C7F42CA7E1C` |
| `Heyang-paper/tables/agreement.tex` | 表 1（per-metric 一致性） | `024966B9C661A7B7F3C87D9ABDBAC8C45A8526F03DABBCD4B97CA6A096E96294` |
| `Heyang-paper/tables/ladder.tex` | 表 2（容差阶梯） | `A62FC0C46EBFDE1B67E61B49718169CFF36E54CD24A313E1BA446A9F82CCA1BB` |
| `Heyang-paper/tables/scale.tex` | 表 3（尺度表） | `2E1BE9DB359864B9A0B417D77CF088CAA789D6CE3969794A206CF5A23B0A680C` |

### 1.2 A2 R6 复算代码与文档（WS-1_dataset/R6_recalc/）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/R6_recalc/ASSET_MANIFEST.md` | 资产清单 A1–A5（权重/loader/脚本/数据树） | `473E965605A12FDBFDC7BBD68449433D2E272F89CB36A6B0251FAFDC7DF08D45` |
| `WS-1_dataset/R6_recalc/R6_recalc_report.md` | 复算报告（环境/全量结果/时长/三步声明） | `5E61B5BD2D87844BBB39335DE25043A298A07BAFB850BA93DC9D4601D2D1A89F` |
| `WS-1_dataset/R6_recalc/R6独立复算操作指南.md` | 独立复算操作指南（§0.1 引用 ASSET_MANIFEST） | `3B68244E0057E811DAC6E0D43CF5D86DD83B42A3178B2B8CEA2D14AEC2851E8E` |
| `WS-1_dataset/R6_recalc/R6_独立复算完成总结.md` | 复算完成总结 | `620D1BFD46715F2F8B5E3B52C58EFDCEB40DB749A2608E3E40F4113A97A22774` |
| `WS-1_dataset/R6_recalc/compare_linux_vs_ref.py` | Linux-vs-reference 双判据比较器（论文数字支撑） | `2322F400BC00260F4C625469C66D334A7AED2EDD5E986883267AA0F911FBC53A` |
| `WS-1_dataset/R6_recalc/compare_full764.py` | 全量 764 比较器（Windows 历史 artifact） | `B54210A690B591B00AD7672891082C52CBBE22883373BDC6CFC81EFD0C2D12B9` |
| `WS-1_dataset/R6_recalc/freq_detectability_recalc.py` | A3 频域检测性复算脚本（detectability-freq-v1） | `EBE91B16877315F1DDEC3A1552EC9195198FF07C8AA035E0878F4809F4A014D0` |
| `WS-1_dataset/R6_recalc/statistical_tests_recalc.py` | A4 统计检验复算脚本（vendor-kw / dose-friedman） | `8DC5ADE288944B0B19E149BF182E3ACC00A3D89E20AB463EF0FB0E306A7B6748` |
| `WS-1_dataset/R6_recalc/recompare_per_metric.py` | per-metric 重比较校验（Windows artifact） | `97D783802D0F7FEC780E56AA08035CEA4C8EF871019A8BA2B0D1861E1C645B1B` |
| `WS-1_dataset/R6_recalc/tolerance_audit.py` | 容差审计脚本 | `E03E4FD8B9F11A4363E2AD3CDE32CFDDF0EB23103C4386391A5C26B7E3E9F381` |

### 1.3 A3 哈希锚点清单（WS-1_dataset/R6_recalc/hashes/）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/R6_recalc/hashes/ckpt_hashes.txt` | 5 个 checkpoint SHA-256 锚点（复算锁定用） | `006703A126DCE556F4FF1A486FF38F0BEB224A279F02F4289507DD75F65ADE00` |
| `WS-1_dataset/R6_recalc/hashes/data_hashes.txt` | LIDC 数据树 364 项哈希清单（图像仅哈希） | `1F41B875E68861A5A73DE4D2D4AB7AB467D4D831691515F23ACCB82383BF8A6B` |
| `WS-1_dataset/R6_recalc/hashes/aapm_hashes.txt` | AAPM 数据树 25 项哈希清单（图像仅哈希） | `57386E5A605A813B7AAA0A60A05D3B92F6013006B92BA3999C00C56C2C0A222C` |
| `WS-1_dataset/R6_recalc/hashes/env_pip_freeze.txt` | 复算环境依赖锁定（torch2.3.0+cu121 等） | `711BDD0FC7BD07C83AE06C41B67ECBC0B8D01053B09DE5E9CB11A3DF1A8E653D` |
| `WS-1_dataset/R6_recalc/hashes/task_spec_hash.txt` | task_spec 协议锚点（AE7AE799…） | `C16B8F4C927E1B32C04225BEAA6BBBB8D1F89E240B6E6CB4518555A015EF9E49` |

### 1.4 A4 第三环境运行包（WS-1_dataset/R6_recalc/third_env/）

> 注：本组为 task 5 交付物。`checkpoint_provenance_license.md` 明确"发送第三方前需 owner 授权"；
> 随策展包分发时须保持该受控说明，权重本体不随包。

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/R6_recalc/third_env/THIRD_ENV_RUNBOOK_2026-09-25.md` | 第三环境（Linux/Blackwell）运行手册 | `FD85DAEDFF08ED4778FFAF93567165E25CE47CB0D9D4A717DEA6097819A9AA2F` |
| `WS-1_dataset/R6_recalc/third_env/data_manifest_LIDC_AAPM.md` | 数据 manifest（LIDC/AAPM 溯源与许可） | `F6488B8FFB61E44838EC2BA0B37ACCC18D36A7EF9791C1F9498D140B8558BCCE` |
| `WS-1_dataset/R6_recalc/third_env/checkpoint_provenance_license.md` | checkpoint 来源与许可说明（受控资产） | `9E74F61D1AF2DD1732108E3A7B5CD464D456A5A1688D64D200CD41946918B3AA` |
| `WS-1_dataset/R6_recalc/third_env/THIRD_PARTY_OPERATOR_GUIDE.md` | 第三方操作者指南 | `C9036936121DD1146342C0F37556ABB6920631DB20DBFA438B11B05885CBFC65` |

### 1.5 A5 baselines 代码与许可（WS-1_dataset/baselines/）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/baselines/LICENSE` | Apache-2.0 标准许可（202 行） | `C71D239DF91726FC519C6EB72D318EC65820627232B2F796219E87DCF35D0AB4` |
| `WS-1_dataset/baselines/pyproject.toml` | 包元数据（version 0.5.0，license Apache-2.0） | `7E07F4DA8682DCC59141983A80D1C8792FBC3371E609FF1CD3C980786CCEA85F` |
| `WS-1_dataset/baselines/task_spec.json` | 训练/评估协议（SKE-Gaussian 20HU/2px 等） | `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C` |
| `WS-1_dataset/baselines/README.md` | baselines 说明（needs pwm_ldct_loader on the path） | `90BCACDD6ABF4E3E6130ED711BAA4D44E3AA97F908B533793E76334DB57D5FB1` |

### 1.6 A6 schema 规范文档（WS-1_dataset/schema/）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/schema/README.md` | schema 目录说明 | `83CFFE31D371AD94717AA82BE1E15E0978EFE110A8374851C3FC8B9F98711A1C` |
| `WS-1_dataset/schema/dataset_schema.md` | 数据集规范（Methods 引用） | `A3A8BE951FC10BB12C14E91C5A933325E6DB92AEDE341E596CD5EC086CB88635` |
| `WS-1_dataset/schema/dicom_cleaning_spec.md` | DICOM 清洗白名单规范 | `7C5DBAFFE41A4271D1FE145077D2E3E6544ACAD17B5D6A763B7BC4B0AC99FE62` |
| `WS-1_dataset/schema/dicom_to_hdf5_mapping.md` | DICOM→HDF5 映射 | `8FD148E2BE5DF44CBEB535A71B382555238CBFD839D9C100BCE4F3DD3648AE62` |
| `WS-1_dataset/schema/annotation_qa_protocol.md` | 标注 QA 协议 | `CA0E37F7673D10083B326F97A8EA41A1D35C54290EB5477DD4B6D7721BABFBD5` |
| `WS-1_dataset/schema/detectability_task_spec.md` | 检测性任务规范（§6 detectability-freq-v1） | `A64FBF2B5E89CD38A08B505F3A75B52A1837396029351973B9E4B5E57F415665` |

### 1.7 A7 PhysioNet listing

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/physionet_listing/listing.md` | PhysioNet 发布页素材（CC BY 4.0，[CONFIRM] 字段待填） | `966A290B74A6151DE25E7FBE9C664787EDA27A5E62E43D06CA3256D882B7C093` |

### 1.8 A8 复算结果 JSON（核心）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/R6_recalc/results/comparison_linux_full764.json` | Linux rerun vs reference 全量比较结果（论文数字支撑） | `5B5A18D3E2E557DC3DB4F132BBECD3F660B2EA40104F3DA2A0E2EB0AE70E7CD8` |
| `WS-1_dataset/R6_recalc/results/comparison_full764.json` | Windows 历史比较结果（route A 证据） | `065B7B99F9123C8EBABD9907140F6DA7A3F43055AFFAD5EDB08EE7F3EE25C852` |

> 其余复算中间 JSON（`results/` 下 det/freq/stat 等 28 项）按需随包附送，本清单不再逐项展开；如需完整目录哈希，可补附录。

### 1.9 A9 发布交付物（本次新增，release/）

| 路径 | 纳入理由 | SHA-256 |
|---|---|---|
| `WS-1_dataset/R6_recalc/release/RELEASE_MANIFEST.md` | 本清单 | `D5BC576CB9BA6B86D344DBDF568128FD8714D35A0066242CC4D2C04FBC9852A6` |
| `WS-1_dataset/R6_recalc/release/RIGHTS_CHECKLIST.md` | 逐项权利检查表 | `AA301E353CC2818FF7BCCD1B68A92B390D59C3A51E2C4DF2C032E77A38077D00` |
| `WS-1_dataset/R6_recalc/release/AVAILABILITY_STATEMENT_draft.md` | 可用性声明草稿（DOI 占位） | `4A687A292CA4D3E29DA00E98A76470A1C9DD6A6FBBC8A723AC6A89707E3B8C4A` |

> 注：RIGHTS_CHECKLIST / AVAILABILITY_STATEMENT_draft 已定稿不再改动；本清单为自引用条目，
> 每次编辑会使自身哈希漂移，**发布打包时以 `Get-FileHash -Algorithm SHA256 RELEASE_MANIFEST.md`
> 实测值为准**（表中值为 2026-09-26 最近一次实测）。

---

## 2. B 类 — 仅哈希、不分发

### 2.1 B1 LIDC 数据树（图像，364 项）

- **对象**：PWM-LDCT v0.5 派生数据树（HDF5 shards / annotations / metadata / splits），文件级 SHA-256 清单见 `hashes/data_hashes.txt`（364 项）。
- **状态**：**图像类数据，不分发，仅哈希**。数据本体通过 PhysioNet（credentialed, CC BY 4.0 项目层）+ 上游 TCIA（LIDC-IDRI, CC BY 3.0）渠道访问；作者不在此再分发原始图像。

### 2.2 B2 AAPM 数据树（图像，25 项）

- **对象**：AAPM 2016 真实配对 held-out 数据树（4 患者 test + split），文件级 SHA-256 清单见 `hashes/aapm_hashes.txt`（25 项）。
- **状态**：**图像类数据，不分发，仅哈希**。上游许可以 TCIA 条目为准（与 LIDC 同源条款体系）；作者不在此再分发。

### 2.3 B3 模型权重（checkpoint，5 项）

| 权重 | 大小 | SHA-256 | 状态 |
|---|---|---|---|
| `red_cnn.pt` | 7.4 MB | `DF775D088AB1E720D72A530033F9460A7CF6FDDF636ABE9757312A441A04976E` | **仅哈希；发送需 owner 授权**（训练来源未记录） |
| `learn.pt` | 774 KB | `3EABF5254C4F6F96706872DBB26EA8E89707A74F9FBAA6F19208115730B68EA0` | **仅哈希；发送需 owner 授权**（训练来源未记录） |
| `ctformer.pt` | 350 MB | `AEAD0C15D859E25DAC5AFFD51FF4EEDC108060E08165E739669ED40B106107B2` | **仅哈希；发送需 owner 授权**（早期大模型存档，不作为复算对照） |
| `corediff.pt` | 19 MB | `41ABA6748778BECD3E10595014BE36CAA84C4B238EE787380444E59418DFA7AD` | **仅哈希；发送需 owner 授权**（训练来源未记录） |
| `ctformer_small_retrain.pt` | 9.7 MB | `78C0C59C91920074FBFB16F0E939B21C784811F11867B0E4E37C59864CFCCF2B` | **仅哈希；发送需 owner 授权**（作者重训，有训练报告 `output/ctformer_retrain_report.md`） |

- **说明**：`blur` 为内置 trap（`get_model("blur")`），无需权重。`.gitignore` 忽略 `*.pt`，git 仓库内无权重文件。
- **授权路径**：owner 明确授权后，按 `third_env/checkpoint_provenance_license.md` §5 清单打包交付（含 task_spec + 数据树子集）。

---

## 3. 明确不纳入发布包的项目

| 项 | 原因 |
|---|---|
| `R6_recalc/*.bak`（4 个） | 备份中间产物，非交付物 |
| `Heyang-paper/*.log / .aux / .bbl / .blg / .out` | LaTeX 编译中间产物 |
| `WS-4_leaderboard` 未提交 3 个 py | 其他工作流（leaderboard）未完成项，不属于本发布范围 |
| 仓库内未跟踪/未提交改动（third_env 4 文档的本地修改等） | 待相应任务 owner 决策，不进入本发布包 |
| 图像数据本体（LIDC/AAPM 数据树） | 上游许可限制 + 任务约束"不分发图像" |
| checkpoint 权重本体（5 个 .pt） | 受控资产，发送需 owner 授权 |