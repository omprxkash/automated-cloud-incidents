from __future__ import annotations

from typing import Any, List, Optional, Union

from src.clients.session import get_connection
from src.mock.mock_cloud import MockCloud


class NovaClient:
    """Wrapper around Nova (compute) operations."""

    def __init__(self, conn: Optional[Any] = None, mock: bool = False) -> None:
        self.conn: Union[MockCloud, Any] = conn or get_connection(mock=mock)

    def list_servers(self) -> List[dict]:
        """Return all servers in the project."""
        servers = self.conn.list_servers()
        return [_normalise_server(s) for s in servers]

    def get_server(self, server_id: str) -> Optional[dict]:
        """Fetch a single server by ID."""
        s = self.conn.get_server(server_id)
        return _normalise_server(s) if s else None

    def create_server(
        self,
        name: str,
        image: str,
        flavor: str,
        network: str,
        *,
        wait: bool = True,
    ) -> dict:
        """Boot a new server and wait for it to become ACTIVE."""
        server = self.conn.create_server(
            name=name,
            image=image,
            flavor=flavor,
            network=network,
            wait=wait,
        )
        return _normalise_server(server)

    def delete_server(self, server_id: str, *, wait: bool = True) -> None:
        """Terminate a server."""
        self.conn.delete_server(server_id, wait=wait)

    def get_console(self, server_id: str) -> str:
        """Fetch the serial console output for a server."""
        return self.conn.get_server_console_output(server_id)

    def list_servers_by_status(self, status: str) -> List[dict]:
        """Return only servers matching the given status (e.g. ACTIVE, ERROR)."""
        return [s for s in self.list_servers() if s.get("status") == status]


def _normalise_server(s: Any) -> dict:
    if isinstance(s, dict):
        return s
    return {
        "id": s.id,
        "name": s.name,
        "status": s.status,
        "image": (
            getattr(s, "image", {}).get("name", "")
            if isinstance(getattr(s, "image", None), dict)
            else str(getattr(s, "image", ""))
        ),
        "flavor": (
            getattr(s, "flavor", {}).get("name", "")
            if isinstance(getattr(s, "flavor", None), dict)
            else str(getattr(s, "flavor", ""))
        ),
        "addresses": s.addresses or {},
    }
