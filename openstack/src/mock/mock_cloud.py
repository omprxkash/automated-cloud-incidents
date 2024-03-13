from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional


def _uid() -> str:
    return str(uuid.uuid4())


class MockCloud:
    """In-memory simulation of the OpenStack SDK connection.

    Keeps state in plain dicts so the wrappers and CLI work without a real cloud.
    Method signatures mirror what the SDK wrappers actually call.
    """

    def __init__(self) -> None:
        self._servers: Dict[str, dict] = {}
        self._networks: Dict[str, dict] = {}
        self._subnets: Dict[str, dict] = {}
        self._routers: Dict[str, dict] = {}
        self._floating_ips: Dict[str, dict] = {}
        self._volumes: Dict[str, dict] = {}
        self._snapshots: Dict[str, dict] = {}
        self._containers: Dict[str, dict] = {}
        self._objects: Dict[str, Dict[str, dict]] = {}

    # ------------------------------------------------------------------ Nova
    def list_servers(self) -> List[dict]:
        return list(self._servers.values())

    def create_server(
        self,
        name: str,
        image: str,
        flavor: str,
        network: str,
        *,
        wait: bool = True,
        **_: Any,
    ) -> dict:
        server = {
            "id": _uid(),
            "name": name,
            "image": image,
            "flavor": flavor,
            "network": network,
            "status": "ACTIVE",
            "addresses": {network: [{"addr": f"10.0.0.{len(self._servers) + 10}", "version": 4}]},
        }
        self._servers[server["id"]] = server
        return server

    def get_server(self, server_id: str) -> Optional[dict]:
        return self._servers.get(server_id)

    def delete_server(self, server_id: str, *, wait: bool = True) -> None:
        self._servers.pop(server_id, None)

    def get_server_console_output(self, server_id: str) -> str:
        if server_id not in self._servers:
            raise KeyError(f"Server {server_id!r} not found")
        name = self._servers[server_id]["name"]
        return (
            f"[    0.000000] Booting {name}\n"
            f"[    1.234567] systemd[1]: Started.\n"
            f"[mock console output for {name}]\n"
        )

    # --------------------------------------------------------------- Neutron
    def list_networks(self) -> List[dict]:
        return list(self._networks.values())

    def create_network(self, name: str, **_: Any) -> dict:
        net = {"id": _uid(), "name": name, "status": "ACTIVE"}
        self._networks[net["id"]] = net
        return net

    def get_network(self, network_id: str) -> Optional[dict]:
        return self._networks.get(network_id)

    def create_subnet(
        self,
        network_id: str,
        name: str,
        cidr: str,
        ip_version: int = 4,
        **_: Any,
    ) -> dict:
        subnet = {
            "id": _uid(),
            "name": name,
            "network_id": network_id,
            "cidr": cidr,
            "ip_version": ip_version,
        }
        self._subnets[subnet["id"]] = subnet
        return subnet

    def create_router(self, name: str, **_: Any) -> dict:
        router = {"id": _uid(), "name": name, "status": "ACTIVE"}
        self._routers[router["id"]] = router
        return router

    def add_router_interface(self, router_id: str, subnet_id: str) -> dict:
        return {"router_id": router_id, "subnet_id": subnet_id}

    def create_floating_ip(self, network: str = "public", **_: Any) -> dict:
        fip = {
            "id": _uid(),
            "floating_ip_address": f"203.0.113.{len(self._floating_ips) + 1}",
            "network": network,
            "status": "DOWN",
        }
        self._floating_ips[fip["id"]] = fip
        return fip

    def add_floating_ip_to_server(self, server_id: str, floating_ip: str) -> None:
        if server_id in self._servers:
            addrs = self._servers[server_id].setdefault("addresses", {})
            addrs.setdefault("public", []).append({"addr": floating_ip, "version": 4})

    # --------------------------------------------------------------- Cinder
    def list_volumes(self) -> List[dict]:
        return list(self._volumes.values())

    def create_volume(self, name: str, size: int, **_: Any) -> dict:
        vol = {
            "id": _uid(),
            "name": name,
            "size": size,
            "status": "available",
            "attachments": [],
        }
        self._volumes[vol["id"]] = vol
        return vol

    def get_volume(self, volume_id: str) -> Optional[dict]:
        return self._volumes.get(volume_id)

    def attach_volume(self, server_id: str, volume_id: str, **_: Any) -> dict:
        if volume_id not in self._volumes:
            raise KeyError(f"Volume {volume_id!r} not found")
        self._volumes[volume_id]["status"] = "in-use"
        self._volumes[volume_id]["attachments"].append({"server_id": server_id})
        return self._volumes[volume_id]

    def create_volume_snapshot(self, volume_id: str, name: str, **_: Any) -> dict:
        snap = {
            "id": _uid(),
            "name": name,
            "volume_id": volume_id,
            "status": "available",
        }
        self._snapshots[snap["id"]] = snap
        return snap

    def delete_volume(self, volume_id: str, **_: Any) -> None:
        self._volumes.pop(volume_id, None)

    # --------------------------------------------------------------- Swift
    def list_containers(self) -> List[dict]:
        return list(self._containers.values())

    def create_container(self, name: str, **_: Any) -> dict:
        container = {"name": name, "count": 0, "bytes": 0}
        self._containers[name] = container
        self._objects[name] = {}
        return container

    def get_container(self, name: str) -> Optional[dict]:
        return self._containers.get(name)

    def list_objects(self, container: str) -> List[dict]:
        return list(self._objects.get(container, {}).values())

    def upload_object(self, container: str, name: str, data: bytes, **_: Any) -> dict:
        if container not in self._containers:
            self.create_container(container)
        obj = {"name": name, "bytes": len(data), "content_type": "application/octet-stream"}
        self._objects[container][name] = obj
        self._containers[container]["count"] = len(self._objects[container])
        self._containers[container]["bytes"] += len(data)
        return obj

    def download_object(self, container: str, name: str) -> bytes:
        if container not in self._objects or name not in self._objects[container]:
            raise KeyError(f"{container}/{name} not found")
        return b"[mock content]"

    def delete_object(self, container: str, name: str) -> None:
        if container in self._objects:
            self._objects[container].pop(name, None)
