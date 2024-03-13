output "floating_ips" {
  description = "Public floating IP addresses assigned to web instances"
  value       = openstack_networking_floatingip_v2.web[*].address
}

output "instance_ids" {
  description = "IDs of the created compute instances"
  value       = openstack_compute_instance_v2.web[*].id
}

output "private_network_id" {
  description = "ID of the private network"
  value       = openstack_networking_network_v2.private.id
}

output "data_volume_id" {
  description = "ID of the data block volume"
  value       = openstack_blockstorage_volume_v3.data.id
}

output "router_id" {
  description = "ID of the main router"
  value       = openstack_networking_router_v2.main.id
}

output "subnet_id" {
  description = "ID of the private subnet"
  value       = openstack_networking_subnet_v2.private.id
}
