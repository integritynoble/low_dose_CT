# THIRD ENV RUNBOOK — 第三环境运行手册（2026-09-25）

> **任务 5（第三环境）交付物 1/5**
> 目标机：owner 原生 Linux RTX 5090 工作站（Ubuntu 26.04 / NVIDIA Blackwell sm_120 / driver 595.71.05 / CUDA 13.2）。
> 本手册**自包含**：第三方操作者不看其它文档即可从命名 commit 出发，复算出 5 个
> `*_det_full764.json` 并完成与参考结果的比对。**本手册不要求操作者复算其它内容**
> （频域检测性 / 统计检验不在第三环境运行包范围内）。
>
> 配套交付物：
> - `../third_env/THIRD_PARTY_OPERATOR_GUIDE.md`（交付物 5/5：操作者前置条件与回传约定）
> - `../third_env/data_manifest_LIDC_AAPM.md`（交付物 3/5：数据下载 manifest 与哈希对照）
> - `../third_env/checkpoint_provenance_license.md`（交付物 4/5：checkpoint 来源与许可）
> - git 分支 `third-env/blackwell`（交付物 2/5：Blackwell 支持的环境分支）

---

## 0. 目标机与版本决策（owner 定）

| 项 | 值 |
|---|---|
| OS | Ubuntu 26.04（原生 Linux，非 WSL） |
| GPU | NVIDIA GeForce RTX 5090（Blackwell 架构，compute capability sm_120） |
| 驱动 | 595.71.05（CUDA 13.2 运行时） |
| CUDA toolkit | 13.2（随驱动可用）；PyTorch 侧见 §1.2 版本决策 |
| Python | 3.10+（推荐 3.12，与 R6 复算环境一致） |
| 与现两环境的差异 | 参考=本地运行环境、复算=Windows 2×RTX 4090；第三环境为**原生 Linux + Blackwell**，全轴不同 |

**版本决策依据**（2026-09-25 检索结论）：
- **PyTorch 2.7.0 是首个原生支持 Blackwell（sm_120）的稳定版**，随附 CUDA 12.8 wheels（cu128）。
- **CUDA 13.0 为 PyPI 稳定发布**（支持 Blackwell 10.0 / 12.0 架构）；**CUDA 13.2 为实验版**
  （`https://download.pytorch.org/whl/nightly/cu132`，仅 nightly 构建）。
- 驱动 595.71.05 兼容 CUDA 12.8 / 13.0 / 13.2 应用运行时（驱动向后兼容更低 CUDA 应用）。

**推荐安装路线（二选一，默认路线 A）**：

| 路线 | torch 版本 | torchvision | index-url | 状态 |
|---|---|---|---|---|
| **A（推荐）** | `>=2.7.0`（如 2.9.x / 2.11.x） | 随 torch 配套（pip 自动解析） | `https://download.pytorch.org/whl/cu128` | 稳定 wheels，明确支持 sm_120 |
| B | PyPI 默认（`pip install torch torchvision`） | 随 torch 配套 | PyPI（CUDA 13.0 稳定版） | 稳定；装到 13.0 系 torch 亦支持 Blackwell |
| C | nightly `cu132` | 随 torch 配套 | `https://download.pytorch.org/whl/nightly/cu132` | **实验版**，不推荐第三方操作者首选 |

> 判据侧影响：torch 版本只影响 GPU 内核选择与数值路径，**不改变任何指标定义
> （eval.py / observers.py 计算逻辑一行不许动）**；判据为相对 1e-4（per-metric），
> 详见 §6。

---

## 1. 前置：仓库、分支与依赖

### 1.1 取得代码（从命名 commit 开始）

第三方操作者从 owner 处获得仓库（私有仓库 + 已授权资产包，见
`THIRD_PARTY_OPERATOR_GUIDE.md` §1 / `checkpoint_provenance_license.md` §0 授权条款）。

```bash
# 克隆并切到第三环境分支（交付物 2/5，基于 heyang HEAD 9ce3388 创建）
git clone <repo-url> low_dose_CT-heyang
cd low_dose_CT-heyang
git checkout third-env/blackwell
git log -1 --oneline        # 应显示 third-env/blackwell 分支最新提交（任务5 环境分支提交）
```

