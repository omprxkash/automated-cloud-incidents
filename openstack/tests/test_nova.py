"""Tests for the Nova compute wrapper (runs against MockCloud)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.clients.nova import NovaClient
from src.mock.mock_cloud import MockCloud


@pytest.fixture
def nova() -> NovaClient:
    return NovaClient(conn=MockCloud())


def test_list_servers_empty(nova: NovaClient) -> None:
    assert nova.list_servers() == []


def test_create_server_returns_active(nova: NovaClient) -> None:
    server = nova.create_server(
        name="test-vm",
        image="ubuntu-22.04",
        flavor="m1.small",
        network="private",
    )
    assert server["name"] == "test-vm"
    assert server["status"] == "ACTIVE"
    assert "id" in server


def test_list_servers_after_create(nova: NovaClient) -> None:
    nova.create_server("vm1", "ubuntu-22.04", "m1.small", "private")
    nova.create_server("vm2", "ubuntu-22.04", "m1.small", "private")
    servers = nova.list_servers()
    assert len(servers) == 2
    names = {s["name"] for s in servers}
    assert names == {"vm1", "vm2"}


def test_delete_server(nova: NovaClient) -> None:
    server = nova.create_server("del-me", "ubuntu-22.04", "m1.small", "private")
    nova.delete_server(server["id"])
    assert nova.list_servers() == []


def test_get_console(nova: NovaClient) -> None:
    server = nova.create_server("console-vm", "ubuntu-22.04", "m1.small", "private")
    output = nova.get_console(server["id"])
    assert isinstance(output, str)
    assert len(output) > 0


def test_delete_nonexistent_server_is_noop(nova: NovaClient) -> None:
    nova.delete_server("does-not-exist")  # should not raise


def test_list_servers_by_status(nova: NovaClient) -> None:
    nova.create_server("active-vm", "ubuntu-22.04", "m1.small", "private")
    active = nova.list_servers_by_status("ACTIVE")
    assert len(active) == 1
    assert all(s["status"] == "ACTIVE" for s in active)
    error = nova.list_servers_by_status("ERROR")
    assert error == []


def test_get_server_returns_none_for_missing(nova: NovaClient) -> None:
    result = nova.get_server("nonexistent-id")
    assert result is None


def test_get_server_returns_server(nova: NovaClient) -> None:
    created = nova.create_server("lookup-vm", "img", "m1.small", "net")
    found = nova.get_server(created["id"])
    assert found is not None
    assert found["name"] == "lookup-vm"
