"""Create a volume, launch a server, and attach the volume to it.

Run offline:
    OPENSTACK_MOCK=1 python examples/attach_volume.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.clients.cinder import CinderClient
from src.clients.nova import NovaClient
from src.clients.session import get_connection

MOCK = os.environ.get("OPENSTACK_MOCK", "1") in ("1", "true", "yes")

conn = get_connection(mock=MOCK)
nova = NovaClient(conn=conn)
cinder = CinderClient(conn=conn)

print("Creating volume…")
vol = cinder.create_volume(name="data-disk", size=20)
print(f"  Volume: {vol['id']} — {vol['size']} GiB, {vol['status']}")

print("Launching server…")
server = nova.create_server(
    name="db1",
    image="ubuntu-22.04",
    flavor="m1.medium",
    network="private",
)
print(f"  Server: {server['id']} — {server['status']}")

print("Attaching volume to server…")
result = cinder.attach_volume(server_id=server["id"], volume_id=vol["id"])
print(f"  Volume status: {result['status']}")

print("Taking a snapshot…")
snap = cinder.snapshot_volume(volume_id=vol["id"], name="data-disk-snap-01")
print(f"  Snapshot: {snap['id']}")

print("\nAll volumes:")
for v in cinder.list_volumes():
    print(f"  {v['id'][:8]}  {v['name']}  {v['size']} GiB  [{v['status']}]")

print("Done.")
