from __future__ import annotations

from typing import Any, List, Optional, Union

from src.clients.session import get_connection
from src.mock.mock_cloud import MockCloud


class CinderClient:
    """Wrapper around Cinder (block storage) operations."""

    def __init__(self, conn: Optional[Any] = None, mock: bool = False) -> None:
        self.conn: Union[MockCloud, Any] = conn or get_connection(mock=mock)

    def list_volumes(self) -> List[dict]:
        """Return all volumes in the project."""
        vols = self.conn.list_volumes()
        return [_normalise_volume(v) for v in vols]

    def get_volume(self, volume_id: str) -> Optional[dict]:
        """Fetch a volume by ID."""
        v = self.conn.get_volume(volume_id)
        return _normalise_volume(v) if v else None

    def create_volume(self, name: str, size: int) -> dict:
        """Create a block volume of the given size (GiB)."""
        vol = self.conn.create_volume(name=name, size=size)
        return _normalise_volume(vol)

    def attach_volume(self, server_id: str, volume_id: str) -> dict:
        """Attach a volume to a running server."""
        vol = self.conn.attach_volume(server_id=server_id, volume_id=volume_id)
        return _normalise_volume(vol)

    def snapshot_volume(self, volume_id: str, name: str) -> dict:
        """Take a point-in-time snapshot of a volume."""
        snap = self.conn.create_volume_snapshot(volume_id=volume_id, name=name)
        return _normalise_snapshot(snap)

    def delete_volume(self, volume_id: str) -> None:
        """Delete a volume (must be detached first)."""
        self.conn.delete_volume(volume_id)


def _normalise_volume(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    return {
        "id": v.id,
        "name": v.name,
        "size": v.size,
        "status": v.status,
        "attachments": getattr(v, "attachments", []),
    }


def _normalise_snapshot(s: Any) -> dict:
    if isinstance(s, dict):
        return s
    return {"id": s.id, "name": s.name, "volume_id": s.volume_id, "status": s.status}
