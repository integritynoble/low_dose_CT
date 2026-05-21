# fastMRI knee — NYU registration recipe

fastMRI is a large public MRI raw-data dataset released by NYU Langone (knee + brain). For WS-2's MRI validator we need the **knee** subset.

**Citation:** Zbontar J, Knoll F, Sriram A, et al. fastMRI: A Publicly Available Raw k-Space and DICOM Dataset of Knee Images for Accelerated MR Image Reconstruction Using Machine Learning. Radiology: Artificial Intelligence 2(1):e190007, 2020.

## Step 1: Register

1. Visit https://fastmri.med.nyu.edu/
2. Click "Apply for Access".
3. Fill in the registration form:
   - **Full name**
   - **Email** (academic / institutional preferred; PWM Foundation email is acceptable)
   - **Affiliation**: UTSW / PWM Protocol Foundation
   - **Title**: as per current institutional role
   - **Country**: USA
   - **Intended research use** (suggested text):

     ```
     Validation of a modality-general signal-equivalence framework for
     reduced-signal medical imaging (target: Nature Methods 2027). The
     framework's MRI validator uses fastMRI knee accelerated reconstruction
     as a worked example of 4x k-space undersampling. We will not
     redistribute the data; we will cite the fastMRI paper in any
     publication that uses the data.
     ```

   - **Will you redistribute the data?** No.
   - **Will the data leave your institution?** No (other than required for
     publication of derived results, e.g., reconstructed image samples
     in a paper figure, which is permitted under the fastMRI license).

4. Submit. NYU's system typically auto-approves within 24 hours for academic
   / research affiliations.

## Step 2: Sign the data-use agreement

After approval, an electronic DUA is emailed. The agreement is straightforward
(non-redistribution, citation requirement, agreement to NYU's terms). Sign
and return.

## Step 3: Download the knee subset

NYU provides a download portal. The relevant subsets for WS-2 MRI v1:

| Subset | Size | Needed? |
|---|---|---|
| Knee singlecoil training | ~85 GB | **Yes** |
| Knee singlecoil validation | ~12 GB | **Yes** |
| Knee multicoil training | ~100 GB | Stretch (better noise modeling) |
| Knee multicoil validation | ~15 GB | Stretch |
| Knee test | ~6 GB | Yes |
| Brain (all) | ~600 GB | Not Year-1 scope |

**For WS-2 Year-1 minimum:** singlecoil train + validation + test (~100 GB).

Stage at `D:/fastmri_knee/`.

## Step 4: Verify integrity

NYU provides MD5 checksums. After download:

```bash
cd D:/fastmri_knee/
md5sum -c checksums.md5
# All files should pass.
```

## Step 5: Process via the WS-2 MRI validator

Once the WS-2 MRI validator lands (Phase 3, ~D9+270), see
[`../WS-2_framework/`](../WS-2_framework/) for the validator pipeline.

The validator's contract:
- Input: full-sampled k-space + 4x variable-density Cartesian undersampled k-space
- Reference method ($\mathcal{M}_{\textrm{ref}}$): GRAPPA / SENSE on the fully-sampled k-space
- Method under test: any user-supplied reconstruction method
- Output: 5-tuple signal-equivalence credential at $r = 0.25$ for the canonical
  meniscus-segmentation task.

## License

fastMRI is released under a NYU-specific data-use agreement. Key terms:
- Free for academic / research use
- No redistribution
- Citation required
- Commercial use prohibited without separate agreement
- Reconstructions / derived results may be published

## Common gotchas

- **The download portal has session timeouts.** A 100-GB download takes
  many hours; use `wget --continue` or the official downloader to avoid
  losing progress.
- **Singlecoil vs multicoil.** Singlecoil is simpler and sufficient for
  WS-2 Year-1; multicoil enables more realistic coil-sensitivity modeling
  but is not needed until Year-2 if at all.
- **Variable-density vs equispaced masks.** The fastMRI default is
  equispaced + central-k-fully-sampled; for WS-2 we use the
  variable-density mask per the framework's open-questions §7 decision
  (see [`../WS-2_framework/theory/open_questions.md`](../WS-2_framework/theory/open_questions.md)).
