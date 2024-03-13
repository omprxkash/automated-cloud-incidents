# Improved Results

Stores outputs for the two graph-attention models: **GAT-ViT** (dense graph) and **Sparse-GAT-ViT** (sparse k-NN, main contribution).

After training, you will find:
- `gat_vit_best.pt` — best GAT-ViT checkpoint
- `sparse_gat_best.pt` — best Sparse-GAT-ViT checkpoint
- `gat_vit_train_log.csv` — per-epoch loss and accuracy
- `sparse_gat_train_log.csv`
- `gat_vit_confusion_matrix.png`
- `sparse_gat_confusion_matrix.png`
- `tsne_embeddings.png` — t-SNE of learned patch representations
- `edge_count_analysis.png` — sparse vs dense edge comparison

Train graph models:
```bash
python src/train.py --model gat_vit    --epochs 100 --batch 64 --out results/improved
python src/train.py --model sparse_gat --epochs 100 --batch 64 --graph-k 4 --threshold 0.1 --out results/improved
```
