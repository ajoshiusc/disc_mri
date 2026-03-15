#!/usr/bin/env python3
"""
Step 3 – Generate publication-quality figures and text report.

Loads the aggregated metric data produced by step2_extract_metrics.py
(``final_data.json``) and renders a 2×3 grid of error-bar plots, one
curve per TE value, metric vs. number of input stacks.

Prerequisites: run step2_extract_metrics.py first.
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np

from config import (
    FINAL_DATA_JSON, OUTPUT_DIR, TE_VALUES,
    # plt.rcParams are applied when config is imported
)

FIGURE_PATH = os.path.join(OUTPUT_DIR, "comprehensive_te_analysis_10subjects.png")

METRIC_INFO = [
    ('cr',     'Contrast Ratio (GM/WM)',              False),
    ('cnr',    'CNR (GM vs WM)',                       False),
    ('ssim',   'Structural Similarity Index (SSIM)',   False),
    ('snr_gm', 'SNR Gray Matter',                      False),
    ('snr_wm', 'SNR White Matter',                     False),
    ('nmse',   'Mean Squared Error (NMSE)',             True),
]


def load_final_data(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Aggregated data file not found: {path}\n"
            "Run step2_extract_metrics.py first."
        )
    with open(path) as f:
        raw = json.load(f)
    # Restore integer keys for TE values and stack counts
    return {
        int(te): {
            int(s): {metric: vals for metric, vals in md.items()}
            for s, md in sd.items()
        }
        for te, sd in raw.items()
    }


def plot(final_data: dict) -> None:
    colors  = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    markers = ['o', 's', '^', 'd']

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(
        'Comprehensive Image Quality Assessment: 10 Subject Average',
        fontsize=18, fontweight='bold', y=0.98,
    )

    for ax in axes.flat:
        ax.grid(True, linestyle='--', alpha=0.7)

    for idx, te in enumerate(TE_VALUES):
        valid_stacks = sorted(s for s in final_data[te] if 1 <= s <= 12)
        if not valid_stacks:
            continue

        c, m = colors[idx], markers[idx]

        for (key, title, is_log), ax in zip(METRIC_INFO, axes.flat):
            means, errs = [], []
            for s in valid_stacks:
                subj_means = [v for v in final_data[te][s][key] if not np.isnan(v)]
                if subj_means:
                    n = len(subj_means)
                    means.append(np.nanmean(subj_means))
                    errs.append(
                        np.nanstd(subj_means, ddof=1) / np.sqrt(n) if n > 1 else 0.0
                    )
                else:
                    means.append(np.nan)
                    errs.append(0.0)

            ax.errorbar(
                valid_stacks, means, yerr=errs,
                fmt=f"{m}-", color=c, label=f'TE {te} ms',
                capsize=4, capthick=1.5, elinewidth=1.5,
            )
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('Number of Input Stacks')
            if is_log:
                ax.set_yscale('log')

    for (key, title, is_log), ax in zip(METRIC_INFO, axes.flat):
        ax.legend(loc='best')
        ax.set_xticks(range(1, 13))

    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(FIGURE_PATH, dpi=300, bbox_inches='tight')
    print(f"  Saved figure → {FIGURE_PATH}")


def main() -> None:
    print("Step 3: Loading aggregated data ...")
    final_data = load_final_data(FINAL_DATA_JSON)

    print("Step 3: Generating figure ...")
    plot(final_data)
    print("Step 3 complete.")


if __name__ == "__main__":
    main()
