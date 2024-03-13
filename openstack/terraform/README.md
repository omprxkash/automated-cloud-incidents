# Terraform — OpenStack Stack

This Terraform configuration provisions a network, subnet, router, compute instances, floating IPs, and a data volume using the [OpenStack Terraform provider](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest).

## What it creates

- Private network + subnet (`10.20.0.0/24`)
- Router with external gateway + subnet interface
- One or more compute instances (configurable count)
- A floating IP per instance
- A block volume attached to the first instance

## Prerequisites

- Terraform >= 1.5
- An OpenStack cloud with Keystone v3
- A key pair already imported into OpenStack

## Quick start

```bash
cd terraform

# Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform plan
terraform apply
```

### terraform.tfvars.example

```hcl
auth_url       = "https://keystone.example.com:5000/v3"
project_name   = "demo"
username       = "demo"
password       = "replace-me"
region         = "RegionOne"
public_network = "public"
key_pair       = "my-key"
image_name     = "ubuntu-22.04"
flavor_name    = "m1.small"
instance_count = 2
volume_size    = 20
subnet_cidr    = "10.20.0.0/24"
```

## Variables

| Name | Default | Description |
|---|---|---|
| `auth_url` | *(required)* | Keystone endpoint |
| `project_name` | `demo` | Project/tenant name |
| `username` | *(required)* | OpenStack user |
| `password` | *(required)* | OpenStack password |
| `region` | `RegionOne` | Region |
| `public_network` | `public` | External network for floating IPs |
| `image_name` | `ubuntu-22.04` | Image for instances |
| `flavor_name` | `m1.small` | Instance flavor |
| `key_pair` | *(required)* | SSH key pair name |
| `instance_count` | `1` | How many instances |
| `volume_size` | `20` | Data volume size (GiB) |
| `subnet_cidr` | `10.20.0.0/24` | Private subnet CIDR |

## Outputs

| Name | Description |
|---|---|
| `floating_ips` | Public IP addresses |
| `instance_ids` | Compute instance IDs |
| `private_network_id` | Private network ID |
| `data_volume_id` | Block volume ID |

## Teardown

```bash
terraform destroy
```

## State management

By default Terraform stores state locally in `terraform.tfstate`. For team use, configure a remote backend (e.g. S3-compatible object store):

```hcl
terraform {
  backend "s3" {
    bucket   = "my-tfstate-bucket"
    key      = "openstack/terraform.tfstate"
    region   = "us-east-1"
    endpoint = "https://object-store.example.com"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}
```
