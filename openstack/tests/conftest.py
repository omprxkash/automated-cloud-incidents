"""Shared pytest fixtures."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.mock.mock_cloud import MockCloud


@pytest.fixture
def cloud() -> MockCloud:
    """A fresh MockCloud instance per test."""
    return MockCloud()
