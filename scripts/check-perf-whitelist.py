#!/usr/bin/env python3
"""Stream /metrics and verify custom_attributes_on_perf_metrics whitelist."""

from __future__ import print_function

import os
import re
import sys
import urllib.request

BASE_LABELS = {
    'host_name', 'dc_name', 'cluster_name', 'tags',
    'vm_name', 'ds_name', 'vm_ip_address', 'alarms', 'ds_cluster', 'partition',
}

CHECK_METRICS = [
    'vmware_host_cpu_usagemhz_average',
    'vmware_host_cpu_usage_average',
    'vmware_host_cpu_demand_average',
    'vmware_vm_max_cpu_usage',
    'vmware_vm_cpu_ready_summation',
    'vmware_vm_power_state',
]


def parse_labels(label_blob):
    labels = {}
    for part in label_blob.split(','):
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        labels[key] = value.strip('"')
    return labels


def custom_labels(labels):
    return sorted(key for key in labels if key not in BASE_LABELS)


def stream_metrics(url, max_lines_per_metric=3):
    samples = {metric: [] for metric in CHECK_METRICS}
    metric_re = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{(.+)\}\s')

    with urllib.request.urlopen(url, timeout=600) as response:
        for raw_line in response:
            line = raw_line.decode('utf-8', errors='replace').strip()
            if not line or line.startswith('#'):
                continue

            match = metric_re.match(line)
            if not match:
                continue

            name = match.group(1)
            if name not in samples:
                continue
            if len(samples[name]) >= max_lines_per_metric:
                continue

            labels = parse_labels(match.group(2))
            samples[name].append(labels)

            if all(len(values) >= max_lines_per_metric for values in samples.values()):
                break

    return samples


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        'PARITY_DEV_METRICS_URL',
        'http://localhost:9273/metrics?target=vcenter.example.com',
    )
    label = sys.argv[2] if len(sys.argv) > 2 else 'dev'

    print('=== {} ==='.format(label))
    print('URL:', url)
    try:
        samples = stream_metrics(url)
    except Exception as exc:
        print('ERROR:', exc)
        sys.exit(1)

    for metric in CHECK_METRICS:
        rows = samples.get(metric, [])
        print('\n{} (samples={})'.format(metric, len(rows)))
        if not rows:
            print('  not found in streamed output')
            continue
        custom = custom_labels(rows[0])
        print('  custom labels:', custom if custom else '(none)')
        print('  all labels:', sorted(rows[0]))


if __name__ == '__main__':
    main()
