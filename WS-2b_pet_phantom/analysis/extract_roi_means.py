"""Extract NEMA sphere/background ROI means from reconstructed PWM-PET-IQ volumes.

This is the ONE genuinely data-dependent step: it turns reconstructed volumes into the
``roi_means.json`` that ``analyze_phantom.py`` consumes. It cannot be completed until the
phantom scans exist, but the contract and the exact remaining work are pinned here so the
gap is explicit rather than hidden inside a table.

Given the reconstructed volume for each series and the phantom geometry, NEMA NU 2-2018
prescribes:
  * one spherical VOI per hot/cold sphere, diameter = the sphere's physical inner diameter,
    centred on the sphere;
  * 12 background ROIs of each sphere size drawn on the central slice, repeated on
    +/-1 cm and +/-2 cm slices (60 background ROIs per sphere size);
  * ROI means read against the known fill concentrations in ``ground_truth.json``.

The unimplemented piece is purely the **spatial localization** (finding sphere centres in
the volume): the arithmetic on the resulting ROI means is already implemented and tested in
``nema_metrics.py`` / ``analyze_phantom.py``.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List


def load_ground_truth(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def place_rois(volume, sphere_geometry: Dict[str, Any]) -> Dict[str, Any]:
    """Return {'c_hot': mean, 'bg_roi_means': [...]} for one sphere on one volume.

    TODO(acquisition): implement NEMA VOI placement once recon volumes exist. Requires:
      1. locate the phantom in `volume` (fiducial / template registration to the known
         NEMA NU-2 geometry, or the acquisition's recorded couch/phantom offset);
      2. place the spherical VOI at each sphere centre (radius = sphere_geometry['diameter_mm']/2);
      3. place the 12x5 background ROIs per NEMA and read their means.
    Until then this raises so no ROI mean is ever silently fabricated.
    """
    raise NotImplementedError(
        "NEMA VOI/background-ROI placement is acquisition-gated; see module docstring. "
        "The metric math over the resulting means is complete in nema_metrics.py."
    )


def build_roi_means(recon_root: str, ground_truth_path: str) -> Dict[str, Any]:
    gt = load_ground_truth(ground_truth_path)
    doc: Dict[str, Any] = {"true_activity_ratio": gt.get("true_activity_ratio"), "levels": {}}
    # Enumerate reconstructed series/levels from disk here, then per level call place_rois
    # for each sphere. Left to wire up with the real recon layout at acquisition time.
    _ = recon_root
    raise NotImplementedError(
        "wire recon-volume enumeration + place_rois once volumes exist; emits roi_means.json "
        "matching analyze_phantom.py's contract."
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recon-root", required=True, help="dir of reconstructed volumes per level")
    ap.add_argument("--ground-truth", required=True)
    ap.add_argument("--out", default="roi_means.json")
    args = ap.parse_args()
    doc = build_roi_means(args.recon_root, args.ground_truth)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)


if __name__ == "__main__":
    main()
