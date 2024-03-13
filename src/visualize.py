"""Visualization utilities: attention maps, t-SNE embeddings, training curves.

Usage:
    python src/visualize.py --mode attention --model vit --checkpoint results/vit/best.pt
    python src/visualize.py --mode tsne     --model sparse_gat --checkpoint results/sparse_gat/best.pt
    python src/visualize.py --mode curves   --log results/sparse_gat/train_log.csv
"""

import argparse
import csv
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from sklearn.manifold import TSNE

from src.preprocess import get_dataloaders, build_eval_transform
from src.models import ViTSmall, GATViT, SparseGATViT, DeiTSmall


DARK_BG = "#1a1a2e"
ACCENT  = "#e94560"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["attention", "tsne", "curves"], required=True)
    p.add_argument("--model",      type=str, default="vit",
                   choices=["vit", "gat_vit", "sparse_gat", "deit"])
    p.add_argument("--checkpoint", type=str, default="")
    p.add_argument("--log",        type=str, default="")
    p.add_argument("--data",       type=str, default="./data")
    p.add_argument("--out",        type=str, default="./results")
    p.add_argument("--n-samples",  type=int, default=1000)
    p.add_argument("--patch-k",    type=int, default=4)
    p.add_argument("--graph-k",    type=int, default=4)
    p.add_argument("--threshold",  type=float, default=0.1)
    p.add_argument("--device",     type=str, default="")
    return p.parse_args()


def load_model(name, ckpt, args, device):
    if name == "vit":
        m = ViTSmall(img_size=128, patch_size=16, num_classes=100)
    elif name == "gat_vit":
        m = GATViT(num_classes=100, patch_k=args.patch_k)
    elif name == "sparse_gat":
        m = SparseGATViT(num_classes=100, patch_k=args.patch_k,
                         graph_k=args.graph_k, threshold=args.threshold)
    elif name == "deit":
        m = DeiTSmall(img_size=128, patch_size=16, num_classes=100)
    m.load_state_dict(torch.load(ckpt, map_location=device))
    return m.to(device).eval()


# ──────────────────────────────────────────────────────────
# Attention maps (ViT / DeiT)
# ──────────────────────────────────────────────────────────

def extract_vit_attention(model: ViTSmall, img_tensor: torch.Tensor):
    """Return list of attention weight tensors, one per Transformer layer."""
    hooks, attn_weights = [], []

    def make_hook(module, input, output):
        # nn.MultiheadAttention returns (output, attn_weights) when need_weights=True
        pass

    # We use the model's built-in method
    with torch.no_grad():
        weights = model.get_attention_weights(img_tensor.unsqueeze(0))
    return weights  # list of (1, nhead, N+1, N+1)


def plot_attention_maps(model, img_tensor, save_dir: Path, img_size: int = 128):
    weights = extract_vit_attention(model, img_tensor)
    n_layers = len(weights)
    fig, axes = plt.subplots(2, n_layers // 2, figsize=(n_layers * 2, 6))
    fig.patch.set_facecolor(DARK_BG)

    patch_size = 16
    n_patches_side = img_size // patch_size

    for idx, attn in enumerate(weights):
        # average across heads, take CLS→patch attention
        attn_mean = attn[0].mean(0)[0, 1:]   # (N,)
        attn_map  = attn_mean.reshape(n_patches_side, n_patches_side).numpy()
        attn_map  = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)

        ax = axes.flat[idx]
        ax.imshow(attn_map, cmap="inferno", interpolation="bilinear")
        ax.set_title(f"Layer {idx+1}", color="white", fontsize=8)
        ax.axis("off")

    plt.suptitle("Transformer Attention Maps (CLS → Patches)", color="white", fontsize=12)
    plt.tight_layout()
    save_path = save_dir / "attention_maps.png"
    fig.savefig(save_path, dpi=150, facecolor=DARK_BG)
    plt.close(fig)
    print(f"Attention maps saved → {save_path}")


# ──────────────────────────────────────────────────────────
# t-SNE embedding visualization
# ──────────────────────────────────────────────────────────

