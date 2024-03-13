"""Create a network + subnet and attach a router.

Run offline:
    OPENSTACK_MOCK=1 python examples/create_network.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.clients.neutron import NeutronClient

MOCK = os.environ.get("OPENSTACK_MOCK", "1") in ("1", "true", "yes")

neutron = NeutronClient(mock=MOCK)

print("Creating network…")
net = neutron.create_network(name="private")
print(f"  Network: {net['id']}")

print("Creating subnet 10.0.0.0/24…")
subnet = neutron.create_subnet(
    network_id=net["id"],
    name="private-subnet",
    cidr="10.0.0.0/24",
)
print(f"  Subnet: {subnet['id']} ({subnet['cidr']})")

print("Creating router and attaching subnet…")
router = neutron.create_router(name="main-router", subnet_id=subnet["id"])
print(f"  Router: {router['id']}")

print("\nAll networks:")
for n in neutron.list_networks():
    print(f"  {n['id'][:8]}… {n['name']} [{n.get('status', '')}]")
