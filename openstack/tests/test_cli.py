"""CLI smoke tests using Click's test runner (all in mock mode)."""
from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def invoke(runner: CliRunner, *args: str) -> "click.testing.Result":
    return runner.invoke(cli, ["--mock"] + list(args), catch_exceptions=False)


# ---- server ----

def test_server_list_empty(runner: CliRunner) -> None:
    result = invoke(runner, "server", "list")
    assert result.exit_code == 0
    assert "No servers found" in result.output


def test_server_create_and_list(runner: CliRunner) -> None:
    # Can't share state across invocations with the runner, so just check create succeeds
    result = invoke(runner, "server", "create",
                    "--name", "web1",
                    "--image", "ubuntu-22.04",
                    "--flavor", "m1.small",
                    "--network", "private")
    assert result.exit_code == 0
    assert "created" in result.output.lower()


# ---- network ----

def test_network_list_empty(runner: CliRunner) -> None:
    result = invoke(runner, "network", "list")
    assert result.exit_code == 0
    assert "No networks found" in result.output


def test_network_create(runner: CliRunner) -> None:
    result = invoke(runner, "network", "create", "--name", "private", "--cidr", "10.0.0.0/24")
    assert result.exit_code == 0
    assert "Network created" in result.output
    assert "Subnet created" in result.output


# ---- volume ----

def test_volume_list_empty(runner: CliRunner) -> None:
    result = invoke(runner, "volume", "list")
    assert result.exit_code == 0
    assert "No volumes found" in result.output


def test_volume_create(runner: CliRunner) -> None:
    result = invoke(runner, "volume", "create", "--name", "data", "--size", "10")
    assert result.exit_code == 0
    assert "Volume created" in result.output


# ---- object ----

def test_object_list_empty(runner: CliRunner) -> None:
    result = invoke(runner, "object", "list", "backups")
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_object_upload(runner: CliRunner, tmp_path) -> None:
    test_file = tmp_path / "dump.sql"
    test_file.write_text("SELECT 1;")
    result = invoke(runner, "object", "upload",
                    "--container", "backups",
                    "--file", str(test_file))
    assert result.exit_code == 0
    assert "Uploaded" in result.output
