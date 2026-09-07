# pwm_ldct_loader

Unified Python loader for **PWM-LDCT v0.5** — a content-addressed harmonization of three public
low-dose CT datasets (LIDC-IDRI, AAPM 2016, Mayo LDCT-and-Projection-Data) under one schema.
**v0.5 release scope: LIDC-IDRI only (1,010 patients); AAPM 2016 + Mayo LDCT-PD are v1.0 roadmap
additions** — the loader and schema already model all three sources, but the v0.5 deposited tree
contains only LIDC-derived data.

It implements the loader contract (§4) and the conformance check (§8) defined in the
specification at [`../schema/dataset_schema.md`](../schema/dataset_schema.md) (schema `0.5.0`).

> **Status:** scaffold. The class/function signatures, schema constants, split logic,
> metadata/annotation handling, and `validate()` are implemented and tested against a synthetic
> conformant fixture. Building the harmonized HDF5 from raw source DICOM is performed by the
> preprocessing Dockerfiles ([`../pipelines/`](../pipelines/)); the loader reads their output.

## Install

```bash
pip install pwm_ldct_loader            # core (numpy + h5py)
pip install pwm_ldct_loader[torch]     # add the torch backend
```

## Quickstart

```python
from pwm_ldct_loader import LowDoseCTDataset, validate, seed_everything

seed_everything(42)

# point at the harmonized tree (output of the preprocessing pipelines) ...
train = LowDoseCTDataset(root="/path/to/pwm_ldct_v0_5", split="train", seed=42)

# ... or at per-source roots (manuscript Usage Notes signature)
train = LowDoseCTDataset(
    root_lidc="/path/to/lidc_harmonized",
    root_aapm="/path/to/aapm_harmonized",
    root_mayo="/path/to/mayo_harmonized",
    split="train", seed=42,
)

sample = train[0]
sample["full_dose"]    # [H, W] float32, HU
sample["low_dose"]     # [H, W] real where available else simulated
sample["low_dose_kind"]# "real" | "sim"
sample["sinogram"]     # [V, D] or None (lidc)
sample["source"]       # "lidc" | "aapm" | "mayo"
sample["annotations"]  # {"nodules": [...], "likert": {...}}
sample["metadata"]     # parsed metadata.json

# conformance check (dataset_schema.md §8)
report = validate("/path/to/pwm_ldct_v0_5")
assert report.ok, report.errors
```

### Key arguments (see `dataset_schema.md` §4.1)

`split`, `seed`, `dose_ratio` (0.10/0.25/0.50 for simulated), `prefer_real_ld`,
`resample_spacing` (mm; default keeps native), `slice_thickness` (`"thin"` ≤ 1.5 mm, or a float),
`sources` (subset, e.g. `["aapm","mayo"]` for real-paired-only), `return_sinogram`,
`backend` (`"numpy"` default-without-torch, or `"torch"`).

## Develop / test

```bash
pip install -e .[dev,torch]
pytest
```

From the repository root the equivalent editable install is `pip install -e WS-1_dataset/pwm_ldct_loader` — the standard way to install a `src/`-layout package and the prerequisite for the loader test suite (25 passed; without the install the outer directory shadows the package and collection fails with `No module named pwm_ldct_loader.schema`).

The test suite builds a tiny synthetic conformant tree and asserts the schema invariants, the
sample contract, split determinism, annotation consolidation, and `validate()` behavior — no
network or real data required.

## License

Apache-2.0 (code). The dataset records the loader reads carry their own open licenses
(CC BY 4.0 / CC BY 3.0 / CC0) per the Data Records table in the manuscript.
