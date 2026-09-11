---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_13a56d6ba5d911f1903b525400f8a581
    ReservedCode1: ZQA0mizU9MeuAeUQUPKyuVOxI2ZfY1jK4SqSL0EVcZWBQ8wIlm+pN/ZNsY6Wof0QI+5J5lwDQwETzsxeWz1r3cpcweOYNezJJUTsaZBxQD9dhsZyZGBqjoiQ8JZI00kamqv09O8qauA2jctQUlxdyrrH7xrYpKEOwhxCY3T++bw3031wvegjeDxoAIM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_13a56d6ba5d911f1903b525400f8a581
    ReservedCode2: ZQA0mizU9MeuAeUQUPKyuVOxI2ZfY1jK4SqSL0EVcZWBQ8wIlm+pN/ZNsY6Wof0QI+5J5lwDQwETzsxeWz1r3cpcweOYNezJJUTsaZBxQD9dhsZyZGBqjoiQ8JZI00kamqv09O8qauA2jctQUlxdyrrH7xrYpKEOwhxCY3T++bw3031wvegjeDxoAIM=
---

# R6 独立复算 · 作者随附资产清单（ASSET MANIFEST）

> 对应《R6独立复算操作指南.md》§0.1。本清单与指南一同交付给独立复算者；
> 交付前请逐项核对并填写 SHA256，缺一不可，否则陌生复算者无法完成复算。

交付日期：2026-09-01
交付状态：☑ 已完成（SHA256 已逐项填写；数据树/AAPM 树按哈希清单校验）

---

## A1 模型权重（5 个检查点）

| 文件 | 大小 | 来源路径 | SHA256 |
|---|---|---|---|
| `red_cnn.pt` | 7.4 MB | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\checkpoints\red_cnn.pt` | `DF775D088AB1E720D72A530033F9460A7CF6FDDF636ABE9757312A441A04976E` |
| `learn.pt` | 774 KB | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\checkpoints\learn.pt` | `3EABF5254C4F6F96706872DBB26EA8E89707A74F9FBAA6F19208115730B68EA0` |
| `ctformer.pt` | 350 MB | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\checkpoints\ctformer.pt` | `AEAD0C15D859E25DAC5AFFD51FF4EEDC108060E08165E739669ED40B106107B2` |
| `corediff.pt` | 19 MB | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\checkpoints\corediff.pt` | `41ABA6748778BECD3E10595014BE36CAA84C4B238EE787380444E59418DFA7AD` |
| `ctformer_small_retrain.pt` | 9.7 MB | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\baselines\checkpoints\ctformer_small_retrain.pt` | `78C0C59C91920074FBFB16F0E939B21C784811F11867B0E4E37C59864CFCCF2B` |

说明：`blur` 为内置 trap（`get_model("blur")`），**无需权重**。
CTformer 复算使用 `ctformer_small_retrain.pt`（模型字段 `ctformer_small`，on-board 实际协议）；`ctformer.pt` 为早期大模型存档，不作为本复算对照。
`.gitignore` 忽略 `*.pt`，git clone 后仓库内无权重，必须随资产交付。
指引：《指南》§2「数据与检查点锁定」、§4「全量复算」。

## A2 pwm_ldct_loader 依赖包

| 项 | 值 |
|---|---|
| 类型 | Python 包（源码树） |
| 来源路径 | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pwm_ldct_loader` |
| 安装方式 | `pip install -e <路径>` 或提供 wheel |
| 用途 | 低剂量模拟 `lowdose_sim`（A3 频域脚本依赖） |
| SHA256（源码树组合哈希） | `87BA7C4F5B0F4AA883DB0A93C48AF59D76EF0C3AF6962AA95F44E9327B9EEB84` |
| 哈希口径 | `analysis/common.py::inputs_fingerprint` — 对 17 个源文件（排除 `__pycache__`/`*.pyc`）各自 SHA256 排序后再取 SHA256。压缩包哈希不可复现（依赖 tar/zip 参数），故改用与本仓库 `analysis/` 溯源一致的组合哈希口径。复算者可运行下方命令自行核验。 |
| 核验命令 | `python3 -c "import sys,glob,os;sys.path.insert(0,'analysis');from common import inputs_fingerprint;print(inputs_fingerprint([p for p in glob.glob('pwm_ldct_loader/**/*',recursive=True) if os.path.isfile(p) and '__pycache__' not in p and not p.endswith('.pyc')]))"` |

