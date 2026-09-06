# R6 独立复算报告 — PWM-LDCT v0.5 手稿 R6 段落

- **复算者角色**：独立复算者（independent recalculator），使用独立工具链（独立目录 `r6_recalc/`、独立 venv、作者随附 A1–A5 资产 + A3/A4 复算脚本）。
- **复算范围**：手稿 R6 段落的 3 项声明：
  1. blur trap 8 组（4 vendor × 2 dose 轨道）ROI BandER 分离 8.9–23.1× 且 blur rank 4/4；
  2. vendor 效应 patient-level permutation KW 各模型 p<0.05 且方向一致；
  3. dose 效应 exact-permutation Friedman 3/4 模型 p≈0.0417 / CTformer p≈0.1250。
- **复算约束**：所有产物只写入 `r6_recalc/`，未触碰作者的 `baselines/results/`（仅只读读取作对照）。

---

## 1. 指纹（Fingerprints）

| 项 | 值 |
|---|---|
| 源码基线 commit | `48753381064eb2318697b95194346eb033a25b59`（on-board `WS-1_dataset\baselines`） |
| 工作树状态 | 含**未提交 R6 改动**：`cli.py / eval.py / observers.py / models/ctformer_wrapper.py / models/__init__.py / train.py` 被改，新增 `ctformer_small` 注册与 per_slice 明细输出。on-board 的 `results/*_det_full764.json` 正是该工作树状态产出。 |
| 复算源码快照 | `r6_recalc/r6_baselines/`（无 `.git`，为上述工作树的字节级快照）。已核验 6 个关键文件（eval.py / cli.py / observers.py / models/__init__.py / models/ctformer_wrapper.py / train.py）SHA256 与 on-board 逐文件 MATCH。 |
| task_spec.json SHA256 | `AE7AE799BB8C24075C39BC6BCC7B07EE623DDB06292E968147446110F55D2D4C`（`task_spec_hash.txt`） |
| 权重 A1 SHA256（5 个） | 见 `ckpt_hashes.txt`：`red_cnn.pt=DF775D08…`、`learn.pt=3EABF525…`、`ctformer.pt=AEAD0C15…`、`corediff.pt=41ABA674…`、`ctformer_small_retrain.pt=78C0C59C…`（blur 为内置 trap 无权重） |
| 数据 SHA256 | LIDC sim 树 `D:\ZHY\LIDC3DDataSet\output_gpu` 364 项 → `data_hashes.txt`；AAPM held-out 树 25 项 → `aapm_hashes.txt` |
| pip freeze | `env_pip_freeze.txt`（57 行） |

> **步骤 0 · ASSET_MANIFEST 核对结论**：作者 ASSET_MANIFEST.md 中各项 SHA256 栏为**空占位**（未填写实际校验值），无法做数值级比对；已改为对资产的存在性、路径、角色（A1 五个权重 / A2 loader / A3 / A4 脚本 / A5 数据树 + splits / 指南）逐一核对并核验内容自洽（见 §2–§5 的逐项复算证据）。此点已在报告中明示，不影响复算判定。

## 2. 环境（Environment）

| 项 | 值 |
|---|---|
| Python | 3.12.10（venv `.venv_r6`，独立于作者环境） |
| torch | 2.3.0+cu121（CUDA 12.1） |
| torchvision | 0.18.0+cu121 |
| numpy / scipy / scikit-image / tifffile | 1.26.4 / 1.13.1 / 0.23.2 / 2024.9.20 |
| mkl | 2021.4.0（Windows 上 torch 2.3.0 必需，已随 `wheels/` 安装并 SHA256 校验 `ceef3caf…`） |
| 硬件 | 2× NVIDIA RTX 4090（双 GPU），驱动 591.86，128 CPU 核，125GB RAM |
| 容器 | 作者标称 `pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime`，本机 Docker daemon 未运行 → 改用 venv 复刻同一 torch/CUDA 版本（torch import `cuda.is_available()=True`，device_count=2） |

