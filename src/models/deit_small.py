"""DeiTSmall: Data-efficient Image Transformer with distillation token.

Teacher model: ResNet-50 (pretrained on ImageNet, frozen).
Loss: 0.5 * CE(student_cls, labels) + 0.5 * KL(student_distill, teacher_softmax)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class PatchEmbedding(nn.Module):
    def __init__(self, img_size: int, patch_size: int, embed_dim: int):
        super().__init__()
        self.num_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(3, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        return self.proj(x).flatten(2).transpose(1, 2)  # (B, N, D)


class DeiTSmall(nn.Module):
    """DeiT-Small architecture (d=384, heads=6, layers=12) — from-scratch."""

    def __init__(
        self,
        img_size: int = 128,
        patch_size: int = 16,
        num_classes: int = 100,
        embed_dim: int = 384,
        depth: int = 12,
        nhead: int = 6,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, embed_dim)
        N = self.patch_embed.num_patches

        self.cls_token   = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.dist_token  = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed   = nn.Parameter(torch.zeros(1, N + 2, embed_dim))
        self.drop        = nn.Dropout(dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=nhead,
            dim_feedforward=int(embed_dim * mlp_ratio),
            dropout=dropout, activation="gelu",
            batch_first=True, norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=depth)
        self.norm = nn.LayerNorm(embed_dim)

        self.head      = nn.Linear(embed_dim, num_classes)   # for CLS token
        self.head_dist = nn.Linear(embed_dim, num_classes)   # for distillation token

        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.dist_token, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.size(0)
        tokens = self.patch_embed(x)
        cls  = self.cls_token.expand(B, -1, -1)
        dist = self.dist_token.expand(B, -1, -1)
        tokens = torch.cat([cls, dist, tokens], dim=1)  # (B, N+2, D)
        tokens = tokens + self.pos_embed
        tokens = self.drop(tokens)
        tokens = self.transformer(tokens)
        tokens = self.norm(tokens)

        cls_out  = self.head(tokens[:, 0])
        dist_out = self.head_dist(tokens[:, 1])

        if self.training:
            return cls_out, dist_out   # both needed for distillation loss
        # at inference: average cls + distillation logits
        return (cls_out + dist_out) / 2


def distillation_loss(
    cls_logits: torch.Tensor,
    dist_logits: torch.Tensor,
    labels: torch.Tensor,
    teacher_logits: torch.Tensor,
    alpha: float = 0.5,
    temperature: float = 3.0,
) -> torch.Tensor:
    """Combined cross-entropy (hard) + KL-divergence (soft) loss."""
    ce_loss = F.cross_entropy(cls_logits, labels)
    soft_teacher = F.softmax(teacher_logits / temperature, dim=-1)
    soft_student = F.log_softmax(dist_logits / temperature, dim=-1)
    kl_loss = F.kl_div(soft_student, soft_teacher, reduction="batchmean") * (temperature ** 2)
    return (1 - alpha) * ce_loss + alpha * kl_loss
