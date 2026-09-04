"""Dose-detectability curve builder (Rung 4: single-point -> curve declaration).

Reads the per-model `*_results_det.json` files (baselines/results) and produces:

- a dose-detectability curve (dose ratio on x, CNR on y, one line per baseline
  plus the standing Gaussian-blur trap, with the Rose criterion CNR=3.0 drawn
  as a reference line) saved as PNG;
- a statistics JSON with per-model CNR/PSNR per dose, the named knee, and the
  Rose-crossing dose ratio.

Knee naming (declared): the knee is the dose ratio at which CNR first crosses
the Rose criterion of 3.0 (linear interpolation between the adjacent simulated
points); for methods that never reach it, the knee is reported as "not_reached"
and the largest-CNR-gain interval is given as the closest approach. This turns
the three simulated points (0.10/0.25/0.50) into a curve statement instead of
single-point claims (low-dose-ct.md Rung 4 / "the next action").
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Tuple

ROSE_CRITERION = 3.0
DOSE_ORDER = ("sim_r010", "sim_r025", "sim_r050")
DOSE_RATIOS = (0.10, 0.25, 0.50)
TRAP_MODEL = "blur"  # the permanent Gaussian-blur control


def _load_model_results(results_dir: str) -> Dict[str, dict]:
    """Load all *_results_det.json into {model_name: parsed}."""
    out: Dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "*_results_det.json"))):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        out[data.get("model", os.path.basename(path))] = data
    return out


def _cnr_series(data: dict) -> Tuple[List[float], List[Optional[float]]]:
    """Return (dose ratios, cnr mean per dose)."""
    ratios: List[float] = []
    cnrs: List[Optional[float]] = []
    for key in DOSE_ORDER:
        det = data.get("per_dose", {}).get(key, {}).get("detectability")
        ratios.append(DOSE_RATIOS[DOSE_ORDER.index(key)])
        cnrs.append(det.get("cnr_mean") if det else None)
    return ratios, cnrs


def rose_crossing_ratio(ratios: List[float], cnrs: List[Optional[float]],
                        rose: float = ROSE_CRITERION) -> Optional[float]:
    """Dose ratio at which CNR first crosses ``rose`` (linear interpolation).

    Returns None when CNR never reaches the criterion within the sampled range.
    """
    valid = [(r, c) for r, c in zip(ratios, cnrs) if c is not None]
    if not valid:
        return None
    for i in range(1, len(valid)):
        r_prev, c_prev = valid[i - 1]
        r_cur, c_cur = valid[i]
        if c_cur >= rose >= c_prev:
            # linear interpolation between the two adjacent simulated points
            frac = (rose - c_prev) / (c_cur - c_prev) if c_cur != c_prev else 0.0
            return float(r_prev + frac * (r_cur - r_prev))
    last_c = valid[-1][1]
    return None if last_c < rose else float(valid[-1][0])


def max_gain_interval(ratios: List[float], cnrs: List[Optional[float]]) -> Optional[Tuple[float, float, float]]:
    """The adjacent dose interval with the largest CNR gain.

    Returns (midpoint_ratio, gain, interval) or None when fewer than 2 valid points.
    """
    valid = [(r, c) for r, c in zip(ratios, cnrs) if c is not None]
    if len(valid) < 2:
        return None
    best = None
    best_gain = -float("inf")
    for i in range(1, len(valid)):
        gain = valid[i][1] - valid[i - 1][1]
        if gain > best_gain:
            best_gain = gain
            best = ((valid[i - 1][0] + valid[i][0]) / 2.0, gain,
                    (valid[i - 1][0], valid[i][0]))
    return best


def build_stats(results_dir: str, rose: float = ROSE_CRITERION) -> dict:
    """Aggregate per-model dose-detectability stats + knee naming."""
    models = _load_model_results(results_dir)
    per_model = {}
    for name in sorted(models):
        data = models[name]
        ratios, cnrs = _cnr_series(data)
        psnrs = [data.get("per_dose", {}).get(k, {}).get("psnr") for k in DOSE_ORDER]
        crossing = rose_crossing_ratio(ratios, cnrs, rose)
        mg = max_gain_interval(ratios, cnrs)
        per_model[name] = {
            "dose_ratios": ratios,
            "cnr_mean": cnrs,
            "psnr": psnrs,
            "rose_crossing_ratio": crossing,
            "knee": {
                "label": (f"rose-crossing@{crossing:.3f}" if crossing is not None else "not_reached"),
                "rose_crossing_ratio": crossing,
                "max_gain_interval_midpoint": (mg[0] if mg else None),
                "max_gain": (mg[1] if mg else None),
                "max_gain_interval": (list(mg[2]) if mg else None),
                "method": ("linear interpolation between adjacent simulated points"
                           if crossing is not None else "closest approach (max CNR gain interval)"),
            },
        }
    return {
        "rose_criterion": rose,
        "dose_ratios": list(DOSE_RATIOS),
        "task": models[list(models)[0]].get("task") if models else None,
        "n_models": len(per_model),
        "per_model": per_model,
    }


def plot_curve(stats: dict, out_png: str) -> str:
    """Render the dose-detectability curve PNG (dose ratio x, CNR y)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    rose = stats["rose_criterion"]

    markers = {"red_cnn": "o", "learn": "s", "ctformer": "^", "corediff": "D", "blur": "x"}
    for name, sm in stats["per_model"].items():
        ratios = sm["dose_ratios"]
        cnrs = sm["cnr_mean"]
        is_trap = name == TRAP_MODEL
        ax.plot(ratios, cnrs,
                marker=markers.get(name, "o"),
                linewidth=2.2 if not is_trap else 2.8,
                linestyle="--" if is_trap else "-",
                color="#c0392b" if is_trap else None,
                label=f"{name} (trap)" if is_trap else name)
        knee = sm["knee"]["rose_crossing_ratio"]
        if knee is not None:
            ax.axvline(knee, color="gray", linewidth=1.0, alpha=0.55, linestyle=":")
            ax.annotate(f"knee {knee:.2f}",
                        xy=(knee, rose), xytext=(knee + 0.005, rose + 0.45),
                        fontsize=8, color="dimgray",
                        arrowprops=dict(arrowstyle="->", color="dimgray", lw=0.8))
        else:
            ax.annotate(f"{name}: knee not reached",
                        xy=(ratios[-1], cnrs[-1]), xytext=(0.30, cnrs[-1] + 0.18),
                        fontsize=8, color="gray")

    # Rose criterion reference line
    ax.axhline(rose, color="black", linewidth=1.4, linestyle="-.", alpha=0.85)
    ax.text(0.105, rose + 0.12, f"Rose criterion CNR = {rose:g}", fontsize=9,
            color="black", ha="left")

    ax.set_xlabel("Dose ratio $r$ (simulated)")
    ax.set_ylabel("Detectability (CNR, Rose index)")
    ax.set_title("Dose-detectability curves, PWM-LDCT v0.5 baselines (SKE-Gaussian20HU-s2px)")
    ax.set_xticks(list(DOSE_RATIOS))
    ax.set_xticklabels([f"{r:.2f}" for r in DOSE_RATIOS])
    ax.set_xlim(0.08, 0.54)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    return out_png


def build_curve(results_dir: str, out_png: str, out_json: str) -> dict:
    stats = build_stats(results_dir)
    plot_curve(stats, out_png)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"wrote {out_png}")
    print(f"wrote {out_json}")
    return stats


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="dose-curve",
                                description="Build the dose-detectability curve from *_results_det.json")
    p.add_argument("--results-dir", default=None,
                   help="directory with *_results_det.json (default: baselines/results)")
    p.add_argument("--out-png", required=True, help="output curve PNG path")
    p.add_argument("--out-json", required=True, help="output statistics JSON path")
    args = p.parse_args(argv)
    results_dir = args.results_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "results")
    build_curve(results_dir, args.out_png, args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
