#!/usr/bin/env python3
"""Focused analysis of prod vs dev parity dumps."""

from __future__ import print_function

import os
import sys
from collections import defaultdict


def parse(path):
    series = defaultdict(list)
    for line in open(path, encoding='utf-8', errors='replace'):
        if not line or line.startswith('#') or '{' not in line:
            continue
        try:
            name, rest = line.split('{', 1)
            if '}' not in rest:
                continue
            labels, _ = rest.rsplit('}', 1)
        except ValueError:
            continue
        row = {}
        for part in labels.split(','):
            if '=' in part:
                key, value = part.split('=', 1)
                row[key] = value.strip('"')
        series[name].append(row)
    return series


def main():
    prod_path = sys.argv[1] if len(sys.argv) > 1 else '.parity-test/prod.txt'
    dev_path = sys.argv[2] if len(sys.argv) > 2 else '.parity-test/dev.txt'

    prod = parse(prod_path)
    dev = parse(dev_path)

    print('=== File stats ===')
    for label, path in [('prod', prod_path), ('dev', dev_path)]:
        print('{}: {:.1f} MB'.format(label, os.path.getsize(path) / 1024 / 1024))

    print('\n=== Sample counts ===')
    for metric in [
        'vmware_vm_power_state',
        'vmware_host_memory_max',
        'vmware_vm_cpu_usage_average',
        'vmware_host_cpu_usage_average',
        'vmware_vm_red_alarms',
        'vmware_vm_net_transmitted_average',
    ]:
        print('{}: prod={} dev={}'.format(
            metric, len(prod.get(metric, [])), len(dev.get(metric, []))))

    for metric in ['vmware_vm_power_state', 'vmware_host_memory_max']:
        prod_labels = set()
        dev_labels = set()
        for row in prod.get(metric, [])[:5000]:
            prod_labels.update(row)
        for row in dev.get(metric, [])[:5000]:
            dev_labels.update(row)
        print('\n{} label keys:'.format(metric))
        print('  prod:', sorted(prod_labels))
        print('  dev :', sorted(dev_labels))
        print('  only prod:', sorted(prod_labels - dev_labels))
        print('  only dev :', sorted(dev_labels - prod_labels))

    blacklist_like = {'backup', 'ticketnumber', 'automation', 'linux_os_manual_patching'}
    for metric in ['vmware_vm_power_state', 'vmware_host_memory_max']:
        prod_hits = sum(
            1 for row in prod.get(metric, [])
            if any(key.lower() in blacklist_like for key in row)
        )
        dev_hits = sum(
            1 for row in dev.get(metric, [])
            if any(key.lower() in blacklist_like for key in row)
        )
        print('{} rows with blacklist-like labels: prod={} dev={}'.format(
            metric, prod_hits, dev_hits))

    base_labels = {
        'vm_name', 'ds_name', 'host_name', 'dc_name', 'cluster_name',
        'vm_ip_address', 'tags', 'alarms', 'ds_cluster',
    }
    common_perf = []
    for metric in sorted(set(prod) & set(dev)):
        if not any(token in metric for token in ('_cpu_', '_mem_', '_net_', '_disk_')):
            continue
        if prod.get(metric) and dev.get(metric):
            common_perf.append((metric, len(prod[metric]), len(dev[metric])))
    common_perf.sort(key=lambda item: -item[2])

    print('\n=== Perf metrics present in BOTH (top 12) ===')
    for metric, prod_count, dev_count in common_perf[:12]:
        prod_custom = set()
        dev_custom = set()
        for row in prod[metric][:100]:
            prod_custom.update(key for key in row if key not in base_labels)
        for row in dev[metric][:100]:
            dev_custom.update(key for key in row if key not in base_labels)
        print('{}: prod_series={} dev_series={} custom_prod={} custom_dev={}'.format(
            metric, prod_count, dev_count, sorted(prod_custom), sorted(dev_custom)))

    vm_name = 'ua-apac-kaa-ci1'
    print('\n=== Same VM comparison ({}) ==='.format(vm_name))
    for metric in [
        'vmware_vm_power_state',
        'vmware_vm_cpu_usage_average',
        'vmware_vm_net_transmitted_average',
        'vmware_vm_red_alarms',
    ]:
        prod_rows = [row for row in prod.get(metric, []) if row.get('vm_name') == vm_name]
        dev_rows = [row for row in dev.get(metric, []) if row.get('vm_name') == vm_name]
        print('\n{}: prod={} dev={}'.format(metric, len(prod_rows), len(dev_rows)))
        if prod_rows:
            print('  prod keys:', sorted(prod_rows[0]))
        if dev_rows:
            print('  dev keys :', sorted(dev_rows[0]))

    print('\n=== Selected perf metrics custom labels ===')
    for metric in [
        'vmware_host_cpu_usage_average',
        'vmware_host_net_droppedRx_summation',
        'vmware_host_mem_active_average',
        'vmware_vm_max_cpu_usage',
        'vmware_vm_cpu_ready_summation',
    ]:
        for label, data in [('prod', prod), ('dev', dev)]:
            rows = data.get(metric, [])
            custom = set()
            for row in rows[:50]:
                custom.update(key for key in row if key not in base_labels)
            print('{} {} count={} custom={}'.format(
                label, metric, len(rows), sorted(custom)))
        print('---')


if __name__ == '__main__':
    main()
