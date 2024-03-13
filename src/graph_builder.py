"""
PatchGraphBuilder: converts CNN feature maps into PyTorch Geometric graphs.

Two graph modes:
  - dense:  every patch connected to its 8 spatial neighbours (grid connectivity)
  - sparse: k-NN connectivity with Gaussian feature-similarity edge weights,
            edges below threshold tau are pruned
"""

import math
import torch
import torch.nn.functional as F
from torch_geometric.data import Data, Batch


class PatchGraphBuilder:
    """Extracts non-overlapping patches from a feature map and builds a graph.

    Args:
        patch_k:   spatial side-length of each patch (pixels in feature-map space)
        mode:      'dense' (8-neighbor) or 'sparse' (k-NN + Gaussian weights)
        graph_k:   number of nearest spatial neighbours in sparse mode
        sigma:     bandwidth of Gaussian similarity kernel
        threshold: minimum edge weight to keep in sparse mode
    """

    def __init__(
        self,
        patch_k: int = 4,
        mode: str = "sparse",
        graph_k: int = 4,
        sigma: float = 1.0,
        threshold: float = 0.1,
    ) -> None:
        self.patch_k    = patch_k
        self.mode       = mode
        self.graph_k    = graph_k
        self.sigma      = sigma
        self.threshold  = threshold

    # ------------------------------------------------------------------
    # Feature-map → patch nodes
    # ------------------------------------------------------------------

    def extract_patches(self, feat: torch.Tensor) -> torch.Tensor:
        """Unfold (B, C, H, W) feature map into (B, N, C*patch_k^2) patch vectors.

        Patches that don't fit exactly are discarded (floor division).
        """
        B, C, H, W = feat.shape
        k = self.patch_k
        # use unfold to extract non-overlapping k×k blocks
        patches = feat.unfold(2, k, k).unfold(3, k, k)  # (B, C, nH, nW, k, k)
        nH, nW = patches.shape[2], patches.shape[3]
        # reshape to (B, N, C*k*k)
        patches = patches.contiguous().view(B, C, nH, nW, k * k)
        patches = patches.permute(0, 2, 3, 1, 4)          # (B, nH, nW, C, k*k)
        patches = patches.reshape(B, nH * nW, C * k * k)  # (B, N, D)
        return patches  # N = nH * nW

    # ------------------------------------------------------------------
    # Graph construction helpers
    # ------------------------------------------------------------------

    def _grid_shape(self, feat: torch.Tensor) -> tuple[int, int]:
        H, W = feat.shape[2], feat.shape[3]
        return H // self.patch_k, W // self.patch_k

    def build_dense_graph(self, nH: int, nW: int) -> torch.Tensor:
        """8-neighbor COO edge_index for an nH×nW grid of patches."""
        edges = []
        N = nH * nW
        for r in range(nH):
            for c in range(nW):
                u = r * nW + c
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < nH and 0 <= nc < nW:
                            v = nr * nW + nc
                            edges.append((u, v))
        if not edges:
            # single-node graph: self-loop
            return torch.zeros(2, 1, dtype=torch.long)
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        return edge_index  # (2, E)

    def build_sparse_graph(
        self, patches: torch.Tensor, nH: int, nW: int
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """k-NN spatial graph with Gaussian feature-similarity edge weights.

        Returns:
            edge_index: (2, E)
            edge_attr:  (E,) — Gaussian similarity weights (pruned by threshold)
        """
        N = patches.shape[0]  # number of patch nodes (single image)
        k = min(self.graph_k, N - 1)

        # build spatial (row, col) positions for each patch
        positions = torch.zeros(N, 2, dtype=torch.float)
        for idx in range(N):
            r, c = divmod(idx, nW)
            positions[idx, 0] = r
            positions[idx, 1] = c

        # spatial distance → k-nearest neighbours
        pos_dist = torch.cdist(positions.float(), positions.float())  # (N, N)
        _, nn_idx = pos_dist.topk(k + 1, largest=False, dim=1)       # include self
        nn_idx = nn_idx[:, 1:]  # drop self (distance=0)

        # Gaussian feature similarity for candidate edges
        patch_norm = F.normalize(patches.float(), dim=-1)  # (N, D)
        src_list, dst_list, w_list = [], [], []
        for u in range(N):
            for v in nn_idx[u]:
                v = v.item()
                diff = patches[u].float() - patches[v].float()
                w = math.exp(-diff.pow(2).sum().item() / (self.sigma ** 2))
                if w >= self.threshold:
                    src_list.append(u)
                    dst_list.append(v)
                    w_list.append(w)

        if not src_list:
            # fallback: fully connect tiny graphs
            src_list = list(range(N))
            dst_list = list(range(N))
            w_list   = [1.0] * N

        edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
        edge_attr  = torch.tensor(w_list, dtype=torch.float)
        return edge_index, edge_attr

    # ------------------------------------------------------------------
    # Public: batch of images → list of PyG Data objects
    # ------------------------------------------------------------------

    def build(self, feat: torch.Tensor) -> Batch:
        """Convert a batch of feature maps to a PyG Batch.

        Args:
            feat: (B, C, H, W) — feature maps from CNN backbone

        Returns:
            PyG Batch object with .x, .edge_index, (.edge_attr), .batch
        """
        patches_batch = self.extract_patches(feat)  # (B, N, D)
        B = patches_batch.shape[0]
        nH, nW = self._grid_shape(feat)

        data_list = []
        for i in range(B):
            x = patches_batch[i]  # (N, D)
            if self.mode == "dense":
                edge_index = self.build_dense_graph(nH, nW)
                data = Data(x=x, edge_index=edge_index)
            else:
                edge_index, edge_attr = self.build_sparse_graph(x, nH, nW)
                data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data_list.append(data)

        return Batch.from_data_list(data_list)
