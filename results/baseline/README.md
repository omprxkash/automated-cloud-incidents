# Baseline Results

Stores outputs for the two baseline models: **ViT-Small** and **DeiT-Small** (no graph).

After training, you will find:
- `vit_best.pt` — best ViT-Small checkpoint
- `deit_best.pt` — best DeiT-Small checkpoint
- `vit_train_log.csv` — per-epoch loss and accuracy
- `deit_train_log.csv`
- `vit_confusion_matrix.png`
- `deit_confusion_matrix.png`
- `attention_maps/` — ViT layer attention overlays

Train baseline models:
```bash
python src/train.py --model vit  --epochs 100 --batch 128 --out results/baseline
python src/train.py --model deit --epochs 100 --batch 128 --out results/baseline
```