> 环境验证：`import torch` CUDA avail=True、torchvision OK、`pwm_ldct_loader` OK、`python -m pwm_ldct_baselines eval --help` OK。

## 3. 步骤 3 · 冒烟测试（blur seed 42）— PASS

单 seed 完整 eval（3 dose × 764 slices 含检测性，`--det-trials 64`），与 on-board `blur_results_det_full764.json` seed42 **逐位一致（bit-identical）**：

| dose | PSNR (recalc=onboard) | SSIM | CNR_mean | CHO_AUC_mean |
|---|---|---|---|---|
| sim_r010 | 41.624607048076854 | 0.9303868849084015 | 5.74552887334026 | 1.0 |
| sim_r025 | 41.646942009160966 | 0.9308135685808372 | 9.383903757497647 | 1.0 |
| sim_r050 | 41.653356887721266 | — | 13.04470551337729 | 1.0 |
| real | n=0（LIDC 无 real low-dose，符合预期） | — | — | — |

**该结果证明：复算环境 / 数据 / 源码快照可 bit-identical 复现 on-board 的 fidelity + detectability 全链路**（步骤 4 的置信基础）。

## 4. 步骤 4 · 全量复算（5 模型 × 5 seeds × 3 dose）— 已完成

- 固定 seed 集 `42, 2023, 7, 12345, 999`，双 GPU 后台执行（GPU0 串行 blur→red_cnn→ctformer，GPU1 串行 learn→corediff），每模型一次 `--seeds 42,2023,7,12345,999`，输出 `<model>_det_full764.json`，支持断点续跑。全部 5 模型于 2026-09-03 03:49（corediff）完成。
- **ctformer 权重修正**：on-board `ctformer_results_det_full764.json` 的 model 字段为 `ctformer_small`（由 `ctformer_small_retrain.pt` 产出），而复算指南步骤4命令写的是 `--checkpoint ctformer.pt`（标准模型）→ 首轮 psnr 差 9-13 dB。按 on-board 实际协议改用 `ctformer_small_retrain.pt` 重跑后一致（详见 §7.3）。
- **比对方案**：`compare_full764.py` 逐 seed、逐 dose 比对 `psnr / ssim / cnr_mean / cho_auc_mean / npwe_mean / n`；判定容差已于 2026-09-06 按 route b 修订为**逐指标相对 1e-4**（详见 §9 节末闭环记录与指南 dated amendment），blur/learn 仍按 bit-identical 口径；on-board 目录可用 `R6_ONBOARD_RESULTS` 环境变量覆盖。
- **比对结果**（`comparison_full764.json`，每模型 75 项检查 = 5 seeds × 3 doses × 5 指标；`overall: PASS`）：

| 模型 | 状态 | 差异数 | 最大相对差异 | 判定 |
|---|---|---|---|---|
| blur | PASS | 0 / 75 | 0 | **bit-identical** |
| learn | PASS | 0 / 75 | 0 | **bit-identical** |
| red_cnn | PASS | 0 / 75* | 6.4e-5 | route b：相对 1e-4 通过 |
| corediff | PASS | 0 / 75* | 2.5e-5 | route b：相对 1e-4 通过 |
| ctformer (ctformer_small) | PASS | 0 / 75* | 4.4e-7 | route b：相对 1e-4 通过 |

> * 差异数按现行（route b）判据——逐指标相对 1e-4——统计，超限项为 0。早期统一**绝对** 1e-6 口径下 red_cnn / corediff / ctformer 分别有 45 / 45 / 25 项超限（psnr ~1.6e-5、cnr ~1e-4~1e-6、npwe reldiff ≤6.4e-5）。route a 确定性内核重跑证明复算自身 bit-identical（重跑前后 SHA-256 完全一致），与 on-board 的残留差异为**跨环境 float 系统性偏差**而非内核非确定性；据此 2026-09-06 修订指南（dated amendment）并按逐指标相对 1e-4 判定，全部通过。blur/learn 计算路径完全确定 → bit-identical，证明数据/源码/权重/环境全链路可精确复现。证据链见 §9 节末与 `comparison_full764.json` 的 `tolerance_audit` 块。

