#!/usr/bin/env python3
"""Single-pass prod/dev comparison for selected metrics."""

from __future__ import print_function

import os
import re
import sys
import urllib.request

DEFAULT_TARGET = 'vcenter.example.com'
DEFAULT_EXPORTER_HOST = 'localhost'
DEFAULT_PROD_PORT = '9272'
DEFAULT_DEV_PORT = '9273'


def metrics_url(host, port, target):
    return 'http://{host}:{port}/metrics?target={target}'.format(
        host=host,
        port=port,
        target=target,
    )


URLS = {
    'prod': metrics_url(
        os.environ.get('PARITY_EXPORTER_HOST', DEFAULT_EXPORTER_HOST),
        os.environ.get('PARITY_PROD_PORT', DEFAULT_PROD_PORT),
        os.environ.get('PARITY_TARGET', DEFAULT_TARGET),
    ),
    'dev': metrics_url(
        os.environ.get('PARITY_EXPORTER_HOST', DEFAULT_EXPORTER_HOST),
        os.environ.get('PARITY_DEV_PORT', DEFAULT_DEV_PORT),
        os.environ.get('PARITY_TARGET', DEFAULT_TARGET),
    ),
}

METRICS = [
    'vmware_host_cpu_usagemhz_average',
    'vmware_host_cpu_usage_average',
    'vmware_host_cpu_demand_average',
    'vmware_vm_cpu_ready_summation',
    'vmware_vm_power_state',
    'vmware_vm_red_alarms',
]

BASE = {
    'host_name', 'dc_name', 'cluster_name', 'tags',
    'vm_name', 'ds_name', 'vm_ip_address', 'alarms', 'ds_cluster', 'partition',
}


def collect_first_samples(url):
    wanted = set(METRICS)
    found = {}
    metric_re = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{(.+)\}\s')

    with urllib.request.urlopen(url, timeout=600) as response:
        for raw_line in response:
            line = raw_line.decode('utf-8', errors='replace').strip()
            match = metric_re.match(line)
            if not match:
                continue

            name = match.group(1)
            if name not in wanted or name in found:
                continue

            labels = {}
            for part in match.group(2).split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    labels[key] = value.strip('"')
            found[name] = labels

            if len(found) == len(wanted):
                break

    return found


def main():
    all_samples = {}
    for env, url in URLS.items():
        print('Collecting from {}...'.format(env))
        print('  {}'.format(url))
        all_samples[env] = collect_first_samples(url)

    for metric in METRICS:
        print('\n=== {} ==='.format(metric))
        for env in ('prod', 'dev'):
            labels = all_samples[env].get(metric)
            if labels is None:
                print('{}: not found'.format(env))
                continue
            custom = sorted(key for key in labels if key not in BASE)
            extra = ''
            if metric.endswith('_alarms'):
                extra = ' alarms_label={}'.format('alarms' in labels)
            print('{}: custom={}{}'.format(env, custom, extra))


if __name__ == '__main__':
    main()
