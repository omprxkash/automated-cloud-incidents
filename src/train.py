"""Unified training CLI for all four model variants.

Usage:
    python src/train.py --model vit --epochs 100 --batch 128
    python src/train.py --model gat_vit --epochs 100 --batch 64
    python src/train.py --model sparse_gat --epochs 100 --batch 64
    python src/train.py --model deit --epochs 100 --batch 128
"""

import argparse
import csv
import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import LambdaLR
import torchvision.models as tv_models

from src.preprocess import get_dataloaders
from src.models import ViTSmall, GATViT, SparseGATViT, DeiTSmall
from src.models.deit_small import distillation_loss


def parse_args():
    p = argparse.ArgumentParser(description="Train graph-attention vision transformer on CIFAR-100")
    p.add_argument("--model",    type=str, default="sparse_gat",
                   choices=["vit", "gat_vit", "sparse_gat", "deit"])
    p.add_argument("--epochs",   type=int, default=100)
    p.add_argument("--batch",    type=int, default=128)
    p.add_argument("--lr",       type=float, default=1e-3)
    p.add_argument("--warmup",   type=int, default=10)
    p.add_argument("--wd",       type=float, default=1e-2)
    p.add_argument("--grad-clip",type=float, default=1.0)
    p.add_argument("--workers",  type=int, default=4)
    p.add_argument("--data",     type=str, default="./data")
    p.add_argument("--out",      type=str, default="./results")
    p.add_argument("--device",   type=str, default="")
    p.add_argument("--seed",     type=int, default=42)
    # graph-specific
    p.add_argument("--patch-k",  type=int, default=4)
    p.add_argument("--graph-k",  type=int, default=4)
    p.add_argument("--threshold",type=float, default=0.1)
    return p.parse_args()


def build_model(name: str, args) -> nn.Module:
    if name == "vit":
        return ViTSmall(img_size=128, patch_size=16, num_classes=100)
    if name == "gat_vit":
        return GATViT(num_classes=100, patch_k=args.patch_k)
    if name == "sparse_gat":
        return SparseGATViT(
            num_classes=100, patch_k=args.patch_k,
            graph_k=args.graph_k, threshold=args.threshold,
        )
    if name == "deit":
        return DeiTSmall(img_size=128, patch_size=16, num_classes=100)
    raise ValueError(f"Unknown model: {name}")


def warmup_cosine_schedule(optimizer, warmup_epochs: int, total_epochs: int) -> LambdaLR:
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(1, total_epochs - warmup_epochs)
        import math
        return 0.5 * (1.0 + math.cos(math.pi * progress))
    return LambdaLR(optimizer, lr_lambda)


def top_k_accuracy(logits: torch.Tensor, targets: torch.Tensor, k: int) -> float:
    _, pred = logits.topk(k, dim=1, largest=True, sorted=True)
    correct = pred.eq(targets.unsqueeze(1).expand_as(pred))
    return correct.any(dim=1).float().mean().item()


def run_epoch(model, loader, criterion, optimizer, device, grad_clip, scheduler=None,
              teacher=None, alpha=0.5, is_train=True, log_interval=50):
    model.train(is_train)
    total_loss, total_top1, total_top5, n_batches = 0.0, 0.0, 0.0, 0
    ctx = torch.enable_grad() if is_train else torch.no_grad()

    with ctx:
        for batch_idx, (imgs, labels) in enumerate(loader):
            imgs, labels = imgs.to(device), labels.to(device)

            if is_train:
                optimizer.zero_grad()

            if teacher is not None and is_train:
                # DeiT distillation
                cls_logits, dist_logits = model(imgs)
                with torch.no_grad():
                    teacher_logits = teacher(imgs)
                loss = distillation_loss(cls_logits, dist_logits, labels, teacher_logits, alpha)
                logits = (cls_logits + dist_logits) / 2
            else:
                logits = model(imgs)
                if isinstance(logits, tuple):
                    logits = (logits[0] + logits[1]) / 2
                loss = criterion(logits, labels)

            if is_train:
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                optimizer.step()

            total_loss += loss.item()
            total_top1 += top_k_accuracy(logits, labels, 1)
            total_top5 += top_k_accuracy(logits, labels, 5)
            n_batches  += 1

            if is_train and batch_idx % log_interval == 0:
                lr_now = optimizer.param_groups[0]["lr"]
                print(f"  batch {batch_idx}/{len(loader)}  "
                      f"loss={loss.item():.4f}  top1={total_top1/n_batches:.3f}  "
                      f"lr={lr_now:.6f}")

    if scheduler is not None and is_train:
        scheduler.step()

    return total_loss / n_batches, total_top1 / n_batches, total_top5 / n_batches


def main():
    args = parse_args()
    torch.manual_seed(args.seed)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device)
    print(f"Device: {device}")

    train_loader, val_loader, _ = get_dataloaders(
        data_root=args.data, batch_size=args.batch,
        num_workers=args.workers,
    )

    model = build_model(args.model, args).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model: {args.model}  |  trainable params: {n_params/1e6:.2f}M")

    teacher = None
    if args.model == "deit":
        teacher = tv_models.resnet50(weights=tv_models.ResNet50_Weights.IMAGENET1K_V1)
        teacher = teacher.to(device).eval()
        for p in teacher.parameters():
            p.requires_grad_(False)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    scheduler = warmup_cosine_schedule(optimizer, args.warmup, args.epochs)

    out_dir = Path(args.out) / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "train_log.csv"

    best_val_top1 = 0.0
    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "train_top1", "train_top5",
                         "val_loss", "val_top1", "val_top5", "lr"])

        for epoch in range(1, args.epochs + 1):
            t0 = time.time()
            lr_now = optimizer.param_groups[0]["lr"]
            print(f"\n=== Epoch {epoch}/{args.epochs}  lr={lr_now:.6f} ===")

            tr_loss, tr1, tr5 = run_epoch(
                model, train_loader, criterion, optimizer, device,
                args.grad_clip, scheduler, teacher, is_train=True,
            )
            va_loss, va1, va5 = run_epoch(
                model, val_loader, criterion, optimizer, device,
                args.grad_clip, is_train=False,
            )

            elapsed = time.time() - t0
            print(f"  train loss={tr_loss:.4f}  top1={tr1:.3f}  top5={tr5:.3f}")
            print(f"  val   loss={va_loss:.4f}  top1={va1:.3f}  top5={va5:.3f}  [{elapsed:.1f}s]")

            writer.writerow([epoch, tr_loss, tr1, tr5, va_loss, va1, va5, lr_now])
            f.flush()

            torch.save(model.state_dict(), out_dir / "last.pt")
            if va1 > best_val_top1:
                best_val_top1 = va1
                torch.save(model.state_dict(), out_dir / "best.pt")
                print(f"  [checkpoint saved — best val top-1: {best_val_top1:.3f}]")

    print(f"\nTraining complete. Best val top-1: {best_val_top1:.3f}")
    print(f"Checkpoints: {out_dir}")


if __name__ == "__main__":
    main()
