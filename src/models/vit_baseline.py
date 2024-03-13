"""ViTSmall: standard Vision Transformer baseline (no CNN backbone, no graph).

Patch embedding via strided Conv2d → positional encoding → Transformer encoder
→ CLS token → linear classifier.
"""

import math
import torch
import torch.nn as nn


class PatchEmbedding(nn.Module):
    def __init__(self, img_size: int, patch_size: int, in_ch: int, embed_dim: int):
        super().__init__()
        assert img_size % patch_size == 0
        self.num_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(in_ch, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, H, W) → (B, N, D)
        x = self.proj(x)                    # (B, D, nH, nW)
        x = x.flatten(2).transpose(1, 2)   # (B, N, D)
        return x


class SinusoidalPositionEncoding(nn.Module):
    def __init__(self, num_patches: int, embed_dim: int):
        super().__init__()
        pe = torch.zeros(num_patches + 1, embed_dim)
        pos = torch.arange(num_patches + 1).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, embed_dim, 2).float() * (-math.log(10000.0) / embed_dim))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, N+1, D)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class ViTSmall(nn.Module):
    """Lightweight ViT: 12 layers, d_model=192, nhead=3."""

    def __init__(
        self,
        img_size: int = 128,
        patch_size: int = 16,
        num_classes: int = 100,
        embed_dim: int = 192,
        depth: int = 12,
        nhead: int = 3,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, 3, embed_dim)
        num_patches = self.patch_embed.num_patches

        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_enc   = SinusoidalPositionEncoding(num_patches, embed_dim)
        self.drop      = nn.Dropout(dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=nhead,
            dim_feedforward=int(embed_dim * mlp_ratio),
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=depth)
        self.norm = nn.LayerNorm(embed_dim)

        self.head = nn.Linear(embed_dim, num_classes)
        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.head.weight, std=0.02)
        nn.init.zeros_(self.head.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.size(0)
        tokens = self.patch_embed(x)                           # (B, N, D)
        cls = self.cls_token.expand(B, -1, -1)                 # (B, 1, D)
        tokens = torch.cat([cls, tokens], dim=1)               # (B, N+1, D)
        tokens = self.pos_enc(tokens)
        tokens = self.drop(tokens)
        tokens = self.transformer(tokens)
        tokens = self.norm(tokens)
        cls_out = tokens[:, 0]                                  # (B, D)
        return self.head(cls_out)

    def get_attention_weights(self, x: torch.Tensor) -> list[torch.Tensor]:
        """Return per-layer attention weight tensors for visualization."""
        weights = []
        B = x.size(0)
        tokens = self.patch_embed(x)
        cls = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)
        tokens = self.pos_enc(tokens)

        for layer in self.transformer.layers:
            attn_out, attn_w = layer.self_attn(
                tokens, tokens, tokens, need_weights=True, average_attn_weights=False
            )
            weights.append(attn_w.detach().cpu())
            tokens = layer(tokens)
        return weights
