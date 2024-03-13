"""Tests for the config loader."""
from __future__ import annotations

import os

import pytest

from src.config import Config, load_config


def test_defaults():
    """Config should have sensible defaults when no env vars are set."""
    os.environ.pop("OS_AUTH_URL", None)
    os.environ.pop("OS_PROJECT_NAME", None)
    os.environ.pop("OS_USERNAME", None)
    os.environ.pop("OPENSTACK_MOCK", None)
    cfg = load_config()
    assert cfg.region_name == "RegionOne"
    assert cfg.user_domain_name == "Default"
    assert cfg.project_domain_name == "Default"


def test_mock_flag_from_env(monkeypatch):
    monkeypatch.setenv("OPENSTACK_MOCK", "1")
    cfg = load_config()
    assert cfg.mock is True


def test_mock_flag_false_by_default(monkeypatch):
    monkeypatch.delenv("OPENSTACK_MOCK", raising=False)
    cfg = load_config()
    assert cfg.mock is False


def test_reads_os_vars(monkeypatch):
    monkeypatch.setenv("OS_AUTH_URL", "https://ks.example.com:5000/v3")
    monkeypatch.setenv("OS_PROJECT_NAME", "myproject")
    monkeypatch.setenv("OS_USERNAME", "myuser")
    monkeypatch.setenv("OS_PASSWORD", "secret")
    monkeypatch.setenv("OS_REGION_NAME", "us-east-1")
    monkeypatch.setenv("OPENSTACK_MOCK", "0")
    cfg = load_config()
    assert cfg.auth_url == "https://ks.example.com:5000/v3"
    assert cfg.project_name == "myproject"
    assert cfg.username == "myuser"
    assert cfg.region_name == "us-east-1"
