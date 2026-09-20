---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_023b4986b3bf11f1b3c552540024e231
    ReservedCode1: mRfuu2nazBwr+TerLrcM3DloE3I7fU9lo9n/jOyD2mXySiTFahK8Wjw6B34Eqi95qDCvF5He2D9lBb5YdIw8FpQ3sAIi8DMZlET1jwDHW27/y1xAW0sc/vXcNucDrKCiXrp0YmvG2UjxhkOy94EP3ULGv56azAOWy9RoWmj95gnL/k4VXiSbPFkXJF8=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_023b4986b3bf11f1b3c552540024e231
    ReservedCode2: mRfuu2nazBwr+TerLrcM3DloE3I7fU9lo9n/jOyD2mXySiTFahK8Wjw6B34Eqi95qDCvF5He2D9lBb5YdIw8FpQ3sAIi8DMZlET1jwDHW27/y1xAW0sc/vXcNucDrKCiXrp0YmvG2UjxhkOy94EP3ULGv56azAOWy9RoWmj95gnL/k4VXiSbPFkXJF8=
---

# WS-1 Development Setup

> Target of HEYANG item 2.7: document the `pwm_ldct_loader` install/use steps in a
> dev-setup note. Commands below are taken from the real package metadata
> (`pwm_ldct_loader/pyproject.toml`, v0.5.0) and the loader README; nothing is invented.

## Prerequisites

- Python >= 3.9 (per `pyproject.toml` `requires-python`)
- git clone of the repository (this workspace)

## 1. Install the unified loader `pwm_ldct_loader`

The package lives in `WS-1_dataset/pwm_ldct_loader/` (src layout:
`src/pwm_ldct_loader/`). Two install modes are supported.

**A. Local (editable) install for development — recommended inside this repo:**

```bash
pip install -e ./WS-1_dataset/pwm_ldct_loader
```

or, from the package directory:

```bash
cd WS-1_dataset/pwm_ldct_loader
pip install -e .
```

Core dependencies (from `pyproject.toml`): `numpy>=1.21`, `h5py>=3.6`.

**B. Published release install (as documented in the loader README):**

```bash
pip install pwm_ldct_loader            # core (numpy + h5py)
pip install pwm_ldct_loader[torch]     # add the torch backend (torch>=1.12)
```

## 2. Install preprocessing-pipeline dependencies (optional, for regenerating HDF5)

```bash
pip install -r WS-1_dataset/pipelines/requirements.txt
```

`requirements.txt` pins: `pydicom>=2.3`, `numpy>=1.21`, `h5py>=3.6`,
`scikit-image>=0.19` (fast Cython radon/iradon for projection-domain low-dose
simulation), `pytesseract>=0.3` (Stage-2 burned-in-text OCR sweep; requires the
tesseract-ocr binary installed on the OS).

## 3. Optional dev/test extras

```bash
pip install -e "WS-1_dataset/pwm_ldct_loader[dev]"   # pytest>=7
```

## 4. Run the loader test suite

From the package directory (or with `PYTHONPATH` pointing at `src`):

```bash
cd WS-1_dataset/pwm_ldct_loader
python -m pytest        # testpaths=["tests"] per pyproject.toml
```

## 5. Basic usage

See `WS-1_dataset/pwm_ldct_loader/README.md` (Quickstart). Summary of the
source-prefixed root signature (manuscript Usage Notes):

```python
from pwm_ldct_loader import LowDoseCTDataset, validate, seed_everything

seed_everything(42)
train = LowDoseCTDataset(
    root_lidc="/path/to/lidc_harmonized",
    root_aapm="/path/to/aapm_harmonized",
    root_mayo="/path/to/mayo_harmonized",
    split="train", seed=42,
)
sample = train[0]
# sample["full_dose"], sample["low_dose"], sample["low_dose_kind"],
# sample["sinogram"], sample["source"], sample["annotations"], sample["metadata"]

report = validate("/path/to/pwm_ldct_v0_5")   # dataset_schema.md §8 conformance check
assert report.ok, report.errors
```

## Notes

- v0.5 release scope is LIDC-IDRI only (1,010 patients); AAPM 2016 + Mayo LDCT-PD
  are v1.0 roadmap additions (the loader/schema already model all three sources).
- The loader reads HDF5 trees produced by the preprocessing Dockerfiles under
  `WS-1_dataset/pipelines/`; building the harmonized tree from raw source DICOM is
  performed there, not by the loader itself.
*（内容由AI生成，仅供参考）*
