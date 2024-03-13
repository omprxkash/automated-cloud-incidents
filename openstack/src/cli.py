"""osctl -- command-line interface for the OpenStack automation toolkit."""
from __future__ import annotations

import os
import sys

import click
from rich.console import Console
from rich.table import Table

from src.clients.cinder import CinderClient
from src.clients.neutron import NeutronClient
from src.clients.nova import NovaClient
from src.clients.swift import SwiftClient

console = Console()


def _is_mock(ctx_mock: bool) -> bool:
    return ctx_mock or os.environ.get("OPENSTACK_MOCK", "0").strip() in ("1", "true", "yes")


@click.group()
@click.option("--mock", is_flag=True, default=False, help="Run in mock/offline mode (no real cloud needed).")
@click.pass_context
def cli(ctx: click.Context, mock: bool) -> None:
    """osctl -- manage OpenStack resources from the terminal."""
    ctx.ensure_object(dict)
    ctx.obj["mock"] = mock


# ------------------------------------------------------------------ server
@cli.group()
def server() -> None:
    """Manage compute servers (Nova)."""


@server.command("list")
@click.pass_context
def server_list(ctx: click.Context) -> None:
    """List all servers in the project."""
    nova = NovaClient(mock=_is_mock(ctx.obj["mock"]))
    servers = nova.list_servers()

    table = Table(title="Servers", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Image")
    table.add_column("Flavor")

    for s in servers:
        table.add_row(
            str(s.get("id", "")),
            str(s.get("name", "")),
            str(s.get("status", "")),
            str(s.get("image", "")),
            str(s.get("flavor", "")),
        )

    if not servers:
        console.print("[yellow]No servers found.[/yellow]")
    else:
        console.print(table)


@server.command("show")
@click.argument("server_id")
@click.pass_context
def server_show(ctx: click.Context, server_id: str) -> None:
    """Show details for a single server."""
    nova = NovaClient(mock=_is_mock(ctx.obj["mock"]))
    s = nova.get_server(server_id)
    if not s:
        console.print(f"[red]Server {server_id!r} not found.[/red]")
        sys.exit(1)
    for k, v in s.items():
        console.print(f"[bold]{k}[/bold]: {v}")


@server.command("create")
@click.option("--name", required=True, help="Server name.")
@click.option("--image", required=True, help="Image name or ID.")
@click.option("--flavor", required=True, help="Flavor name or ID.")
@click.option("--network", required=True, help="Network name or ID to attach.")
@click.pass_context
def server_create(ctx: click.Context, name: str, image: str, flavor: str, network: str) -> None:
    """Boot a new server."""
    nova = NovaClient(mock=_is_mock(ctx.obj["mock"]))
    console.print(f"[cyan]Creating server [bold]{name}[/bold]...[/cyan]")
    server = nova.create_server(name=name, image=image, flavor=flavor, network=network)
    console.print(f"[green]Server created:[/green] {server['id']} ({server['status']})")


@server.command("delete")
@click.argument("server_id")
@click.pass_context
def server_delete(ctx: click.Context, server_id: str) -> None:
    """Terminate a server by ID."""
    nova = NovaClient(mock=_is_mock(ctx.obj["mock"]))
    nova.delete_server(server_id)
    console.print(f"[green]Server {server_id} deleted.[/green]")


@server.command("console")
@click.argument("server_id")
@click.pass_context
def server_console(ctx: click.Context, server_id: str) -> None:
    """Print the serial console output of a server."""
    nova = NovaClient(mock=_is_mock(ctx.obj["mock"]))
    output = nova.get_console(server_id)
    console.print(output)


# ------------------------------------------------------------------ network
@cli.group()
def network() -> None:
    """Manage networks and subnets (Neutron)."""


@network.command("list")
@click.pass_context
def network_list(ctx: click.Context) -> None:
    """List all networks."""
    neutron = NeutronClient(mock=_is_mock(ctx.obj["mock"]))
    networks = neutron.list_networks()

    table = Table(title="Networks", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Status")

    for n in networks:
        table.add_row(str(n.get("id", "")), str(n.get("name", "")), str(n.get("status", "")))

    if not networks:
        console.print("[yellow]No networks found.[/yellow]")
    else:
        console.print(table)


@network.command("create")
@click.option("--name", required=True, help="Network name.")
@click.option("--cidr", default=None, help="Subnet CIDR to attach (e.g. 10.0.0.0/24).")
@click.pass_context
def network_create(ctx: click.Context, name: str, cidr: str) -> None:
    """Create a network, optionally with a subnet."""
    neutron = NeutronClient(mock=_is_mock(ctx.obj["mock"]))
    console.print(f"[cyan]Creating network [bold]{name}[/bold]...[/cyan]")
    net = neutron.create_network(name=name)
    console.print(f"[green]Network created:[/green] {net['id']}")

    if cidr:
        subnet = neutron.create_subnet(net["id"], name=f"{name}-subnet", cidr=cidr)
        console.print(f"[green]Subnet created:[/green] {subnet['id']} ({cidr})")


# ------------------------------------------------------------------ volume
@cli.group()
def volume() -> None:
    """Manage block volumes (Cinder)."""


@volume.command("list")
@click.pass_context
def volume_list(ctx: click.Context) -> None:
    """List all volumes."""
    cinder = CinderClient(mock=_is_mock(ctx.obj["mock"]))
    vols = cinder.list_volumes()

    table = Table(title="Volumes", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Size (GiB)")
    table.add_column("Status")

    for v in vols:
        table.add_row(str(v.get("id", "")), str(v.get("name", "")), str(v.get("size", "")), str(v.get("status", "")))

    if not vols:
        console.print("[yellow]No volumes found.[/yellow]")
    else:
        console.print(table)


@volume.command("create")
@click.option("--name", required=True, help="Volume name.")
@click.option("--size", required=True, type=int, help="Size in GiB.")
@click.pass_context
def volume_create(ctx: click.Context, name: str, size: int) -> None:
    """Create a new block volume."""
    cinder = CinderClient(mock=_is_mock(ctx.obj["mock"]))
    vol = cinder.create_volume(name=name, size=size)
    console.print(f"[green]Volume created:[/green] {vol['id']} ({size} GiB, {vol['status']})")


@volume.command("attach")
@click.option("--volume", "volume_id", required=True, help="Volume ID.")
@click.option("--server", "server_id", required=True, help="Server ID.")
@click.pass_context
def volume_attach(ctx: click.Context, volume_id: str, server_id: str) -> None:
    """Attach a volume to a server."""
    cinder = CinderClient(mock=_is_mock(ctx.obj["mock"]))
    cinder.attach_volume(server_id=server_id, volume_id=volume_id)
    console.print(f"[green]Volume {volume_id} attached to {server_id}.[/green]")


@volume.command("snapshot")
@click.option("--volume", "volume_id", required=True, help="Volume ID.")
@click.option("--name", required=True, help="Snapshot name.")
@click.pass_context
def volume_snapshot(ctx: click.Context, volume_id: str, name: str) -> None:
    """Snapshot a volume."""
    cinder = CinderClient(mock=_is_mock(ctx.obj["mock"]))
    snap = cinder.snapshot_volume(volume_id=volume_id, name=name)
    console.print(f"[green]Snapshot created:[/green] {snap['id']}")


@volume.command("delete")
@click.argument("volume_id")
@click.pass_context
def volume_delete(ctx: click.Context, volume_id: str) -> None:
    """Delete a volume."""
    cinder = CinderClient(mock=_is_mock(ctx.obj["mock"]))
    cinder.delete_volume(volume_id)
    console.print(f"[green]Volume {volume_id} deleted.[/green]")


# ------------------------------------------------------------------ object
@cli.group(name="object")
def object_cmd() -> None:
    """Manage object storage containers and objects (Swift)."""


@object_cmd.command("containers")
@click.pass_context
def object_containers(ctx: click.Context) -> None:
    """List all containers in the account."""
    swift = SwiftClient(mock=_is_mock(ctx.obj["mock"]))
    containers = swift.list_containers()

    table = Table(title="Containers", show_lines=True)
    table.add_column("Name", style="bold")
    table.add_column("Objects", justify="right")
    table.add_column("Size (bytes)", justify="right")

    for c in containers:
        table.add_row(str(c.get("name", "")), str(c.get("count", 0)), str(c.get("bytes", 0)))

    if not containers:
        console.print("[yellow]No containers found.[/yellow]")
    else:
        console.print(table)


@object_cmd.command("list")
@click.argument("container")
@click.pass_context
def object_list(ctx: click.Context, container: str) -> None:
    """List objects in a container."""
    swift = SwiftClient(mock=_is_mock(ctx.obj["mock"]))
    objects = swift.list_objects(container=container)

    table = Table(title=f"Objects in {container!r}", show_lines=True)
    table.add_column("Name", style="bold")
    table.add_column("Size (bytes)")

    for o in objects:
        table.add_row(str(o.get("name", "")), str(o.get("bytes", 0)))

    if not objects:
        console.print("[yellow]Container is empty.[/yellow]")
    else:
        console.print(table)


@object_cmd.command("upload")
@click.option("--container", required=True, help="Target container name.")
@click.option("--file", "file_path", required=True, help="Local file to upload.")
@click.option("--name", default=None, help="Object name (defaults to filename).")
@click.pass_context
def object_upload(ctx: click.Context, container: str, file_path: str, name: str) -> None:
    """Upload a local file to a container."""
    swift = SwiftClient(mock=_is_mock(ctx.obj["mock"]))
    obj = swift.upload_file(container=container, file_path=file_path, object_name=name)
    console.print(f"[green]Uploaded:[/green] {obj['name']} ({obj.get('bytes', 0)} bytes) to {container}")


@object_cmd.command("download")
@click.option("--container", required=True, help="Source container name.")
@click.option("--name", required=True, help="Object name to download.")
@click.option("--output", default=None, help="Local output path (defaults to object name).")
@click.pass_context
def object_download(ctx: click.Context, container: str, name: str, output: str) -> None:
    """Download an object from a container."""
    swift = SwiftClient(mock=_is_mock(ctx.obj["mock"]))
    data = swift.download_object(container=container, name=name)
    out_path = output or name
    with open(out_path, "wb") as fh:
        fh.write(data)
    console.print(f"[green]Downloaded:[/green] {name} to {out_path}")


if __name__ == "__main__":
    cli()
