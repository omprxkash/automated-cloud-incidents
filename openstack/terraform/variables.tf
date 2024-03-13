variable "auth_url" {
  description = "OpenStack Keystone auth URL (e.g. https://keystone.example.com:5000/v3)"
  type        = string
}

variable "project_name" {
  description = "OpenStack project / tenant name"
  type        = string
  default     = "demo"
}

variable "username" {
  description = "OpenStack username"
  type        = string
}

variable "password" {
  description = "OpenStack password"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "OpenStack region"
  type        = string
  default     = "RegionOne"
}

variable "public_network" {
  description = "Name of the external network for floating IPs"
  type        = string
  default     = "public"
}

variable "image_name" {
  description = "Image name for the compute instance"
  type        = string
  default     = "ubuntu-22.04"
}

variable "flavor_name" {
  description = "Flavor for the compute instance"
  type        = string
  default     = "m1.small"
}

variable "key_pair" {
  description = "SSH key pair name"
  type        = string
}

variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

variable "volume_size" {
  description = "Size of the data volume in GiB"
  type        = number
  default     = 20
}

variable "subnet_cidr" {
  description = "CIDR for the private subnet"
  type        = string
  default     = "10.20.0.0/24"
}

variable "dns_nameservers" {
  description = "DNS nameservers for the private subnet"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "tags" {
  description = "Tags to apply to compute instances"
  type        = map(string)
  default     = {}
}