说明：baselines README 注明 "needs pwm_ldct_loader on the path"，该包不在 baselines 仓库内。
指引：《指南》§1 步骤 3。

## A3 频域检测性复算脚本（已随附）

| 项 | 值 |
|---|---|
| 文件 | `freq_detectability_recalc.py` |
| 随附位置 | 与本清单同目录 |
| 实现协议 | `detectability-freq-v1`（band_energy_ratio + tm_auc，含 2026-08-22 自适应 eps 正则化） |
| 运行要求 | Python 3.10+；`numpy scipy torch pydicom`；A2 包；baselines 包（`pwm_ldct_baselines`） |
| 输入 | 全剂量/低剂量归一化 npy 配对目录（每患者一文件，shape `[S,H,W]`） |
| 产出 | `freq_band_energy_<set>.json`（per_patient + summary_mean） |
| 验证 | 作者自测：与 `output/aapm_lidc_cross_vendor_spread.json` 中 `freq_roi` 字段同源实现 |

用法：
```bash
python freq_detectability_recalc.py \
    --fd-dir r6_recalc/data/aapm_test_fd \
    --ld-dir r6_recalc/data/aapm_test_ld \
    --suffix-ld _r025 \
    --model red_cnn --checkpoint r6_recalc/checkpoints/red_cnn.pt \
    --task-json r6_baselines/task_spec.json \
    --device cuda \
    --out r6_recalc/freq_band_energy_aapm_test.json
```
指引：《指南》§5「频域检测性复算」。

## A4 统计检验复算脚本（已随附）

| 项 | 值 |
|---|---|
| 文件 | `statistical_tests_recalc.py` |
| 随附位置 | 与本清单同目录 |
| 子命令 | `vendor-kw`（patient-level permutation KW，默认 20000 draws, seed 42）；`dose-friedman`（exact-permutation Friedman，1296 枚举） |
| 运行要求 | Python 3.10+；`numpy scipy` |
| 输入 | vendor-kw：`aapm_lidc_cross_vendor_spread.json` 结构（`per_vendor.*.patients[].models.*.freq_roi`）；dose-friedman：`aapm_dose_detectability.json` 结构（`per_patient.*.doses.*.models.*.freq`） |
| 产出 | `vendor_perm_kw.json` / `dose_exact_friedman.json` |
| 验证 | 作者自测：dose-friedman 复现 red_cnn/learn/blur p=0.0417、ctformer p=0.1250（与 `output/aapm_per_dose_spread.json` statistics.per_dose 一致） |

用法：
```bash
python statistical_tests_recalc.py vendor-kw \
    --input r6_recalc/aapm_lidc_cross_vendor_spread.json \
    --vendors GE,Philips,Siemens,Toshiba,AAPM-Siemens-real \
    --n-perm 20000 --seed 42 \
    --out r6_recalc/vendor_perm_kw.json

python statistical_tests_recalc.py dose-friedman \
    --input r6_recalc/aapm_dose_detectability.json \
    --out r6_recalc/dose_exact_friedman.json
```
指引：《指南》§6「统计检验复算」。

## A5 AAPM 真实配对 held-out test 数据 + split

| 项 | 值 |
|---|---|
| 数据树 | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pipelines\_runtime\aapm_tree_v1\hdf5\test\aapm\aapm-xxxx`（test 应为 4 患者：aapm-0003 / aapm-0005 / aapm-0006 / aapm-0009） |
| split 文件 | `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\splits\aapm_train.txt`、`aapm_val.txt`、`aapm_test.txt` |
| 用途 | 频域协议的真实解剖判别（与 LIDC 模拟组分别报告，绝不平均） |
| SHA256（数据树压缩包） | 不提供整树压缩包单哈希；按文件哈希清单校验：作者侧已生成 `aapm_hashes.txt`（**25 项**）→ `hashes\aapm_hashes.txt`（与本清单同目录下 `hashes\` 子目录）。校验方式：`Get-FileHash -Algorithm SHA256` 对每文件逐项比对，全部一致即通过 |

指引：《指南》§2「AAPM 真实配对数据」、§5。

---

## 交叉引用速查

| 指南章节 | 所需资产 |
|---|---|
| §1 环境搭建 | A2 |
| §2 数据与检查点锁定 | A1、A5 |
| §4 全量复算（5 模型 × 5 seeds × 3 dose） | A1（blur 除外） |
| §5 频域检测性复算 | A3、A5、A2 |
| §6 统计检验复算 | A4 |
