# LIDC-IDRI 数据下载 manifest 与哈希对照（2026-09-25）

> **任务 5（第三环境）交付物 3/5**
> 说明 LIDC-IDRI 原始数据的下载方式（TCIA 来源）、两层许可关系，以及第三环境
> 实际运行所需的两棵数据树（LIDC sim 364 项 / AAPM 25 项）的哈希校验方法。

---

## 1. LIDC-IDRI 原始数据来源与下载（TCIA）

**数据源**：The Cancer Imaging Archive (TCIA) — **LIDC-IDRI** 公开数据集
（1,010 名患者的胸部 CT 与结节标注）。

**下载方式**（TCIA 官方流程）：

1. 打开 TCIA 的 LIDC-IDRI 数据集页面（https://www.cancerimagingarchive.net/ 搜索
   "LIDC-IDRI"）。
2. 点击页面 **Download** 按钮，保存一个 **`.tcia` manifest 文件**（清单格式）。
3. 安装 **NBIA Data Retriever**（TCIA 官方下载客户端，Windows/macOS/Linux 均有）。
4. 用 NBIA Data Retriever 打开该 `.tcia` 文件，选择下载目录，开始批量拉取原始
   DICOM 文件。下载完成后得到完整的 LIDC-IDRI 原始 DICOM 树。

**许可（TCIA 层）**：TCIA 的 LIDC-IDRI 数据依 **Creative Commons Attribution 3.0
Unported（CC BY 3.0）** 提供，可自由浏览、下载，并可用于商业、科研与教育目的，
需注明出处（署名 TCIA / LIDC-IDRI 数据集，并遵循其 citation 要求）。

---

## 2. 两层许可（重要：不要混淆）

| 层 | 对象 | 许可 | 说明 |
|---|---|---|---|
| **上游数据层** | LIDC-IDRI 原始 DICOM（TCIA 下载） | **CC BY 3.0 Unported** | 数据源自 TCIA；引用/再分发须署名 |
| **项目自身发布层** | PWM-LDCT v0.5 的 PhysioNet listing / 二次加工资产 | **CC BY 4.0**（`physionet_listing/`） | 项目对加工后数据集（HDF5 树、清单、标注对齐等）的发布许可 |

> 两层许可是**叠加而非替代**：第三方使用 PWM-LDCT 加工产物时，既要遵守项目
> PhysioNet listing 的 CC BY 4.0 条款，也要遵守上游 LIDC-IDRI 的 CC BY 3.0
> 署名要求；TCIA 数据的使用与再分发以 CC BY 3.0 为限。

---

## 3. 第三环境实际运行的数据树与哈希对照

第三环境 eval 使用的是 **PWM-LDCT 已加工的 LIDC 模拟低剂量树**（
`output_gpu`，含 hdf5 子树 + `manifest.sha256`），**不是** TCIA 原始 DICOM；
AAPM held-out 树同理为加工产物。因此运行时校验对象是这两棵加工树的逐文件
SHA256 清单：

| 数据树 | 项数 | 哈希清单 | 说明 |
|---|---|---|---|
| LIDC sim 树（`D:\ZHY\LIDC3DDataSet\output_gpu`） | **364** | `R6_recalc/hashes/data_hashes.txt` | eval 的 `--dataset` 根；3 dose × test split |
| AAPM held-out 树（`pipelines\_runtime\aapm_tree_v1`） | **25** | `R6_recalc/hashes/aapm_hashes.txt` | 频域检测性复算（A5）用，第三环境运行包不含 |

### 3.1 逐项校验说明

`data_hashes.txt` / `aapm_hashes.txt` 每行格式：
`<SHA256>  <作者侧绝对路径>`（Windows 盘符路径）。校验依据是 **SHA256 值本身**；
路径前缀只是定位符，第三方落盘后路径必然变化，因此用「前缀替换 + 逐项比对」。

### 3.2 Linux 校验命令（第三环境）

```bash
# LIDC sim 树（364 项）
python3 - <<'EOF'
import hashlib, pathlib, sys
repo = "<repo 根>/WS-1_dataset"
tree_root = "<LIDC sim 树实际根>"           # 例如 /data/LIDC3DDataSet/output_gpu
hashfile = f"{repo}/R6_recalc/hashes/data_hashes.txt"
ref = {}
for line in open(hashfile, encoding="utf-8"):
    h, p = line.strip().split("  ", 1)
    ref[p.replace("\\", "/")] = h.lower()
ok = miss = bad = 0
for p, h in ref.items():
    rel = p.replace("D:/ZHY/LIDC3DDataSet/output_gpu/", "")
    f = pathlib.Path(tree_root) / rel
    if not f.exists():
        miss += 1; continue
    if hashlib.sha256(f.read_bytes()).hexdigest() == h:
        ok += 1
    else:
        bad += 1
print(f"LIDC ok={ok} bad={bad} missing={miss} total={len(ref)}")
sys.exit(0 if (ok == len(ref) and bad == 0 and miss == 0) else 1)
EOF

# AAPM 树（25 项，可选）
python3 - <<'EOF'
import hashlib, pathlib, sys
repo = "<repo 根>/WS-1_dataset"
tree_root = "<AAPM 树实际根>"               # 例如 /data/aapm_tree_v1
hashfile = f"{repo}/R6_recalc/hashes/aapm_hashes.txt"
ref = {}
for line in open(hashfile, encoding="utf-8"):
    h, p = line.strip().split("  ", 1)
    ref[p.replace("\\", "/")] = h.lower()
ok = miss = bad = 0
for p, h in ref.items():
    rel = p.replace("D:/ZHY/low_dose_CT-heyang/WS-1_dataset/pipelines/_runtime/aapm_tree_v1/", "")
    f = pathlib.Path(tree_root) / rel
    if not f.exists():
        miss += 1; continue
    if hashlib.sha256(f.read_bytes()).hexdigest() == h:
        ok += 1
    else:
        bad += 1
print(f"AAPM ok={ok} bad={bad} missing={miss} total={len(ref)}")
sys.exit(0 if (ok == len(ref) and bad == 0 and miss == 0) else 1)
EOF
```

期望：LIDC `ok=364 bad=0 missing=0`；AAPM `ok=25 bad=0 missing=0`。

> 若前缀结构与上方示例不同，仅需把 `rel` 提取逻辑改为「用清单中作者路径的公共
> 前缀裁剪后拼到本地根」。也可生成 `sha256sum -c` 兼容清单后直接校验。

---

## 4. 其他资产哈希（交叉引用）

| 资产 | 哈希清单 |
|---|---|
| task_spec.json | `R6_recalc/hashes/task_spec_hash.txt`（`AE7AE799…`） |
| 5 个模型权重 | `R6_recalc/hashes/ckpt_hashes.txt` |
| pwm_ldct_loader 源码树组合哈希 | `ASSET_MANIFEST.md` A2（`87BA7C4F…`） |

> 数据哈希清单本身由作者侧生成于 R6 复算（`R6_recalc/hashes/`），第三环境沿用
> 同一锚点，保证跨环境可比。