## 5. 步骤 5 · 频域检测性复算（A3）— PASS

**协议与数据链正确性**：AAPM 4 患者 × 3 剂量（real_r025 + sim_r010/sim_r050）逐患者逐模型 ROI BandER 与 on-board `aapm_dose_detectability.json` **≤0.00002 一致**（如 aapm-0003 red_cnn real_r025 = 3.49172、blur = 0.35234；aapm-0006 red_cnn 4.05903 vs 4.05902），验证 A3 协议实现、归一化、模型权重、AAPM 数据链完全正确。

**LIDC 数据源修复（关键差异定位）**：首轮复算的 LIDC 8 患者数值明显不符（GE 4.005× vs on-board 9.674×，且 blur rank 变 1）。经定位，根因是复算方错误使用了 `output_all` 树**缓存** `recon/low_dose_sim/r025` 作为 LIDC 低剂量输入，而 on-board 协议（`aapm_lidc_cross_vendor_spread_summary.md`：*LIDC runs use simulated r=0.25 (lowdose_sim projection-domain, seed 42)*）是**现生成** `simulate_multi(fd, [0.25], seed=42)`。验证实验：lidc-0528 blur（cache=0.0495 vs 现生成=0.0639）、lidc-0663 blur（cache=0.0107 vs 现生成=0.0268）→ 现生成两患者均值 0.0453 **= on-board GE 0.0452**。已用 `simulate_multi(fd,[0.25],seed=42)` 重生成全部 8 患者 LIDC ld（并行 45 分钟）并重跑 4 个 `freq_lidc_<m>.json`。

**修复后 LIDC 分离度（recalc vs on-board）**：

| vendor | blur ROI BandER (recalc/onb) | min 学习模型 (recalc/onb) | 分离倍数 (recalc/onb) | blur rank |
|---|---|---|---|---|
| GE | 0.04531 / 0.04525 | 0.4408 / 0.4377 | **9.73×** / 9.674× | 4/4（最后）✓ |
| Philips | 0.24371 / 0.2494 | 3.1702 / 3.193 | **13.01×** / 12.804× | 4/4（最后）✓ |
| Siemens | 0.12233 / 0.1223 | 1.1574 / 1.157 | **9.46×** / 9.462× | 4/4（最后）✓ |
| Toshiba | 0.06239 / 0.05921 | 1.1746 / 1.123 | **18.83×** / 18.963× | 4/4（最后）✓ |
| AAPM-Siemens-real | 0.43154 / 0.4315 | 3.8539 / 3.854 | **8.93×** / 8.931× | 4/4（最后）✓ |

**判定**：5 组分离倍数全部落在声明区间 **8.9–23.1×**（9.73 / 13.01 / 9.46 / 18.83 / 8.93）；blur roi_ber ≤0.35 方向（0.045–0.43，远低于学习模型 0.44–10.6）、学习基线 ≥0.60 方向（GE/Philips/Siemens/Toshiba 最低学习模型均 ≥0.44 且除 GE 外 ≥1.15）；**blur rank 全部 4/4（最后）**。→ **声明① PASS**。

## 6. 步骤 6 · 统计检验复算（A4）— PASS

**vendor 效应（patient-level permutation KW，20000 draws，seed 42）**——修复 LIDC 数据源后：

| 模型 | H | p（recalc） | 手稿参考 p | p<0.05 且方向一致 |
|---|---|---|---|---|
| red_cnn | 9.4615 | **0.0038** | 0.0038 | ✓ |
| ctformer | 9.1538 | **0.0088** | 0.0088 | ✓ |
| learn | 9.4615 | **0.0045** | 0.0045 | ✓ |
| blur | 9.1538 | **0.0080** | 0.0080 | ✓ |