**命名基线**：源码基线 = 分支 `third-env/blackwell`（基于 `9ce3388`（含任务 1-4 的
7 个已提交未 push commit）+ 任务 5 环境提交）。`git rev-parse HEAD` 应能复现
运行手册所附的 commit hash（以交付时报告值为准）。

### 1.2 环境搭建（Python venv + pip）

```bash
python3 -m venv .venv_t3
source .venv_t3/bin/activate
python -m pip install -U pip

# 路线 A（推荐）：PyTorch ≥2.7.0 + CUDA 12.8 wheels（明确支持 Blackwell sm_120）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
# （若选择路线 B：pip install torch torchvision   # PyPI 默认 = CUDA 13.0 稳定版）
# （若选择路线 C（实验，不推荐）：pip install torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu132）

# 其余依赖（与 linux_pip_freeze.txt 对齐的科学栈）
pip install numpy==1.26.4 scipy==1.13.1 scikit-image==0.23.2 tifffile==2026.3.3 \
            h5py==3.16.0 pydicom==3.0.2 einops==0.8.2 lpips==0.1.4 timm==1.0.29 \
            pillow==12.3.0 tqdm==4.70.0 PyYAML==6.0.3 requests==2.34.2 safetensors==0.8.0

# 两个 editable 本地包（顺序：loader 先，baselines 后——baselines 依赖 loader）
pip install -e WS-1_dataset/pwm_ldct_loader
pip install -e WS-1_dataset/baselines
```

> **loader 与 baselines 均为 editable 安装**（`pip install -e`），与 R6 复算的
> `linux_pip_freeze.txt` 中的两个 editable 包对应。安装后执行冒烟验证（§4）。

### 1.3 依赖版本对照（第三环境 vs 已交付环境）

| 包 | R6 复算/参考环境 | 第三环境（本手册） |
|---|---|---|
| torch | 2.3.0+cu121 | **≥2.7.0（cu128 / cu130，路线 A/B）** |
| torchvision | 0.18.0+cu121 | 随 torch 配套（≥0.22.0） |
| numpy / scipy | 1.26.4 / 1.13.1 | 同左 |
| scikit-image / tifffile | 0.23.2 / 2026.3.3 | 同左 |
| pydicom | 3.0.2 | 同左 |
| baselines / loader | editable（源码树） | editable（同左） |

> **不动指标定义**：`eval.py / observers.py / freq_detectability_recalc.py /
> statistical_tests_recalc.py` 的计算逻辑严禁改动。分支 `third-env/blackwell`
> 相对 heyang 只含环境声明类改动（pyproject.toml / README），见交付物 2/5 的
> diff 摘要。

---

## 2. 数据与权重放置 + 哈希校验

### 2.1 目录布局（第三环境约定）

```text
<工作根>/low_dose_CT-heyang/
├── WS-1_dataset/
│   ├── baselines/checkpoints/          # 5 个权重（git 忽略 *.pt，需随资产包提供）
│   ├── baselines/task_spec.json        # 任务规格（SKE-Gaussian 20HU / 2px）
│   ├── R6_recalc/hashes/               # data_hashes.txt / aapm_hashes.txt / ckpt_hashes.txt / task_spec_hash.txt
│   └── pipelines/_runtime/aapm_tree_v1/ # AAPM held-out 树（仅频域复算用，第三环境不需要）
├── <LIDC sim 树>/output_gpu/           # 364 项 LIDC 模拟低剂量树（eval 的 --dataset 根）
└── third_env_run/                      # 运行工作目录（放输出 JSON + 日志）
```

### 2.2 数据放置与哈希校验

**LIDC sim 树（eval 输入，364 项）**：由 owner 提供（与
`D:\ZHY\LIDC3DDataSet\output_gpu` 同构的副本，含 hdf5 子树 + manifest.sha256）。
校验：对照 `R6_recalc/hashes/data_hashes.txt`（364 项，逐文件 SHA256）。

