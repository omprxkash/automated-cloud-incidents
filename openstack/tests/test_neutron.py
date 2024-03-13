"""Tests for the Neutron networking wrapper (runs against MockCloud)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.clients.neutron import NeutronClient
from src.mock.mock_cloud import MockCloud


@pytest.fixture
def neutron() -> NeutronClient:
    return NeutronClient(conn=MockCloud())


def test_list_networks_empty(neutron: NeutronClient) -> None:
    assert neutron.list_networks() == []


def test_create_network(neutron: NeutronClient) -> None:
    net = neutron.create_network(name="private")
    assert net["name"] == "private"
    assert "id" in net
    assert net["status"] == "ACTIVE"


def test_list_networks_after_create(neutron: NeutronClient) -> None:
    neutron.create_network("net-a")
    neutron.create_network("net-b")
    networks = neutron.list_networks()
    assert len(networks) == 2


def test_create_subnet(neutron: NeutronClient) -> None:
    net = neutron.create_network("test-net")
    subnet = neutron.create_subnet(
        network_id=net["id"],
        name="test-subnet",
        cidr="192.168.1.0/24",
    )
    assert subnet["cidr"] == "192.168.1.0/24"
    assert subnet["network_id"] == net["id"]


def test_create_router(neutron: NeutronClient) -> None:
    net = neutron.create_network("test-net")
    subnet = neutron.create_subnet(net["id"], "test-subnet", "10.0.1.0/24")
    router = neutron.create_router(name="test-router", subnet_id=subnet["id"])
    assert router["name"] == "test-router"
    assert "id" in router


def test_add_floating_ip(neutron: NeutronClient) -> None:
    fip = neutron.add_floating_ip(server_id="fake-server-id")
    assert "." in fip  # looks like an IP


def test_get_network_returns_none_for_missing(neutron: NeutronClient) -> None:
    assert neutron.get_network("nonexistent-id") is None


def test_get_network_returns_network(neutron: NeutronClient) -> None:
    net = neutron.create_network("findme")
    found = neutron.get_network(net["id"])
    assert found is not None
    assert found["name"] == "findme"


def test_create_multiple_subnets_on_same_network(neutron: NeutronClient) -> None:
    net = neutron.create_network("multi-subnet")
    s1 = neutron.create_subnet(net["id"], "s1", "10.1.0.0/24")
    s2 = neutron.create_subnet(net["id"], "s2", "10.2.0.0/24")
    assert s1["id"] != s2["id"]
    assert s1["cidr"] != s2["cidr"]
