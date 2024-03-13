"""Regenerate all result figures from saved CSV logs and metrics files.

Run this after all models have been trained and evaluated:
    python results/generate_results.py
"""

import csv
import sys
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.abspath("."))
from src.visualize import plot_training_curves

RESULTS = Path("results")
MODELS  = ["vit", "gat_vit", "sparse_gat", "deit"]
LABELS  = ["ViT-Small", "GAT-ViT", "Sparse-GAT-ViT", "DeiT-Small"]
DARK_BG = "#1a1a2e"


def load_metrics(model_name: str) -> dict:
    p = RESULTS / model_name / "metrics.txt"
    if not p.exists():
        return {"top1": 0.0, "top5": 0.0}
    return dict(line.strip().split("=") for line in p.read_text().splitlines() if "=" in line)


def plot_benchmark_comparison():
    """4-panel benchmark figure: top-1, top-5, params, and accuracy scatter."""
    all_metrics = {m: load_metrics(m) for m in MODELS}
    top1  = [float(all_metrics[m].get("top1", 0)) * 100 for m in MODELS]
    top5  = [float(all_metrics[m].get("top5", 0)) * 100 for m in MODELS]
    params = [5.7, 12.3, 12.1, 22.0]  # approximate M params per model

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor(DARK_BG)
    colors = ["#e94560", "#0f3460", "#16213e", "#533483"]

    # Panel 1: Top-1 accuracy
    ax = axes[0, 0]
    ax.set_facecolor("#16213e")
    bars = ax.bar(LABELS, top1, color=colors, edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, top1):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.3, f"{v:.1f}%",
                ha="center", color="white", fontsize=9)
    ax.set_title("Top-1 Accuracy", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.set_ylabel("Accuracy (%)", color="white")
    ax.set_ylim(0, 100)

    # Panel 2: Top-5 accuracy
    ax = axes[0, 1]
    ax.set_facecolor("#16213e")
    bars = ax.bar(LABELS, top5, color=colors, edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, top5):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.3, f"{v:.1f}%",
                ha="center", color="white", fontsize=9)
    ax.set_title("Top-5 Accuracy", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.set_ylabel("Accuracy (%)", color="white")
    ax.set_ylim(0, 100)

    # Panel 3: Params
    ax = axes[1, 0]
    ax.set_facecolor("#16213e")
    ax.bar(LABELS, params, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Model Parameters (M)", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.set_ylabel("Params (M)", color="white")

    # Panel 4: Params vs Top-1 scatter
    ax = axes[1, 1]
    ax.set_facecolor("#16213e")
    for i, (label, p, t1) in enumerate(zip(LABELS, params, top1)):
        ax.scatter(p, t1, color=colors[i], s=120, zorder=5)
        ax.annotate(label, (p, t1), textcoords="offset points",
                    xytext=(5, 5), color="white", fontsize=8)
    ax.set_xlabel("Params (M)", color="white")
    ax.set_ylabel("Top-1 (%)", color="white")
    ax.set_title("Efficiency: Params vs Accuracy", color="white", fontsize=12)
    ax.tick_params(colors="white")

    plt.suptitle("Benchmark Comparison — CIFAR-100", color="white", fontsize=14)
    plt.tight_layout()
    out = RESULTS / "benchmark_comparison.png"
    fig.savefig(out, dpi=150, facecolor=DARK_BG)
    plt.close(fig)
    print(f"Benchmark comparison saved → {out}")


def regenerate_training_curves():
    for model_name in MODELS:
        log_path = RESULTS / model_name / "train_log.csv"
        if log_path.exists():
            plot_training_curves(str(log_path), RESULTS / model_name)
        else:
            print(f"  [skip] {model_name}/train_log.csv not found")


if __name__ == "__main__":
    print("Regenerating all result figures …")
    regenerate_training_curves()
    plot_benchmark_comparison()
    print("Done.")
