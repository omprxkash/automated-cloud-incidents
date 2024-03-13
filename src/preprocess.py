"""CIFAR-100 data pipeline: augmentation, normalization, and DataLoader factory."""

import torch
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms


CIFAR100_MEAN = (0.5071, 0.4867, 0.4408)
CIFAR100_STD  = (0.2675, 0.2565, 0.2761)


def build_train_transform(input_size: int = 128) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.RandomCrop(input_size, padding=input_size // 8),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
        transforms.AutoAugment(policy=transforms.AutoAugmentPolicy.CIFAR10),
        transforms.ToTensor(),
        transforms.Normalize(CIFAR100_MEAN, CIFAR100_STD),
    ])


def build_eval_transform(input_size: int = 128) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize(CIFAR100_MEAN, CIFAR100_STD),
    ])


def get_dataloaders(
    data_root: str = "./data",
    input_size: int = 128,
    batch_size: int = 128,
    num_workers: int = 4,
    val_split: float = 0.1,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Return (train_loader, val_loader, test_loader) for CIFAR-100."""
    train_ds_full = datasets.CIFAR100(
        root=data_root, train=True, download=True,
        transform=build_train_transform(input_size),
    )
    val_size  = int(len(train_ds_full) * val_split)
    train_size = len(train_ds_full) - val_size
    rng = torch.Generator().manual_seed(seed)
    train_ds, val_ds_raw = random_split(train_ds_full, [train_size, val_size], generator=rng)

    # val uses eval transform — wrap with a fresh dataset instance
    val_base = datasets.CIFAR100(
        root=data_root, train=True, download=False,
        transform=build_eval_transform(input_size),
    )
    val_ds = torch.utils.data.Subset(val_base, val_ds_raw.indices)

    test_ds = datasets.CIFAR100(
        root=data_root, train=False, download=True,
        transform=build_eval_transform(input_size),
    )

    loader_kwargs = dict(batch_size=batch_size, num_workers=num_workers, pin_memory=True)
    train_loader = DataLoader(train_ds, shuffle=True,  **loader_kwargs)
    val_loader   = DataLoader(val_ds,   shuffle=False, **loader_kwargs)
    test_loader  = DataLoader(test_ds,  shuffle=False, **loader_kwargs)

    return train_loader, val_loader, test_loader


def get_class_names(data_root: str = "./data") -> list[str]:
    ds = datasets.CIFAR100(root=data_root, train=False, download=True)
    return ds.classes
