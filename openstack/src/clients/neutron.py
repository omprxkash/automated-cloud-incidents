from __future__ import annotations

from typing import Any, List, Optional, Union

from src.clients.session import get_connection
from src.mock.mock_cloud import MockCloud


class NeutronClient:
    """Wrapper around Neutron (networking) operations."""

    def __init__(self, conn: Optional[Any] = None, mock: bool = False) -> None:
        self.conn: Union[MockCloud, Any] = conn or get_connection(mock=mock)

    def list_networks(self) -> List[dict]:
        """Return all networks visible to the project."""
        networks = self.conn.list_networks()
        return [_normalise_network(n) for n in networks]

    def get_network(self, network_id: str) -> Optional[dict]:
        """Fetch a single network by ID."""
        n = self.conn.get_network(network_id)
        return _normalise_network(n) if n else None

    def create_network(self, name: str) -> dict:
        """Create a tenant network."""
        net = self.conn.create_network(name=name)
        return _normalise_network(net)

    def create_subnet(
        self,
        network_id: str,
        name: str,
        cidr: str,
        ip_version: int = 4,
    ) -> dict:
        """Attach a subnet to an existing network."""
        subnet = self.conn.create_subnet(
            network_id=network_id,
            name=name,
            cidr=cidr,
            ip_version=ip_version,
        )
        return _normalise_subnet(subnet)

    def create_router(self, name: str, subnet_id: Optional[str] = None) -> dict:
        """Create a router and optionally attach a subnet interface."""
        router = self.conn.create_router(name=name)
        router_id = router["id"] if isinstance(router, dict) else router.id
        if subnet_id:
            self.conn.add_router_interface(router_id, subnet_id)
        return _normalise_router(router)

    def add_floating_ip(self, server_id: str, network: str = "public") -> str:
        """Allocate a floating IP and associate it with a server."""
        fip = self.conn.create_floating_ip(network=network)
        ip_addr = fip["floating_ip_address"] if isinstance(fip, dict) else fip.floating_ip_address
        self.conn.add_floating_ip_to_server(server_id, ip_addr)
        return ip_addr


def _normalise_network(n: Any) -> dict:
    if isinstance(n, dict):
        return n
    return {"id": n.id, "name": n.name, "status": getattr(n, "status", "ACTIVE")}


def _normalise_subnet(s: Any) -> dict:
    if isinstance(s, dict):
        return s
    return {"id": s.id, "name": s.name, "network_id": s.network_id, "cidr": s.cidr}


def _normalise_router(r: Any) -> dict:
    if isinstance(r, dict):
        return r
    return {"id": r.id, "name": r.name, "status": getattr(r, "status", "ACTIVE")}
