#!/usr/bin/env python3
"""Compare two Prometheus /metrics dumps for parity (ignoring volatile values)."""

from __future__ import print_function

import re
import sys
from collections import defaultdict


def parse_metrics(text):
    """Return dict: (metric_name, label_tuple) -> set of values as strings."""
    series = defaultdict(set)
    skipped = 0
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        try:
            if '{' in line:
                name, rest = line.split('{', 1)
                if '}' not in rest:
                    skipped += 1
                    continue
                labels, value = rest.rsplit('}', 1)
                parts = [p for p in labels.split(',') if p]
                label_items = []
                for part in parts:
                    if '=' not in part:
                        skipped += 1
                        continue
                    k, v = part.split('=', 1)
                    label_items.append((k, v.strip('"')))
                label_tuple = tuple(sorted(label_items))
                val = value.strip()
                if not val:
                    skipped += 1
                    continue
            else:
                parts = line.rsplit(' ', 1)
                if len(parts) != 2:
                    skipped += 1
                    continue
                name, val = parts
                label_tuple = ()
            series[(name, label_tuple)].add(val)
        except (ValueError, IndexError):
            skipped += 1
            continue
    return series, skipped


def main():
    if len(sys.argv) != 3:
        print('Usage: parity-compare.py prod.txt dev.txt', file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], 'r', encoding='utf-8', errors='replace') as f:
        prod, prod_skipped = parse_metrics(f.read())
    with open(sys.argv[2], 'r', encoding='utf-8', errors='replace') as f:
        dev, dev_skipped = parse_metrics(f.read())

    prod_keys = set(prod)
    dev_keys = set(dev)

    only_prod = prod_keys - dev_keys
    only_dev = dev_keys - prod_keys
    common = prod_keys & dev_keys

    value_mismatch = []
    for key in sorted(common):
        if prod[key] != dev[key]:
            value_mismatch.append((key, prod[key], dev[key]))

    prod_names = {k[0] for k in prod_keys}
    dev_names = {k[0] for k in dev_keys}

    print('=== Parity summary ===')
    print('Skipped malformed/truncated lines: prod={} dev={}'.format(prod_skipped, dev_skipped))
    print('Prod series: {}'.format(len(prod_keys)))
    print('Dev series:  {}'.format(len(dev_keys)))
    print('Common:      {}'.format(len(common)))
    print('Only prod:   {}'.format(len(only_prod)))
    print('Only dev:    {}'.format(len(only_dev)))
    print('Value diff:  {}'.format(len(value_mismatch)))
    print('Prod metric names: {}'.format(len(prod_names)))
    print('Dev metric names:  {}'.format(len(dev_names)))
    print('Metric names only in prod: {}'.format(len(prod_names - dev_names)))
    print('Metric names only in dev:  {}'.format(len(dev_names - prod_names)))

    if prod_names - dev_names:
        print('\n--- Metric names only in PROD (up to 30) ---')
        for name in sorted(prod_names - dev_names)[:30]:
            print(name)
    if dev_names - prod_names:
        print('\n--- Metric names only in DEV (up to 30) ---')
        for name in sorted(dev_names - prod_names)[:30]:
            print(name)

    if only_prod:
        print('\n--- Label sets only in PROD (up to 20) ---')
        for key in sorted(only_prod)[:20]:
            print('{} {}'.format(key[0], dict(key[1])))

    if only_dev:
        print('\n--- Label sets only in DEV (up to 20) ---')
        for key in sorted(only_dev)[:20]:
            print('{} {}'.format(key[0], dict(key[1])))

    # Label name differences per metric
    label_diffs = defaultdict(set)
    for name in sorted(prod_names | dev_names):
        prod_labels = {lbl for k in prod_keys if k[0] == name for lbl, _ in k[1]}
        dev_labels = {lbl for k in dev_keys if k[0] == name for lbl, _ in k[1]}
        if prod_labels != dev_labels:
            label_diffs[name] = (prod_labels, dev_labels)

    if label_diffs:
        print('\n--- Metrics with different label keys (up to 25) ---')
        for name in sorted(label_diffs)[:25]:
            pl, dl = label_diffs[name]
            print('{}: prod_only={} dev_only={}'.format(
                name, sorted(pl - dl), sorted(dl - pl)))

    if value_mismatch:
        print('\n--- Value mismatches (up to 15; counters/gauges may differ over time) ---')
        for key, pv, dv in value_mismatch[:15]:
            print('{} {} prod={} dev={}'.format(key[0], dict(key[1]), pv, dv))

    # Parity verdict
    structural_ok = not only_prod and not only_dev and not label_diffs
    print('\n=== Verdict ===')
    if structural_ok:
        print('STRUCTURAL PARITY: OK (same metric+label series)')
        if value_mismatch:
            print('VALUES: {} series differ (expected for live counters/timestamps)'.format(len(value_mismatch)))
    else:
        print('STRUCTURAL PARITY: DIFFERENCES FOUND')
        sys.exit(1)


if __name__ == '__main__':
    main()