```bash
cd <LIDC sim 树根>
# Linux（sha256sum）：
sha256sum -c <repo>/WS-1_dataset/R6_recalc/hashes/data_hashes_linux.txt   # 见下方生成说明
# 或逐项校验：
python3 - <<'EOF'
import hashlib, pathlib
ref = {}
for line in open("<repo>/WS-1_dataset/R6_recalc/hashes/data_hashes.txt", encoding="utf-8"):
    h, p = line.strip().split("  ", 1)
    ref[p.replace("\\", "/")] = h.lower()
ok = miss = bad = 0
for p, h in ref.items():
    f = pathlib.Path(p.replace("D:/ZHY/", "<LIDC sim 树根>/"))
    if not f.exists(): miss += 1; continue
    if hashlib.sha256(f.read_bytes()).hexdigest() == h: ok += 1
    else: bad += 1
print(f"ok={ok} bad={bad} missing={miss} total={len(ref)}")
EOF
# 期望：ok=364 bad=0 missing=0
```

> **说明**：`data_hashes.txt` 记录的是作者侧绝对路径（Windows 盘符）。第三方
> 操作者落盘后路径前缀会变，因此本手册提供两种校验方式：①生成
> `data_hashes_linux.txt`（把 `D:\ZHY\LIDC3DDataSet\output_gpu\` 前缀替换为实际
> 根路径），用 `sha256sum -c` 校验；②用上面的 Python 片段按前缀替换后逐项校验。
> **校验依据是 SHA256 值本身，路径前缀仅为定位符**。AAPM 树同理（§2.3）。

**task_spec.json**：SHA256 必须为
`AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`
（`R6_recalc/hashes/task_spec_hash.txt`）。

```bash
sha256sum <repo>/WS-1_dataset/baselines/task_spec.json
# 期望输出：AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C
```

### 2.3 AAPM 树（可选，第三环境 eval 不使用）

第三环境只跑 LIDC 全量 eval；AAPM 树（25 项，`aapm_hashes.txt`）仅供频域检测性
复算（A3/A5，不在本运行包范围）。如 owner 要求操作者顺带核验数据链完整性，
可对照 `R6_recalc/hashes/aapm_hashes.txt`（25 项）逐项校验，命令同上（前缀替换
为实际 AAPM 树根，期望 ok=25 bad=0 missing=0）。

### 2.4 权重放置与哈希校验

5 个权重（`ckpt_hashes.txt`，blur 为内置 trap 无需权重）：

| 权重 | SHA256（前缀） | 用途 |
|---|---|---|
| `red_cnn.pt` | `DF775D08…` | red_cnn eval |
| `learn.pt` | `3EABF525…` | learn eval |
| `ctformer.pt` | `AEAD0C15…` | **早期大模型存档，不作为本复算对照** |
| `corediff.pt` | `41ABA674…` | corediff eval |
| `ctformer_small_retrain.pt` | `78C0C59C…` | **CTformer 复算实际权重（模型字段 ctformer_small）** |

```bash
cd <repo>/WS-1_dataset/baselines/checkpoints
sha256sum red_cnn.pt learn.pt ctformer.pt corediff.pt ctformer_small_retrain.pt
# 与 R6_recalc/hashes/ckpt_hashes.txt 逐项比对，全部一致才继续
```

> **CTformer 注意事项（R6 复算 §7.3 教训）**：on-board 的
> `ctformer_results_det_full764.json` 由 `ctformer_small_retrain.pt` 产出
> （model 字段 = `ctformer_small`）；**严禁用 `ctformer.pt`（标准大模型）执行
> 第三环境 ctformer 复算**，否则 psnr 差 9–13 dB。

---

## 3. 复算命令序列（从命名 commit → 5 个 *_det_full764.json）

固定 seed 集：`42, 2023, 7, 12345, 999`（对应 eval.py `FIXED_SEED_SET`）；
det-trials = **64**；split = **test**；数据根 = `<LIDC sim 树>/output_gpu`。

```bash
source .venv_t3/bin/activate
cd <repo>/low_dose_CT-heyang
export LIDC_ROOT=<LIDC sim 树根>/output_gpu
export CKPT=WS-1_dataset/baselines/checkpoints
export OUT=<工作根>/third_env_run
mkdir -p "$OUT"

