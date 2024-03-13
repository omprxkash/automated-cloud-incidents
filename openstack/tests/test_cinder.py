"""Tests for the Cinder block storage wrapper (runs against MockCloud)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.clients.cinder import CinderClient
from src.clients.nova import NovaClient
from src.mock.mock_cloud import MockCloud


@pytest.fixture
def cloud() -> MockCloud:
    return MockCloud()


@pytest.fixture
def cinder(cloud: MockCloud) -> CinderClient:
    return CinderClient(conn=cloud)


@pytest.fixture
def nova(cloud: MockCloud) -> NovaClient:
    return NovaClient(conn=cloud)


def test_list_volumes_empty(cinder: CinderClient) -> None:
    assert cinder.list_volumes() == []


def test_create_volume(cinder: CinderClient) -> None:
    vol = cinder.create_volume(name="data", size=50)
    assert vol["name"] == "data"
    assert vol["size"] == 50
    assert vol["status"] == "available"


def test_list_volumes_after_create(cinder: CinderClient) -> None:
    cinder.create_volume("vol-a", 10)
    cinder.create_volume("vol-b", 20)
    assert len(cinder.list_volumes()) == 2


def test_attach_volume(cinder: CinderClient, nova: NovaClient) -> None:
    server = nova.create_server("db1", "ubuntu-22.04", "m1.medium", "private")
    vol = cinder.create_volume("db-data", 100)
    result = cinder.attach_volume(server_id=server["id"], volume_id=vol["id"])
    assert result["status"] == "in-use"
    assert any(a["server_id"] == server["id"] for a in result["attachments"])


def test_snapshot_volume(cinder: CinderClient) -> None:
    vol = cinder.create_volume("snap-me", 30)
    snap = cinder.snapshot_volume(volume_id=vol["id"], name="snap-01")
    assert snap["name"] == "snap-01"
    assert snap["volume_id"] == vol["id"]
    assert snap["status"] == "available"


def test_delete_volume(cinder: CinderClient) -> None:
    vol = cinder.create_volume("delete-me", 5)
    cinder.delete_volume(vol["id"])
    assert cinder.list_volumes() == []


def test_attach_missing_volume_raises(cinder: CinderClient) -> None:
    with pytest.raises(KeyError):
        cinder.attach_volume(server_id="any", volume_id="does-not-exist")


def test_get_volume_returns_none_for_missing(cinder: CinderClient) -> None:
    assert cinder.get_volume("nonexistent") is None


def test_get_volume_returns_volume(cinder: CinderClient) -> None:
    vol = cinder.create_volume("findme", 5)
    found = cinder.get_volume(vol["id"])
    assert found is not None
    assert found["name"] == "findme"


def test_multiple_snapshots_of_same_volume(cinder: CinderClient) -> None:
    vol = cinder.create_volume("snap-vol", 10)
    s1 = cinder.snapshot_volume(vol["id"], "snap-a")
    s2 = cinder.snapshot_volume(vol["id"], "snap-b")
    assert s1["id"] != s2["id"]
    assert s1["volume_id"] == s2["volume_id"] == vol["id"]
