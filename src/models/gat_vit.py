"""GATViT: EfficientNetV2-S backbone + dense 8-neighbor graph + GAT + Transformer.

Pipeline:
  Input → MultiScaleEncoder → PatchGraphBuilder (dense) → SpatialAttentionBlock
        → GlobalTransformerStack → ClassifierHead
"""

import math
import torch
import torch.nn as nn
import timm
from torch_geometric.nn import GATConv, global_mean_pool

from src.graph_builder import PatchGraphBuilder


class MultiScaleEncoder(nn.Module):
    """EfficientNetV2-S feature extractor (final feature stage only)."""

    def __init__(self, freeze_early: bool = True):
        super().__init__()
        backbone = timm.create_model(
            "tf_efficientnetv2_s", pretrained=False, features_only=True
        )
        self.stages = backbone
        self.out_channels = backbone.feature_info.channels()[-1]  # 256 for stage-4

        if freeze_early:
            # freeze first two stages
            for name, param in backbone.named_parameters():
                if name.startswith("blocks.0") or name.startswith("blocks.1"):
                    param.requires_grad_(False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.stages(x)
        return feats[-1]  # (B, C, H', W')


class SpatialAttentionBlock(nn.Module):
    """Two-layer GAT operating on patch graph nodes."""

    def __init__(self, in_dim: int, hidden: int = 128, heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.gat1 = GATConv(in_dim, hidden, heads=heads, dropout=dropout, concat=True)
        self.act1 = nn.ELU()
        self.gat2 = GATConv(hidden * heads, hidden, heads=1, dropout=dropout, concat=False)
        self.act2 = nn.ELU()
        self.out_dim = hidden

    def forward(self, x, edge_index, edge_attr=None, batch=None):
        x = self.act1(self.gat1(x, edge_index))
        x = self.act2(self.gat2(x, edge_index))
        pooled = global_mean_pool(x, batch)  # (B, hidden)
        return pooled


class GlobalTransformerStack(nn.Module):
    """Lightweight Transformer encoder that processes a sequence of 1 pooled token
    plus a learned CLS token."""

    def __init__(self, in_dim: int, d_model: int = 256, nhead: int = 8,
                 num_layers: int = 4, dropout: float = 0.1):
        super().__init__()
        self.proj = nn.Linear(in_dim, d_model)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))

        # sinusoidal for 2 positions (cls + pooled)
        pe = torch.zeros(2, d_model)
        pos = torch.arange(2).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead,
            dim_feedforward=d_model * 4, dropout=dropout,
            activation="gelu", batch_first=True, norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.d_model = d_model

    def forward(self, pooled: torch.Tensor) -> torch.Tensor:
        # pooled: (B, in_dim)
        B = pooled.size(0)
        token = self.proj(pooled).unsqueeze(1)              # (B, 1, d_model)
        cls   = self.cls_token.expand(B, -1, -1)           # (B, 1, d_model)
        seq   = torch.cat([cls, token], dim=1)             # (B, 2, d_model)
        seq   = seq + self.pe
        seq   = self.transformer(seq)
        seq   = self.norm(seq)
        return seq[:, 0]                                   # CLS output (B, d_model)


class ClassifierHead(nn.Module):
    def __init__(self, in_dim: int, hidden: int = 512, num_classes: int = 100,
                 dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class GATViT(nn.Module):
    """Full GATViT: CNN → dense graph → GAT → Transformer → classifier."""

    def __init__(
        self,
        num_classes: int = 100,
        patch_k: int = 4,
        gat_hidden: int = 128,
        gat_heads: int = 4,
        d_model: int = 256,
        nhead: int = 8,
        transformer_layers: int = 4,
        mlp_hidden: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone   = MultiScaleEncoder()
        self.graph_builder = PatchGraphBuilder(patch_k=patch_k, mode="dense")
        self.gat        = SpatialAttentionBlock(
            in_dim=self.backbone.out_channels,
            hidden=gat_hidden, heads=gat_heads, dropout=dropout,
        )
        self.transformer = GlobalTransformerStack(
            in_dim=gat_hidden, d_model=d_model,
            nhead=nhead, num_layers=transformer_layers, dropout=dropout,
        )
        self.head = ClassifierHead(d_model, mlp_hidden, num_classes, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.backbone(x)
        pyg_batch = self.graph_builder.build(feat)
        pyg_batch = pyg_batch.to(x.device)
        pooled = self.gat(
            pyg_batch.x, pyg_batch.edge_index,
            getattr(pyg_batch, "edge_attr", None), pyg_batch.batch,
        )
        out = self.transformer(pooled)
        return self.head(out)
