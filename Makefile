.PHONY: install train-vit train-gat train-sparse train-deit eval-all viz results clean

install:
	pip install -r requirements.txt

train-vit:
	python src/train.py --model vit --epochs 100 --batch 128

train-gat:
	python src/train.py --model gat_vit --epochs 100 --batch 64

train-sparse:
	python src/train.py --model sparse_gat --epochs 100 --batch 64 --graph-k 4 --threshold 0.1

train-deit:
	python src/train.py --model deit --epochs 100 --batch 128

eval-all:
	python src/evaluate.py --model vit        --checkpoint results/vit/best.pt
	python src/evaluate.py --model gat_vit    --checkpoint results/gat_vit/best.pt
	python src/evaluate.py --model sparse_gat --checkpoint results/sparse_gat/best.pt
	python src/evaluate.py --model deit       --checkpoint results/deit/best.pt

viz:
	python src/visualize.py --mode tsne      --model sparse_gat --checkpoint results/sparse_gat/best.pt
	python src/visualize.py --mode attention --model vit        --checkpoint results/vit/best.pt
	python src/visualize.py --mode curves    --model sparse_gat --log results/sparse_gat/train_log.csv

results:
	python results/generate_results.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