# 1) blur trap（内置 trap，无权重；--checkpoint blur）
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" \
    --checkpoint blur \
    --split test \
    --seeds 42,2023,7,12345,999 \
    --out "$OUT/blur_det_full764.json" \
    --det-trials 64 2>&1 | tee "$OUT/blur.log"

# 2) red_cnn
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" \
    --checkpoint "$CKPT/red_cnn.pt" \
    --split test \
    --seeds 42,2023,7,12345,999 \
    --out "$OUT/red_cnn_det_full764.json" \
    --det-trials 64 2>&1 | tee "$OUT/red_cnn.log"

# 3) learn
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" \
    --checkpoint "$CKPT/learn.pt" \
    --split test \
    --seeds 42,2023,7,12345,999 \
    --out "$OUT/learn_det_full764.json" \
    --det-trials 64 2>&1 | tee "$OUT/learn.log"

# 4) ctformer —— 必须使用 ctformer_small_retrain.pt（勿用 ctformer.pt）
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" \
    --checkpoint "$CKPT/ctformer_small_retrain.pt" \
    --split test \
    --seeds 42,2023,7,12345,999 \
    --out "$OUT/ctformer_det_full764.json" \
    --det-trials 64 2>&1 | tee "$OUT/ctformer.log"

# 5) corediff
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" \
    --checkpoint "$CKPT/corediff.pt" \
    --split test \
    --seeds 42,2023,7,12345,999 \
    --out "$OUT/corediff_det_full764.json" \
    --det-trials 64 2>&1 | tee "$OUT/corediff.log"
```

**产出**：`$OUT/{blur,red_cnn,learn,ctformer,corediff}_det_full764.json`
（每文件含 `per_seed` × `per_dose` 的 fidelity + detectability；每模型
5 seeds × 3 dose × 764 slices）。

> 可选并行：5 个模型相互独立，可在多 GPU / 后台并行执行（如 `nohup … &`）；
> 单卡串行亦可。断点续跑：单模型单命令内已按 seed 聚合写文件，重跑覆盖即可。

---

## 4. 冒烟验证（建议先跑，再进全量）

```bash
# blur seed 42 单 seed 冒烟（3 dose × 764 slices）
python -m pwm_ldct_baselines eval \
    --dataset "$LIDC_ROOT" --checkpoint blur --split test --seed 42 \
    --out "$OUT/smoke_blur_seed42.json" --det-trials 64

# 环境自检
python - <<'EOF'
import torch, torchvision, numpy, scipy, skimage, pydicom
import pwm_ldct_loader, pwm_ldct_baselines
print("torch", torch.__version__, "cuda_avail", torch.cuda.is_available(),
      "devices", torch.cuda.device_count())
