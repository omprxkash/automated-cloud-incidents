terraform {
  required_version = ">= 1.5"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.54"
    }
  }
}

provider "openstack" {
  auth_url    = var.auth_url
  tenant_name = var.project_name
  user_name   = var.username
  password    = var.password
  region      = var.region
}

# ---- Networking ----

resource "openstack_networking_network_v2" "private" {
  name           = "private-net"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "private" {
  name            = "private-subnet"
  network_id      = openstack_networking_network_v2.private.id
  cidr            = var.subnet_cidr
  ip_version      = 4
  dns_nameservers = var.dns_nameservers
}

resource "openstack_networking_router_v2" "main" {
  name                = "main-router"
  admin_state_up      = true
  external_network_id = data.openstack_networking_network_v2.public.id
}

resource "openstack_networking_router_interface_v2" "main" {
  router_id = openstack_networking_router_v2.main.id
  subnet_id = openstack_networking_subnet_v2.private.id
}

data "openstack_networking_network_v2" "public" {
  name = var.public_network
}

# ---- Compute ----

data "openstack_images_image_v2" "web" {
  name        = var.image_name
  most_recent = true
}

data "openstack_compute_flavor_v2" "web" {
  name = var.flavor_name
}

resource "openstack_compute_instance_v2" "web" {
  count           = var.instance_count
  name            = "web-${count.index + 1}"
  image_id        = data.openstack_images_image_v2.web.id
  flavor_id       = data.openstack_compute_flavor_v2.web.id
  key_pair        = var.key_pair
  security_groups = ["default"]

  network {
    uuid = openstack_networking_network_v2.private.id
  }

  metadata = {
    role = "web"
  }
}

# ---- Floating IP ----

resource "openstack_networking_floatingip_v2" "web" {
  count = var.instance_count
  pool  = var.public_network
}

resource "openstack_compute_floatingip_associate_v2" "web" {
  count       = var.instance_count
  floating_ip = openstack_networking_floatingip_v2.web[count.index].address
  instance_id = openstack_compute_instance_v2.web[count.index].id
}

# ---- Block Volume ----

resource "openstack_blockstorage_volume_v3" "data" {
  name = "data-volume"
  size = var.volume_size
}

resource "openstack_compute_volume_attach_v2" "data" {
  instance_id = openstack_compute_instance_v2.web[0].id
  volume_id   = openstack_blockstorage_volume_v3.data.id
}
