"""List all resources across Nova, Neutron, Cinder, and Swift at once.

Run offline:
    OPENSTACK_MOCK=1 python examples/list_resources.py

Useful as a quick status overview of everything in a project.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.clients.cinder import CinderClient
from src.clients.neutron import NeutronClient
from src.clients.nova import NovaClient
from src.clients.swift import SwiftClient
from src.clients.session import get_connection

MOCK = os.environ.get("OPENSTACK_MOCK", "1") in ("1", "true", "yes")

conn = get_connection(mock=MOCK)

print("=== Servers ===")
for s in NovaClient(conn=conn).list_servers():
    print(f"  {s['id'][:8]}  {s['name']}  [{s['status']}]")

print("\n=== Networks ===")
for n in NeutronClient(conn=conn).list_networks():
    print(f"  {n['id'][:8]}  {n['name']}  [{n.get('status', '')}]")

print("\n=== Volumes ===")
for v in CinderClient(conn=conn).list_volumes():
    print(f"  {v['id'][:8]}  {v['name']}  {v['size']} GiB  [{v['status']}]")

print("\n=== Containers ===")
for c in SwiftClient(conn=conn).list_containers():
    print(f"  {c['name']}  ({c.get('count', 0)} objects)")

print("\nDone.")