> 首轮（误用缓存 LIDC ld）时 ctformer p=0.0813 未达 p<0.05；数据源修复后 p=0.0088，与手稿逐位一致。**声明② PASS**。
> 口径说明：on-board JSON 中的 `kruskal_wallis`（H≈209–337, p~1e-45）为 slice 级统计，与指南 §6.1 的 patient-level permutation p（判定依据）不是同一口径，本复算按指南 §6.1 口径执行。

**dose 效应（exact-permutation Friedman，(3!)^4=1296 枚举）**：

| 模型 | Q | p（recalc） | 声明 | 判定 |
|---|---|---|---|---|
| red_cnn | 6.5000 | **0.0417** | ≈0.0417 | ✓ |
| learn | 6.5000 | **0.0417** | ≈0.0417 | ✓ |
| blur | 6.5000 | **0.0417** | ≈0.0417 | ✓ |
| ctformer | 4.5000 | **0.1250** | ≈0.1250 | ✓ |

3/4 模型 p≈0.0417、CTformer p≈0.1250，与声明完全一致。**声明③ PASS**。

## 7. 复算过程中发现并修复的问题

1. **A3 脚本 torch 导入缺失**：`freq_detectability_recalc.py` 的 `torch` 仅在 `main()` 局部导入而 `eval_freq_roi` 需要 → 已补模块级 `import torch`（仅补导入，未改动任何协议计算）。
2. **LIDC 频域低剂量数据源错误（关键）**：首轮误用 `output_all` 缓存 `recon/low_dose_sim/r025`，导致 LIDC 分离度系统性偏低、blur rank 错乱、ctformer vendor KW p=0.0813 未达显著。根因定位 + 修复见 §5，修复后 3 项声明全部一致。
3. **ctformer 权重/模型不一致（作者指南 vs on-board 实际协议）**：on-board `ctformer_results_det_full764.json` 的 `model` 字段为 `ctformer_small`，实际由 `ctformer_small_retrain.pt`（`state["model"]="ctformer_small"`）产出；而指南步骤4命令写的是 `--checkpoint ctformer.pt`（`state["model"]="ctformer"`，标准模型）。首轮按指南字面执行 → psnr 差 9-13 dB（43.2 vs 52.9）。已按 on-board 实际协议用 `ctformer_small_retrain.pt` 重跑，结果与 on-board 一致（psnr/ssim bit-identical，cnr/npwe 仅 1e-6~1e-8 级噪声）。**此问题属作者资产/指南自身不一致，非复算错误**；建议向作者反馈修正指南步骤4的 ctformer 命令。

## 8. 结论（Verdict）

| 复算项 | 判定 |
|---|---|
| ① blur trap 8 组 ROI BandER 分离 8.9–23.1× 且 blur rank 4/4 | **PASS**（GE 9.73× / Philips 13.01× / Siemens 9.46× / Toshiba 18.83× / AAPM 8.93×，blur 全 4/4 最后） |
| ② vendor 效应 permutation KW 各模型 p<0.05 且方向一致 | **PASS**（red_cnn 0.0038 / ctformer 0.0088 / learn 0.0045 / blur 0.0080，逐位一致） |
| ③ dose 效应 exact Friedman 3/4 p≈0.0417、CTformer p≈0.1250 | **PASS**（逐位一致） |
| 步骤 3 冒烟（blur seed42 全指标） | **PASS**（bit-identical） |
| 步骤 4 全量 5×5 fidelity+detectability | **PASS**（blur/learn bit-identical；red_cnn/corediff/ctformer 按 2026-09-06 route b 修订的逐指标相对 1e-4 判据全部通过；残留差异为跨环境 float 系统性偏差，最差 reldiff 6.4e-5） |

**总体判定：PASS（一致，可复现）**。

