from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
OUT_FILE = OUT_DIR / "supplementary_roi_volume_BA_logx.pdf"


def load_roi_volumes_cm3(npz_name):
    data = np.load(PROJECT_DIR / npz_name)
    roi_vols = data["roi_vols"]

    if roi_vols.ndim == 4:
        roi_vols = roi_vols[:, :, 0, :]

    # Drop background and terminal aggregate labels, matching the main ROI-volume BA figure.
    roi_vols = roi_vols[:, :, 1:-1]
    return roi_vols / 1000.0


def bland_altman_stats(diff):
    bias = np.mean(diff)
    sd = np.std(diff, ddof=1)
    return bias, bias - 1.96 * sd, bias + 1.96 * sd


def add_stats_box(ax, diff):
    bias, lower, upper = bland_altman_stats(diff)
    text = f"Bias: {bias:.2f} cm$^3$\n95% LoA: [{lower:.2f}, {upper:.2f}] cm$^3$"
    ax.text(
        0.03,
        0.96,
        text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8.5,
        bbox={"facecolor": "white", "edgecolor": "0.70", "alpha": 0.9, "pad": 4},
    )


def plot_log_volume_ba(ax, npz_name, title, color, ylim):
    roi_vols = load_roi_volumes_cm3(npz_name)
    v1 = roi_vols[0].ravel()
    v2 = roi_vols[1].ravel()
    mean_volume = (v1 + v2) / 2.0
    diff = v1 - v2

    valid = np.isfinite(mean_volume) & np.isfinite(diff) & (mean_volume > 0)
    mean_volume = mean_volume[valid]
    diff = diff[valid]

    bias, lower, upper = bland_altman_stats(diff)

    ax.scatter(mean_volume, diff, s=12, color=color, alpha=0.55, edgecolors="none")
    ax.axhline(bias, color="#dc2626", linestyle="--", linewidth=1.0)
    ax.axhline(lower, color="0.20", linestyle="--", linewidth=0.9)
    ax.axhline(upper, color="0.20", linestyle="--", linewidth=0.9)
    ax.axhline(0, color="0.65", linestyle=":", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_ylim(ylim)
    ax.grid(True, color="0.88", linewidth=0.6)
    ax.set_title(title, loc="left", fontsize=12)
    ax.set_xlabel("Mean test-retest ROI volume (cm$^3$)")
    ax.set_ylabel("1st - 2nd repetition (cm$^3$)")
    add_stats_box(ax, diff)


def main():
    plt.rcParams.update(
        {
            "font.size": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
        }
    )

    fig, axs = plt.subplots(2, 2, figsize=(8.2, 6.4), constrained_layout=True)
    panels = [
        (axs[0, 0], "brainSuite_low_field.npz", "(a) BrainSuite 0.55T", "#2563eb", (-6, 6)),
        (axs[0, 1], "brainSuite_3T.npz", "(b) BrainSuite 3T", "#15803d", (-6, 6)),
        (axs[1, 0], "freesurfer_low_field.npz", "(c) FreeSurfer 0.55T", "#2563eb", (-15, 15)),
        (axs[1, 1], "freesurfer_3T.npz", "(d) FreeSurfer 3T", "#15803d", (-15, 15)),
    ]

    for panel in panels:
        plot_log_volume_ba(*panel)

    fig.savefig(OUT_FILE, bbox_inches="tight")
    print(f"Saved {OUT_FILE}")


if __name__ == "__main__":
    main()