print("capability", torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None)
EOF
```

期望：`cuda_avail=True`、`devices>=1`、capability 首元素 ≥ **12**（Blackwell sm_120）。

---

## 5. 预期运行时长（参照与声明）

以 R6 报告 §10.1 的 **2×RTX 4090（确定性内核）实测**为参照：

| 模型 | 4090 实测（R6 §10.1） | 第三环境 5090 预期 |
|---|---|---|
| red_cnn | 585.4 min | 更快（需实测，不预设倍数） |
| ctformer（ctformer_small_retrain.pt） | 422.8 min | 更快（需实测） |
| corediff | 1824.1 min | 更快（需实测） |
| blur / learn | 未单列（R6 未重跑，原复算 bit-identical） | 预计远低于上述模型 |

**声明**：Blackwell 架构 + 更新的 CUDA 通常更快，但**必须实测后如实记录**；不得
引用 4090 数值冒充 5090 耗时。操作者在回传 JSON 时须附每个模型的 wall-clock
（见 `THIRD_PARTY_OPERATOR_GUIDE.md` §4 回传清单）。

---

## 6. 比对方法与判据（验收标准）

### 6.1 双判据（不变）

| 判据 | 类型 | 容差 | 说明 |
|---|---|---|---|
| shipped（预注册） | 绝对 | 1e-6 | 原样保留；跨环境通常不满足，作为机器 FAIL 保留 |
| per-metric declaration | 相对（按指标量纲） | **1e-4** | 2026-09-12 声明；GPU 推理路径判据 |

判据依据：`R6_recalc/compare_linux_vs_ref.py`（`CRITERION`，与
`recompare_per_metric.py` 一致）：
`psnr/ssim/cnr_mean/cho_auc_mean/npwe_mean` 相对 1e-4；`n` 精确相等。
声明日期 2026-09-12，声明位置《R6独立复算操作指南.md》§4 修订记录 +
Director decision 2026-09-11 §2.1 route (b)。

### 6.2 比对命令（第三环境 vs 参考 onboard）

```bash
# 把第三环境结果放到 R6_recalc/results/third_env_run/ 后，在仓库内执行：
cd <repo>/WS-1_dataset/R6_recalc
python3 compare_linux_vs_ref.py            # 默认读 results/linux_rerun
# 若复用该比对器比对第三环境结果，可用 R6_ONBOARD_RESULTS 指定参考目录，
# 并把第三环境 JSON 放置到被比对目录（或按比对器约定调整 REC 路径）后执行：
python3 compare_linux_vs_ref.py --check    # 重新推导并校验
```

> **说明**：`compare_linux_vs_ref.py` 当前硬编码比对 `results/linux_rerun/`
> 与 `baselines/results/`。第三环境比对可复用同一判据逻辑（逐 seed × dose ×
> metric，相对 1e-4）；操作者按 `THIRD_PARTY_OPERATOR_GUIDE.md` §4 回传后，
> 由 owner 侧统一生成 `comparison_third_env_full764.json` 并附两侧 SHA256。

### 6.3 验收口径（3 项手稿声明）

第三环境运行包**不要求复算频域/统计检验**（那是 R6 步骤 5/6）；本运行包的
验收仅针对 **fidelity + detectability 全量复算**与手稿基线表
（`tab:baselines_v05` / `tab:detectability_v05`）对齐：

| # | 验收项 | 口径 |
|---|---|---|
| 1 | 5 个 `*_det_full764.json` 齐全 | 每文件 `per_seed` 含 5 seeds × 3 dose，`detectability.n_slices=764`，`det-trials=64` |
| 2 | 与参考 onboard 一致 | 逐 seed × dose × metric 相对差 ≤ 1e-4（per-metric declaration）；`n` 精确相等 |
| 3 | 环境/数据/权重可追溯 | 数据哈希（§2.2 ok=364）、task_spec SHA256、5 权重 SHA256、分支 commit 全部记录在回传清单 |

**判定表述**：第三环境复算 PASS 指「在 per-metric 相对 1e-4 判据下与参考一致；
shipped 绝对 1e-6 判据保留为 FAIL（跨环境系统性 float 偏移，R6 报告 §10.3 已
实证），不构成真实不一致」。

---

## 7. 安全与合规提示

- 权重与数据为受控资产，**发送第三方前需 owner 授权**（见
  `checkpoint_provenance_license.md` §0）；操作者不得二次分发。
- LIDC-IDRI 原始数据下载与许可（TCIA CC BY 3.0 与项目自身 CC BY 4.0 两层许可）
  见 `data_manifest_LIDC_AAPM.md`。
- 本手册命令均为只读复算（生成新 JSON），不触碰 `baselines/results/` 参考目录
  （仅只读读取）。

---

*附：本手册对应的哈希锚点（2026-09-25 交付时记录）*

| 项 | SHA256 / 值 |
|---|---|
| task_spec.json | `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C` |
| red_cnn.pt / learn.pt / ctformer.pt / corediff.pt / ctformer_small_retrain.pt | `DF775D08… / 3EABF525… / AEAD0C15… / 41ABA674… / 78C0C59C…`（完整值见 `ckpt_hashes.txt`） |
| LIDC sim 树 | 364 项（`data_hashes.txt`） |
| AAPM 树 | 25 项（`aapm_hashes.txt`） |
| 源码基线 | 分支 `third-env/blackwell`（基于 heyang `9ce3388` + 任务5 环境提交，hash 见交付报告） |
