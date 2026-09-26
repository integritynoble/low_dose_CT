# Data and code availability — 声明草稿（DOI 占位）

- **用途**：替换 `Heyang-paper/manuscript.tex` §Data and code availability（原 L318–L321 TODO 占位，替换后行号以实测为准）。
- **状态**：草稿，待 owner 定稿；DOI 处为占位符 `[DOI PLACEHOLDER]`，注册策展发布包后替换。
- **约束遵循**：仓库保持私有；不创建 Zenodo / 公共仓库 / release tag；图像数据不分发；checkpoint 仅列哈希（发送需 owner 授权）。

---

## 一、手稿替换文本（LaTeX，可直接粘贴至 manuscript.tex）

```latex
\section*{Data and code availability}
The evaluation code and the independent-recomputation scripts used in this study are
included in the curated release package archived under DOI [DOI PLACEHOLDER]; the package
manifest lists each file together with its SHA-256 checksum. The underlying image datasets,
LIDC-IDRI and the AAPM 2016 low-dose CT challenge data, remain available through their
original repositories under their respective licenses and are not redistributed here;
content-addressed hash manifests of the derived data trees are provided in the release
package for verification. Model checkpoints are identified by SHA-256 hash in the release
manifest and are not redistributed. Source code is additionally available from the
corresponding author on request while the repository remains private.
```

## 二、声明要点核对

| 声明项 | 文本承诺 | 依据 |
|---|---|---|
| 代码可用性 | 复算/评估代码随策展发布包（DOI）分发；仓库私有期间可向通讯作者索取 | COMPLETION_CHECKLIST §10；任务6约束（仓库保持私有，不建公共仓库） |
| 数据可用性 | LIDC-IDRI / AAPM 2016 指向原始仓库，各自许可约束，**不在此再分发**；提供派生数据树哈希清单 | ASSET_MANIFEST A5；README v0.5（LIDC CC BY 3.0 / 发布层 CC BY 4.0）；COMPLETION_CHECKLIST §10 |
| 权重可用性 | checkpoint 仅 SHA-256 标识，**不随包分发** | ASSET_MANIFEST A1；checkpoint_provenance_license.md §0（发送需 owner 授权） |
| DOI | `[DOI PLACEHOLDER]`，注册后替换 | 任务6：不创建 Zenodo，仅占位 |

## 三、配套哈希锚点

| 锚点 | 值 | 来源 |
|---|---|---|
| 任务协议 | `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`（task_spec.json） | `R6_recalc/hashes/task_spec_hash.txt` |
| 权重哈希（5 项） | 见 `R6_recalc/hashes/ckpt_hashes.txt` | ASSET_MANIFEST A1 |
| LIDC 数据树（364 项） | 见 `R6_recalc/hashes/data_hashes.txt` | ASSET_MANIFEST A5 |
| AAPM 数据树（25 项） | 见 `R6_recalc/hashes/aapm_hashes.txt` | ASSET_MANIFEST A5 |

> 注：第三环境运行包（`third_env/`）中 `checkpoint_provenance_license.md` 为内部受控说明，
> 不含于对外可用性声明文本；手稿声明不授予任何 image / checkpoint 再分发权。