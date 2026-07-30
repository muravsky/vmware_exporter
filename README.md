# vmware_exporter

Prometheus exporter for VMware vCenter / vSphere.

Maintained fork of [pryorda/vmware_exporter](https://github.com/pryorda/vmware_exporter) by Daniel Pryor.
Docker image: [`muravsky/vmware-exporter`](https://hub.docker.com/r/muravsky/vmware-exporter).
Source: [`muravsky/vmware_exporter`](https://github.com/muravsky/vmware_exporter).
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
  fetch_custom_attributes_on_perf: true
  custom_attributes_blacklist:
    - Backup
    - TicketNumber
  custom_attributes_on_perf_metrics:
    - vmware_host_cpu_usage_average
    - vmware_vm_net_transmitted_average
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
| `VSPHERE_FETCH_CUSTOM_ATTRIBUTES_ON_PERF` | `True` | Add custom attributes to VM/host performance metrics |
| `VSPHERE_CUSTOM_ATTRIBUTES_BLACKLIST` | n/a | Comma-separated custom attribute names to exclude from all metrics |
| `VSPHERE_CUSTOM_ATTRIBUTES_ON_PERF_METRICS` | n/a | Comma-separated performance metric names that receive custom attributes. If empty, all perf metrics get them |
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
- `VSPHERE_LIMITED_FETCH_CUSTOM_ATTRIBUTES_ON_PERF`
- `VSPHERE_LIMITED_CUSTOM_ATTRIBUTES_BLACKLIST`
- `VSPHERE_LIMITED_CUSTOM_ATTRIBUTES_ON_PERF_METRICS`
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

## Test image on Docker Hub (without touching `latest`)

You can push an experimental build from your current working tree under a separate tag.
`latest` on Docker Hub stays unchanged until you explicitly push `:latest`.

Recommended tag names:

- `dev-YYYYMMDD` for dated experiments
- `dev-modernization` for the dependency upgrade branch
- `canary` for short-lived smoke tests

Windows (PowerShell):

```powershell
docker login
.\scripts\docker-build-test.ps1 -Tag dev-modernization -Push
```

Linux / WSL:

```bash
docker login
PUSH=1 TAG=dev-modernization ./scripts/docker-build-test.sh
```

Run production and test images side by side:

```bash
# current production image
docker run -d --name vmware_exporter_old \
  -p 9272:9272 \
  -e VSPHERE_HOST=vcenter.company.com \
  -e VSPHERE_USER=administrator@vsphere.local \
  -e VSPHERE_PASSWORD=secret \
  -e VSPHERE_IGNORE_SSL=true \
  muravsky/vmware-exporter:latest

# test image from Docker Hub
docker run -d --name vmware_exporter_new \
  -p 9273:9272 \
  -e VSPHERE_HOST=vcenter.company.com \
  -e VSPHERE_USER=administrator@vsphere.local \
  -e VSPHERE_PASSWORD=secret \
  -e VSPHERE_IGNORE_SSL=true \
  muravsky/vmware-exporter:dev-modernization
```

Compare output:

```bash
curl -s http://localhost:9272/metrics -o old.txt
curl -s http://localhost:9273/metrics -o new.txt
diff old.txt new.txt
```

Optional parity helpers in `scripts/` (use env vars, no hardcoded hosts):

```bash
export PARITY_EXPORTER_HOST=exporter-host
export PARITY_TARGET=vcenter.company.com
python scripts/quick-prod-dev-diff.py
python scripts/parity-compare.py old.txt new.txt
```

Local-only build (no push):

```powershell
.\scripts\docker-build-test.ps1 -Tag dev-local
```

## Origin and credits

This repository is a maintained fork of [pryorda/vmware_exporter](https://github.com/pryorda/vmware_exporter) by [Daniel Pryor](https://github.com/pryorda), which in turn builds on earlier [rverchere/vmware_exporter](https://github.com/rverchere/vmware_exporter) work by Remi Verchere.

Thanks and attribution:

- [Daniel Pryor / pryorda](https://github.com/pryorda/vmware_exporter) — primary upstream exporter and long-time maintainer
- [Remi Verchere / rverchere](https://github.com/rverchere/vmware_exporter) — original VMware exporter
- [VMware pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples)
- [jbidinger/pyvmomi-tools](https://github.com/jbidinger/pyvmomi-tools)
- [Writing a Jenkins exporter in Python](https://www.robustperception.io/writing-a-jenkins-exporter-in-python/) — Prometheus exporter patterns

Core libraries:

- [pyVmomi](https://github.com/vmware/pyvmomi)
- [prometheus/client_python](https://github.com/prometheus/client_python)
- [Twisted](https://twisted.org/)

## License

See [LICENSE](LICENSE). The project remains under the BSD 3-Clause License; original copyright notices are preserved.