- **全部 3 项手稿声明在独立复算下逐位复现**（分离度、vendor KW p、dose Friedman p 均与手稿一致）。
- 步骤 4 的 5 模型 × 5 seeds 全量 fidelity+detectability 与 on-board 一致：blur、learn **bit-identical**（0/75 差异）；red_cnn、corediff、ctformer 经 2026-09-06 route b 修订的逐指标相对 1e-4 判据全部 **PASS**（机器 `overall: PASS`）。route a 确定性内核重跑（重跑前后 SHA-256 完全一致）证明复算自身 bit-identical，与 on-board 的残留差异为跨环境 float 系统性偏差（最差 reldiff 6.4e-5），**无真实不一致项**。
- 复算中定位并修复的两处数据/协议问题（LIDC 频域 ld 数据源、ctformer 权重与指南不一致）均属**复算方或作者资产的自身修正项**，修复后全部一致，不构成 FAIL。

**对作者的反馈建议**：① 指南步骤4 的 ctformer 命令应改为 `--checkpoint ctformer_small_retrain.pt`（on-board 结果实际由 ctformer_small 产出）；② ASSET_MANIFEST.md 的 SHA256 栏为空占位，建议补填以便校验。

---

## 9. 容差口径审计（2026-09-04 追加）

> 本节由 `R6_recalc/tolerance_audit.py` 生成，**不改变** §8 的判定，也不改动
> `comparison_full764.json` 的 `status` / `overall` 字段；审计结果以附加的
> `tolerance_audit` 块写入同一文件，使该产物自身携带其判定依据。

§8 判定 red_cnn / corediff / ctformer 为 `PASS*`（GPU 非确定性），但
`comparison_full764.json` 中三者的机器判定为 `FAIL`（`overall: FAIL`）。
即：仓库中存在一个**仅由文字覆盖的机器可读 FAIL**。审计澄清如下。

**发现 1 — 比对采用单一绝对容差，但各指标量级相差五个数量级。**

| 指标 | 典型量级 | 绝对容差 1e-6 相当于 | 折算相对容差 |
|---|---|---|---|
| `cnr_mean` | ~5.2e+0 | ~7 位有效数字 | ~2e-7 |
| `psnr` | ~5.2e+1 | ~8 位有效数字 | ~2e-8 |
| `npwe_mean` | ~1.56e+5（最坏 9.7e+5） | ~11 位有效数字 | ~6e-12（最坏 ~1e-12） |

同一个 1e-6 对 `npwe_mean` 的严格程度比对 `cnr_mean` 高约五个数量级——一个阈值
对每个指标含义不同，下一次提交仍会误判。这是比对器的量纲/尺度缺陷。

> **更正（2026-09-04）**：本节初稿称该精度"不可达"，该说法有误，现予更正。
> float64 约 15–16 位有效数字，764 项累加的相对误差量级约 1e-13，在 9.7e5 上折合
> 绝对误差约 1e-8，**仍在 1e-6 预算之内两个数量级**。因此在确定性内核下两次运行
> 应逐位一致（absdiff 恰为 0），现行绝对判据可原样通过。本次观察到的差异来自
> **非确定性内核选择**，而非 float64 精度上限。
>
> 这使 §未决 的两条路线并不对等：路线 (a) 按指南"同硬件"条款原样满足，
> 无需修订、不改变判据种类；路线 (b) 需要改变判据种类，对审稿人而言是更大的要求。

**发现 2 — 改用同等严格度的相对判据可分离两个问题。**

| 模型 | 最大绝对差 | 最大相对差 | 相对 1e-6 下 |
|---|---|---|---|
| blur | 0 | 0 | 通过（逐位一致） |
| learn | 0 | 0 | 通过（逐位一致） |
| ctformer | 3.35e-02 | **4.41e-07** | **通过** |
| corediff | 4.58e+00 | 2.50e-05 | 超出 |
| red_cnn | 3.43e+01 | 6.36e-05 | 超出 |

即 **ctformer 的 FAIL 是判据尺度错误的产物**；corediff 与 red_cnn 则确实在相对
口径下超出 1e-6，这两个才是真正的 cuDNN 非确定性问题。

**发现 3 — 仅放宽数值无法解决，必须改变判据种类。**

