"""Create an object storage container and upload a file to it.

Run offline:
    OPENSTACK_MOCK=1 python examples/upload_object.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.clients.swift import SwiftClient

MOCK = os.environ.get("OPENSTACK_MOCK", "1") in ("1", "true", "yes")

swift = SwiftClient(mock=MOCK)

print("Creating container 'backups'…")
container = swift.create_container(name="backups")
print(f"  Container: {container['name']}")

# Write a small temp file to upload
with tempfile.NamedTemporaryFile(suffix=".sql", delete=False, mode="w") as fh:
    fh.write("-- mock database dump\nSELECT 1;\n")
    tmp_path = fh.name

print(f"Uploading {tmp_path}…")
obj = swift.upload_file(container="backups", file_path=tmp_path, object_name="dump.sql")
print(f"  Uploaded: {obj['name']} ({obj['bytes']} bytes)")

print("\nObjects in 'backups':")
for o in swift.list_objects(container="backups"):
    print(f"  {o['name']} — {o['bytes']} bytes")

print("\nAll containers:")
for c in swift.list_containers():
    print(f"  {c['name']}  ({c.get('count', 0)} objects, {c.get('bytes', 0)} bytes)")

os.unlink(tmp_path)
print("Done.")
