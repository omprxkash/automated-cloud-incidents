from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Union

from src.clients.session import get_connection
from src.mock.mock_cloud import MockCloud


class SwiftClient:
    """Wrapper around Swift (object storage) operations."""

    def __init__(self, conn: Optional[Any] = None, mock: bool = False) -> None:
        self.conn: Union[MockCloud, Any] = conn or get_connection(mock=mock)

    def list_containers(self) -> List[dict]:
        """Return all containers in the account."""
        containers = self.conn.list_containers()
        return [_normalise_container(c) for c in containers]

    def create_container(self, name: str) -> dict:
        """Create an object storage container (bucket)."""
        container = self.conn.create_container(name=name)
        return _normalise_container(container)

    def get_container(self, name: str) -> Optional[dict]:
        """Fetch container metadata by name."""
        c = self.conn.get_container(name)
        return _normalise_container(c) if c else None

    def list_objects(self, container: str) -> List[dict]:
        """List objects inside a container."""
        objs = self.conn.list_objects(container=container)
        return [_normalise_object(o) for o in objs]

    def upload_object(self, container: str, name: str, data: bytes) -> dict:
        """Upload bytes to a container under the given object name."""
        obj = self.conn.upload_object(container=container, name=name, data=data)
        return _normalise_object(obj)

    def upload_file(self, container: str, file_path: str, object_name: Optional[str] = None) -> dict:
        """Read a local file and upload it to a container."""
        path = Path(file_path)
        key = object_name or path.name
        data = path.read_bytes()
        return self.upload_object(container, key, data)

    def download_object(self, container: str, name: str) -> bytes:
        """Download an object and return its raw bytes."""
        return self.conn.download_object(container=container, name=name)

    def delete_object(self, container: str, name: str) -> None:
        """Remove an object from a container."""
        self.conn.delete_object(container=container, name=name)

    def ensure_container(self, name: str) -> dict:
        """Return an existing container or create it if it doesn't exist."""
        existing = self.get_container(name)
        return existing if existing is not None else self.create_container(name)


def _normalise_container(c: Any) -> dict:
    if isinstance(c, dict):
        return c
    return {"name": c.name, "count": getattr(c, "count", 0), "bytes": getattr(c, "bytes", 0)}


def _normalise_object(o: Any) -> dict:
    if isinstance(o, dict):
        return o
    return {"name": o.name, "bytes": getattr(o, "bytes", 0), "content_type": getattr(o, "content_type", "")}