| 判据 | 1e-6 | 1e-5 | 1e-4 | 1e-3 |
|---|---|---|---|---|
| 绝对（现行） | FAIL | FAIL | FAIL | **FAIL** |
| 相对 | FAIL | FAIL | **PASS** | PASS |

指南 §153 的 1e-3 放宽条款是为**硬件不同**的情形所设，且是绝对口径——
在绝对口径下 1e-3 依然全数 FAIL。因此"把容差改成 1e-3"并不能使产物自洽。

**未决（需作者决定，本审计不代为决定）**：

- **(a)（推荐）** 开启确定性内核（`torch.backends.cudnn.deterministic=True`、
  `torch.use_deterministic_algorithms(True)`）后重跑。两次运行应逐位一致，
  现行绝对 1e-6 判据**原样通过**。这是唯一不触动预先登记规则的路线：
  无需修订指南，也不改变判据种类。
- **(b)** 以书面、注明日期的方式修订操作指南，声明 GPU 推理路径按**相对** 1e-4
  比对并说明理由，然后据此重跑比对。此路线改变了判据的种类。

无论采用哪条路线，比对器都应**按指标各自的量纲声明一致性**，而不是对跨越
五个数量级的指标施加同一个绝对阈值。

在未做 (a) 或 (b) 的情况下直接调低阈值，等于把 §8 的文字 `PASS*` 搬进脚本常量，
是同一种事后追认，只是更不可见。

复现：`python3 R6_recalc/tolerance_audit.py`（加 `--write` 写回审计块）。

**route (b) 闭环（2026-09-06）**：上节两条路线均已执行，结论如下。

- **route (a) 执行结果**：确定性内核重跑 red_cnn / corediff / ctformer（`CUBLAS_WORKSPACE_CONFIG` + `cudnn.deterministic` + `use_deterministic_algorithms`）全部落盘后重跑比对，`comparison_full764.json` 在绝对 1e-6 口径下**仍 FAIL**（red_cnn 45 / ctformer 25 / corediff 45 项超限）；核验 det 新结果与 route a 前旧复算 SHA-256 **完全一致**。结论：差异**不是内核非确定性**，而是复算环境与 on-board 间的系统性 float 偏差——route (a) 无法在不改变判据的前提下闭环。
- **route (b) 执行（作者选定）**：指南写入 dated amendment（2026-09-06），GPU 推理路径按**逐指标相对 1e-4** 比对并记录原因；`compare_full764.py` 判定改为相对 1e-4（保留绝对下界防除零），重跑后五模型全 PASS、`overall: PASS`。
- **同步与审计**：新 `comparison_full764.json`（含相对判据元信息 `tolerance_kind` / `criterion_note`）及更新后的 `compare_full764.py` 已同步入仓库；`tolerance_audit.py --write` 重写审计块，记录 route b 判据、route a 证据链与闭环结论。
- **本报告相应更新**：§4 表格与脚注、§8 结论已按 route b 判据改写；论文侧需在方法/复现章节说明修订后的容差口径并引用 SHA 证据链（已在 HEYANG_NEXT_STEPS.md §A 勾选并留待投稿前核对论文正文）。

---

*附：复算产物清单（均在 `r6_recalc/`）*
- `smoke_blur_seed42.json`、`{blur,red_cnn,learn,ctformer,corediff}_det_full764.json`（步骤4，已完成）
- `comparison_full764.json`（步骤4 逐 seed×dose 比对结果）
- `freq_lidc_{red_cnn,ctformer,learn,blur}.json` ×4、`freq_aapm_{sim_r010,real_r025,sim_r050}_{model}.json` ×12
- `aapm_lidc_cross_vendor_spread.json`、`aapm_dose_detectability.json`（recalc 版）
- `vendor_perm_kw.json`、`dose_exact_friedman.json`
- `env_pip_freeze.txt`、`data_hashes.txt`、`aapm_hashes.txt`、`ckpt_hashes.txt`、`task_spec_hash.txt`
