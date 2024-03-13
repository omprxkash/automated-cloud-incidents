# Heat Templates

These Heat Orchestration Templates (HOT) provision a 3-tier web stack on OpenStack.

## Templates

| File | Purpose |
|---|---|
| `web_stack.yaml` | Core stack: network, load balancer, auto-scaling web tier, DB server + volume |
| `autoscaling.yaml` | Ceilometer/Aodh alarms tied to the scaling policies |

## Parameters

### web_stack.yaml

| Parameter | Default | Description |
|---|---|---|
| `key_name` | *(required)* | SSH key pair name |
| `image` | `ubuntu-22.04` | Image for all servers |
| `web_flavor` | `m1.small` | Flavor for web tier |
| `db_flavor` | `m1.medium` | Flavor for DB server |
| `db_volume_size` | `50` | Database volume size (GiB) |
| `public_network` | `public` | External network name |
| `web_min_size` | `1` | Min web servers |
| `web_max_size` | `4` | Max web servers |
| `web_desired_size` | `2` | Initial web server count |

### autoscaling.yaml

| Parameter | Default | Description |
|---|---|---|
| `scale_up_url` | *(required)* | From `web_stack` `scale_up_url` output |
| `scale_down_url` | *(required)* | From `web_stack` `scale_down_url` output |
| `high_cpu_threshold` | `75` | CPU % to trigger scale-up |
| `low_cpu_threshold` | `20` | CPU % to trigger scale-down |
| `alarm_period` | `60` | Alarm window in seconds |
| `alarm_evaluation_periods` | `3` | Consecutive periods before firing |

## Deploying

```bash
# Deploy the core stack
openstack stack create -t heat/web_stack.yaml \
  --parameter key_name=my-key \
  --parameter public_network=public \
  web-stack

# Wait for CREATE_COMPLETE
openstack stack show web-stack

# Grab the scaling URLs
SCALE_UP=$(openstack stack output show web-stack scale_up_url -f value -c output_value)
SCALE_DOWN=$(openstack stack output show web-stack scale_down_url -f value -c output_value)

# Deploy alarms
openstack stack create -t heat/autoscaling.yaml \
  --parameter scale_up_url="$SCALE_UP" \
  --parameter scale_down_url="$SCALE_DOWN" \
  web-alarms
```

## Teardown

```bash
openstack stack delete web-alarms
openstack stack delete web-stack
```

## Validating templates locally

You can check your YAML is well-formed before deploying:

```bash
python -c "import yaml; yaml.safe_load(open('heat/web_stack.yaml'))" && echo "OK"
python -c "import yaml; yaml.safe_load(open('heat/autoscaling.yaml'))" && echo "OK"
```