def extract_embeddings(model, loader, device, n_samples=1000):
    embeddings, targets = [], []
    collected = 0

    hooks = []
    features = {}

    def hook_fn(module, input, output):
        features["embed"] = output.detach().cpu()

    # hook into the layer before the final classifier head
    if hasattr(model, "head") and hasattr(model.head, "net"):
        handle = model.head.net[0].register_forward_hook(hook_fn)  # first Linear
        hooks.append(handle)
    elif hasattr(model, "head"):
        handle = model.head.register_forward_pre_hook(
            lambda m, inp: features.update({"embed": inp[0].detach().cpu()})
        )
        hooks.append(handle)

    with torch.no_grad():
        for imgs, labels in loader:
            if collected >= n_samples:
                break
            imgs = imgs.to(device)
            _ = model(imgs)
            emb = features.get("embed", torch.zeros(imgs.size(0), 1))
            n = min(n_samples - collected, emb.size(0))
            embeddings.append(emb[:n])
            targets.append(labels[:n])
            collected += n

    for h in hooks:
        h.remove()

    return torch.cat(embeddings).numpy(), torch.cat(targets).numpy()


def plot_tsne(embeddings, targets, save_path: Path, n_classes: int = 100):
    print("Computing t-SNE (this may take ~1 min) …")
    tsne = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)
    reduced = tsne.fit_transform(embeddings)

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    palette = cm.get_cmap("tab20", n_classes)
    scatter = ax.scatter(
        reduced[:, 0], reduced[:, 1],
        c=targets, cmap="tab20", s=5, alpha=0.6,
    )
    plt.colorbar(scatter, ax=ax, label="Class ID")
    ax.set_title("t-SNE of Learned Embeddings", color="white", fontsize=14)
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")

    plt.tight_layout()
    fig.savefig(save_path, dpi=150, facecolor=DARK_BG)
    plt.close(fig)
    print(f"t-SNE plot saved → {save_path}")


# ──────────────────────────────────────────────────────────
# Training curves (dark WandB style)
# ──────────────────────────────────────────────────────────

def plot_training_curves(log_csv: str, save_dir: Path):
    epochs, tr_loss, tr1, tr5 = [], [], [], []
    va_loss, va1, va5, lrs = [], [], [], []

    with open(log_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            epochs.append(int(row["epoch"]))
            tr_loss.append(float(row["train_loss"]))
            tr1.append(float(row["train_top1"]) * 100)
            tr5.append(float(row["train_top5"]) * 100)
            va_loss.append(float(row["val_loss"]))
            va1.append(float(row["val_top1"]) * 100)
            va5.append(float(row["val_top5"]) * 100)
            lrs.append(float(row["lr"]))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.patch.set_facecolor(DARK_BG)
    titles = ["Loss", "Top-1 Accuracy (%)", "Top-5 Accuracy (%)"]
    train_data = [tr_loss, tr1, tr5]
    val_data   = [va_loss, va1, va5]

    for ax, title, tr, va in zip(axes, titles, train_data, val_data):
        ax.set_facecolor("#16213e")
        ax.plot(epochs, tr, color="#e94560", label="Train", linewidth=2)
        ax.plot(epochs, va, color="#0f3460", label="Val",   linewidth=2)
        ax.set_title(title, color="white", fontsize=12)
        ax.set_xlabel("Epoch", color="white")
        ax.tick_params(colors="white")
        ax.legend(facecolor=DARK_BG, labelcolor="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    plt.suptitle("Training Curves", color="white", fontsize=14)
    plt.tight_layout()
    save_path = save_dir / "training_curves.png"
    fig.savefig(save_path, dpi=150, facecolor=DARK_BG)
    plt.close(fig)
    print(f"Training curves saved → {save_path}")


def main():
    args = parse_args()
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device)
    out_dir = Path(args.out) / args.model
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "curves":
        plot_training_curves(args.log, out_dir)
        return

    model = load_model(args.model, args.checkpoint, args, device)

    if args.mode == "attention":
        if args.model not in ("vit", "deit"):
            print("Attention map visualization only supported for ViT/DeiT.")
            return
        _, _, test_loader = get_dataloaders(args.data, batch_size=1)
        img, _ = next(iter(test_loader))
        plot_attention_maps(model, img[0], out_dir)

    elif args.mode == "tsne":
        _, _, test_loader = get_dataloaders(args.data, batch_size=64)
        embeddings, targets = extract_embeddings(
            model, test_loader, device, args.n_samples
        )
        plot_tsne(embeddings, targets, out_dir / "tsne.png")


if __name__ == "__main__":
    main()
