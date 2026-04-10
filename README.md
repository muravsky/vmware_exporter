# vmware_exporter

Prometheus exporter for VMware vCenter / vSphere.

## What it exports

- VM metrics (power state, CPU, memory)
- VM guest metrics (disks, tools, IP)
- Snapshot metrics
- Host metrics (+ optional alarms/sensors)
- Datastore metrics
- Optional tags and custom attributes as metric labels

## Quick start (Docker)

```bash
docker run --rm -p 9272:9272 \
  -e VSPHERE_HOST=vcenter.company.com \
  -e VSPHERE_USER=administrator@vsphere.local \
  -e VSPHERE_PASSWORD=secret \
  -e VSPHERE_IGNORE_SSL=true \
  --name vmware_exporter \
  muravsky/vmware-exporter
```

Then open:

- http://localhost:9272/metrics

## Minimal configuration file

```yaml
default:
  vsphere_host: vcenter.company.com
  vsphere_user: administrator@vsphere.local
  vsphere_password: secret
  ignore_ssl: true
  specs_size: 5000
  fetch_custom_attributes: true
  fetch_tags: false
  fetch_alarms: false
  collect_only:
    vms: true
    vmguests: true
    datastores: true
    hosts: true
    snapshots: true
```

Run:

```bash
vmware_exporter -c /path/to/config.yml
```

## Environment variables

### Default section variables

| Variable | Default | Description |
| --- | --- | --- |
| `VSPHERE_HOST` | n/a | vSphere / vCenter host |
| `VSPHERE_USER` | n/a | Username |
| `VSPHERE_PASSWORD` | n/a | Password |
| `VSPHERE_IGNORE_SSL` | `False` | Ignore TLS certificate validation |
| `VSPHERE_SPECS_SIZE` | `5000` | Batch size for performance query specs |
| `VSPHERE_FETCH_CUSTOM_ATTRIBUTES` | `False` | Export custom attributes as labels |
| `VSPHERE_FETCH_TAGS` | `False` | Export tags as labels |
| `VSPHERE_FETCH_ALARMS` | `False` | Export triggered alarms |
| `VSPHERE_COLLECT_VMS` | `True` | Collect VM metrics |
| `VSPHERE_COLLECT_VMGUESTS` | `True` | Collect VM guest metrics |
| `VSPHERE_COLLECT_DATASTORES` | `True` | Collect datastore metrics |
| `VSPHERE_COLLECT_HOSTS` | `True` | Collect host metrics |
| `VSPHERE_COLLECT_SNAPSHOTS` | `True` | Collect snapshot metrics |

### Custom section variables

You can define section-specific values with `VSPHERE_<SECTION>_...` prefixes.

Example for section `limited`:

- `VSPHERE_LIMITED_HOST`
- `VSPHERE_LIMITED_USER`
- `VSPHERE_LIMITED_PASSWORD`
- `VSPHERE_LIMITED_IGNORE_SSL`
- `VSPHERE_LIMITED_SPECS_SIZE`
- `VSPHERE_LIMITED_FETCH_CUSTOM_ATTRIBUTES`
- `VSPHERE_LIMITED_FETCH_TAGS`
- `VSPHERE_LIMITED_FETCH_ALARMS`
- `VSPHERE_LIMITED_COLLECT_VMS`
- `VSPHERE_LIMITED_COLLECT_VMGUESTS`
- `VSPHERE_LIMITED_COLLECT_DATASTORES`
- `VSPHERE_LIMITED_COLLECT_HOSTS`
- `VSPHERE_LIMITED_COLLECT_SNAPSHOTS`

`VSPHERE_<SECTION>_USER` is enough for section discovery.

## Multiple sections

You can define multiple config sections and select one at scrape time:

- `/metrics?section=default`
- `/metrics?section=esx`

Environment-based sections are supported via prefix:

- `VSPHERE_<SECTION>_HOST`
- `VSPHERE_<SECTION>_USER`
- `VSPHERE_<SECTION>_PASSWORD`
- etc.

Example: `VSPHERE_LIMITED_USER=...` enables section `limited`.

## Prometheus configuration examples

### Single section scrape

```yaml
- job_name: vmware_exporter
  metrics_path: /metrics
  static_configs:
    - targets: ["exporter-host:9272"]
  params:
    section: ["default"]
```

### Multiple sections from one exporter

```yaml
- job_name: vmware_exporter_default
  metrics_path: /metrics
  static_configs:
    - targets: ["exporter-host:9272"]
  params:
    section: ["default"]

- job_name: vmware_exporter_limited
  metrics_path: /metrics
  static_configs:
    - targets: ["exporter-host:9272"]
  params:
    section: ["limited"]
```

### Target relabeling style

```yaml
- job_name: vmware_vcenter
  metrics_path: /metrics
  static_configs:
    - targets: ["vcenter.company.com"]
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: exporter-host:9272
```

## Sample exported metrics

```text
# HELP vmware_vm_power_state VMWare VM Power state (On / Off)
# TYPE vmware_vm_power_state gauge
vmware_vm_power_state{vm_name="app-01",ds_name="datastore1",host_name="esx-01",dc_name="dc1",cluster_name="cluster-a",vm_ip_address="10.10.10.10"} 1

# HELP vmware_vm_snapshot_timestamp_seconds VMWare Snapshot creation time in seconds
# TYPE vmware_vm_snapshot_timestamp_seconds gauge
vmware_vm_snapshot_timestamp_seconds{vm_name="app-01",ds_name="datastore1",host_name="esx-01",dc_name="dc1",cluster_name="cluster-a",vm_snapshot_name="pre-upgrade"} 1712736000

# HELP vmware_datastore_capacity_size VMWare Datasore capacity in bytes
# TYPE vmware_datastore_capacity_size gauge
vmware_datastore_capacity_size{ds_name="datastore1",dc_name="dc1",ds_cluster="pod-a"} 6.7377299456e+10

# HELP vmware_host_memory_max VMWare Host Memory Max availability in Mbytes
# TYPE vmware_host_memory_max gauge
vmware_host_memory_max{host_name="esx-01",dc_name="dc1",cluster_name="cluster-a"} 131059.0
```

## Build and publish Docker image

```bash
docker login
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t muravsky/vmware-exporter:latest \
  -t muravsky/vmware-exporter:vX.Y.Z \
  --push .
```

## Source / credits

This project is based on community VMware exporter work and keeps attribution to original sources:

- https://github.com/rverchere/vmware_exporter
- https://github.com/pryorda/vmware_exporter
- https://github.com/vmware/pyvmomi-community-samples
- https://github.com/jbidinger/pyvmomi-tools
- https://www.robustperception.io/writing-a-jenkins-exporter-in-python/

Core libraries:

- [pyVmomi](https://github.com/vmware/pyvmomi)
- [prometheus/client_python](https://github.com/prometheus/client_python)
- [Twisted](https://twisted.org/)

## License

See [LICENSE](LICENSE).
