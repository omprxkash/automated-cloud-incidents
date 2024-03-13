"""Launch a VM using the Nova wrapper.

Run offline:
    OPENSTACK_MOCK=1 python examples/launch_vm.py

Run against a real cloud (set OS_* env vars or configure clouds.yaml first):
    python examples/launch_vm.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.clients.nova import NovaClient

MOCK = os.environ.get("OPENSTACK_MOCK", "1") in ("1", "true", "yes")

nova = NovaClient(mock=MOCK)

print("Existing servers:")
for s in nova.list_servers():
    print(f"  {s['id'][:8]}… {s['name']} [{s['status']}]")

print("\nLaunching web1…")
server = nova.create_server(
    name="web1",
    image="ubuntu-22.04",
    flavor="m1.small",
    network="private",
)
print(f"  Created: {server['id']} — status: {server['status']}")

print("\nConsole output:")
print(nova.get_console(server["id"]))

print("\nAll active servers:")
for s in nova.list_servers_by_status("ACTIVE"):
    print(f"  {s['id'][:8]}  {s['name']}")

print("Done.")
