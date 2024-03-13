from setuptools import setup, find_packages

setup(
    name="gat-vit",
    version="0.1.0",
    author="Omprakash Pugazhendhi",
    author_email="omprakash.2021@vitstudent.ac.in",
    description="Graph-attention Vision Transformers for CIFAR-100 classification",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "torch>=2.1.0",
        "torchvision>=0.16.0",
        "timm>=0.9.12",
        "torch-geometric>=2.4.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "scikit-learn>=1.3.2",
        "numpy>=1.26.0",
        "pandas>=2.1.0",
        "pyyaml>=6.0.1",
        "tqdm>=4.66.1",
        "networkx>=3.2.1",
    ],
)
