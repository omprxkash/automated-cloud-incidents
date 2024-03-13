"""Tests for the Swift object storage wrapper (runs against MockCloud)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENSTACK_MOCK", "1")

from src.clients.swift import SwiftClient
from src.mock.mock_cloud import MockCloud


@pytest.fixture
def swift() -> SwiftClient:
    return SwiftClient(conn=MockCloud())


def test_create_container(swift: SwiftClient) -> None:
    container = swift.create_container(name="backups")
    assert container["name"] == "backups"
    assert container["count"] == 0


def test_list_objects_empty(swift: SwiftClient) -> None:
    swift.create_container("logs")
    assert swift.list_objects("logs") == []


def test_upload_and_list_objects(swift: SwiftClient) -> None:
    swift.create_container("data")
    swift.upload_object("data", "file1.txt", b"hello")
    swift.upload_object("data", "file2.txt", b"world!")
    objects = swift.list_objects("data")
    assert len(objects) == 2
    names = {o["name"] for o in objects}
    assert names == {"file1.txt", "file2.txt"}


def test_upload_updates_byte_count(swift: SwiftClient) -> None:
    swift.create_container("metrics")
    swift.upload_object("metrics", "data.bin", b"A" * 1024)
    obj = swift.list_objects("metrics")[0]
    assert obj["bytes"] == 1024


def test_download_object(swift: SwiftClient) -> None:
    swift.create_container("bucket")
    swift.upload_object("bucket", "readme.txt", b"readme content")
    data = swift.download_object("bucket", "readme.txt")
    assert isinstance(data, bytes)


def test_download_missing_raises(swift: SwiftClient) -> None:
    swift.create_container("empty")
    with pytest.raises(KeyError):
        swift.download_object("empty", "missing.txt")


def test_delete_object(swift: SwiftClient) -> None:
    swift.create_container("trash")
    swift.upload_object("trash", "file.txt", b"data")
    swift.delete_object("trash", "file.txt")
    assert swift.list_objects("trash") == []


def test_upload_auto_creates_container(swift: SwiftClient) -> None:
    # Uploading to a non-existent container should auto-create it
    swift.upload_object("auto-bucket", "obj.txt", b"auto")
    objects = swift.list_objects("auto-bucket")
    assert len(objects) == 1


def test_get_container(swift: SwiftClient) -> None:
    swift.create_container("mycontainer")
    c = swift.get_container("mycontainer")
    assert c is not None
    assert c["name"] == "mycontainer"


def test_list_containers(swift: SwiftClient) -> None:
    swift.create_container("a")
    swift.create_container("b")
    containers = swift.list_containers()
    assert len(containers) == 2
