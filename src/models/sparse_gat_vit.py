"""SparseGATViT: same as GATViT but uses a sparse k-NN graph with Gaussian
edge weights and a pruning threshold.  This is the main contribution.
"""

import torch
import torch.nn as nn

from src.graph_builder import PatchGraphBuilder
from src.models.gat_vit import (
    MultiScaleEncoder,
    SpatialAttentionBlock,
    GlobalTransformerStack,
    ClassifierHead,
)


class SparseGATViT(nn.Module):
    """CNN → sparse k-NN graph (k=4, τ=0.1) → GAT → Transformer → classifier."""

    def __init__(
        self,
        num_classes: int = 100,
        patch_k: int = 4,
        graph_k: int = 4,
        sigma: float = 1.0,
        threshold: float = 0.1,
        gat_hidden: int = 128,
        gat_heads: int = 4,
        d_model: int = 256,
        nhead: int = 8,
        transformer_layers: int = 4,
        mlp_hidden: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone = MultiScaleEncoder()
        self.graph_builder = PatchGraphBuilder(
            patch_k=patch_k, mode="sparse",
            graph_k=graph_k, sigma=sigma, threshold=threshold,
        )
        self.gat = SpatialAttentionBlock(
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

    def edge_count_per_sample(self, x: torch.Tensor) -> float:
        """Average number of edges per graph in a batch (diagnostic)."""
        with torch.no_grad():
            feat = self.backbone(x)
            pyg_batch = self.graph_builder.build(feat)
            total_edges = pyg_batch.edge_index.shape[1]
            return total_edges / x.size(0)
