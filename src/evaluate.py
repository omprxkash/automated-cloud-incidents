"""Evaluation script: top-1, top-5, per-class accuracy, confusion matrix.

Usage:
    python src/evaluate.py --model sparse_gat --checkpoint results/sparse_gat/best.pt
"""

import argparse
import csv
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.preprocess import get_dataloaders, get_class_names
from src.models import ViTSmall, GATViT, SparseGATViT, DeiTSmall


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",      type=str, required=True,
                   choices=["vit", "gat_vit", "sparse_gat", "deit"])
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--data",       type=str, default="./data")
    p.add_argument("--batch",      type=int, default=128)
    p.add_argument("--workers",    type=int, default=4)
    p.add_argument("--out",        type=str, default="./results")
    p.add_argument("--device",     type=str, default="")
    p.add_argument("--patch-k",    type=int, default=4)
    p.add_argument("--graph-k",    type=int, default=4)
    p.add_argument("--threshold",  type=float, default=0.1)
    return p.parse_args()


def load_model(name: str, ckpt_path: str, args, device) -> nn.Module:
    if name == "vit":
        m = ViTSmall(img_size=128, patch_size=16, num_classes=100)
    elif name == "gat_vit":
        m = GATViT(num_classes=100, patch_k=args.patch_k)
    elif name == "sparse_gat":
        m = SparseGATViT(num_classes=100, patch_k=args.patch_k,
                         graph_k=args.graph_k, threshold=args.threshold)
    elif name == "deit":
        m = DeiTSmall(img_size=128, patch_size=16, num_classes=100)
    else:
        raise ValueError(name)
    m.load_state_dict(torch.load(ckpt_path, map_location=device))
    return m.to(device).eval()


@torch.no_grad()
def collect_predictions(model, loader, device):
    all_preds, all_labels, all_logits = [], [], []
    for imgs, labels in loader:
        imgs = imgs.to(device)
        logits = model(imgs)
        if isinstance(logits, tuple):
            logits = (logits[0] + logits[1]) / 2
        all_logits.append(logits.cpu())
        all_preds.append(logits.argmax(dim=1).cpu())
        all_labels.append(labels)
    return (
        torch.cat(all_preds).numpy(),
        torch.cat(all_labels).numpy(),
        torch.cat(all_logits),
    )


def top_k_acc(logits, labels, k):
    _, pred = logits.topk(k, dim=1)
    correct = pred.eq(torch.tensor(labels).unsqueeze(1).expand_as(pred))
    return correct.any(dim=1).float().mean().item()


def per_class_accuracy(preds, labels, num_classes=100):
    accs = []
    for c in range(num_classes):
        mask = labels == c
        if mask.sum() == 0:
            accs.append(float("nan"))
        else:
            accs.append((preds[mask] == c).mean())
    return accs


def plot_confusion_matrix(preds, labels, class_names, save_path):
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(labels, preds)
    fig, ax = plt.subplots(figsize=(20, 18))
    sns.heatmap(cm, annot=False, fmt="d", cmap="Blues", ax=ax,
                xticklabels=False, yticklabels=False)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("True", fontsize=12)
    ax.set_title("Confusion Matrix (100 classes)", fontsize=14)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved → {save_path}")


def main():
    args = parse_args()
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device)

    _, _, test_loader = get_dataloaders(
        data_root=args.data, batch_size=args.batch, num_workers=args.workers
    )
    class_names = get_class_names(args.data)

    model = load_model(args.model, args.checkpoint, args, device)

    print("Running evaluation on test set …")
    preds, labels, logits = collect_predictions(model, test_loader, device)

    top1 = top_k_acc(logits, labels, 1)
    top5 = top_k_acc(logits, labels, 5)
    print(f"\n{'='*40}")
    print(f"Model:   {args.model}")
    print(f"Top-1:   {top1*100:.2f}%")
    print(f"Top-5:   {top5*100:.2f}%")
    print(f"{'='*40}")

    # per-class accuracy CSV
    out_dir = Path(args.out) / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    per_class = per_class_accuracy(preds, labels)
    csv_path = out_dir / "per_class_accuracy.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class_id", "class_name", "accuracy"])
        for i, (name, acc) in enumerate(zip(class_names, per_class)):
            writer.writerow([i, name, f"{acc:.4f}"])
    print(f"Per-class accuracy saved → {csv_path}")

    # confusion matrix
    cm_path = out_dir / "confusion_matrix.png"
    plot_confusion_matrix(preds, labels, class_names, cm_path)

    # summary metrics file
    metrics_path = out_dir / "metrics.txt"
    with open(metrics_path, "w") as f:
        f.write(f"model={args.model}\n")
        f.write(f"top1={top1:.4f}\n")
        f.write(f"top5={top5:.4f}\n")
    print(f"Metrics saved → {metrics_path}")


if __name__ == "__main__":
    main()
