"""Direct tests for MockCloud internals."""
from __future__ import annotations

import pytest

from src.mock.mock_cloud import MockCloud


@pytest.fixture
def cloud() -> MockCloud:
    return MockCloud()


def test_floating_ip_association(cloud: MockCloud) -> None:
    server = cloud.create_server("s1", "img", "flavor", "net")
    fip = cloud.create_floating_ip()
    cloud.add_floating_ip_to_server(server["id"], fip["floating_ip_address"])
    updated = cloud.get_server(server["id"])
    public_addrs = updated["addresses"].get("public", [])
    assert any(a["addr"] == fip["floating_ip_address"] for a in public_addrs)


def test_multiple_floating_ips_unique(cloud: MockCloud) -> None:
    fip1 = cloud.create_floating_ip()
    fip2 = cloud.create_floating_ip()
    assert fip1["floating_ip_address"] != fip2["floating_ip_address"]


def test_console_output_contains_name(cloud: MockCloud) -> None:
    server = cloud.create_server("myvm", "img", "flavor", "net")
    output = cloud.get_server_console_output(server["id"])
    assert "myvm" in output


def test_console_raises_for_missing(cloud: MockCloud) -> None:
    with pytest.raises(KeyError):
        cloud.get_server_console_output("nonexistent")


def test_volume_byte_tracking(cloud: MockCloud) -> None:
    cloud.create_container("c")
    cloud.upload_object("c", "a.txt", b"hello")
    cloud.upload_object("c", "b.txt", b"world!")
    assert cloud._containers["c"]["bytes"] == 11
    assert cloud._containers["c"]["count"] == 2


def test_subnet_stored_correctly(cloud: MockCloud) -> None:
    net = cloud.create_network("test-net")
    subnet = cloud.create_subnet(net["id"], "test-subnet", "172.16.0.0/16")
    assert subnet["network_id"] == net["id"]
    assert subnet["cidr"] == "172.16.0.0/16"
