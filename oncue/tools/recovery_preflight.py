#!/usr/bin/env python3
"""Read-only resource inventory for a replacement container; never reads secrets."""
import json
import os
import platform
from pathlib import Path
import shutil


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def integer(value):
    try:
        result = int(value)
        return result if 0 < result < 2**60 else None
    except (ValueError, TypeError):
        return None


def inventory(root=None):
    root = Path(root or Path.cwd())
    mem = {}
    for line in (read('/proc/meminfo') or '').splitlines():
        fields = line.split()
        if fields and fields[0] in ('MemTotal:', 'MemAvailable:'):
            mem[fields[0][:-1]] = int(fields[1]) * 1024
    limit = integer(read('/sys/fs/cgroup/memory.max'))
    if limit is None:
        limit = integer(read('/sys/fs/cgroup/memory/memory.limit_in_bytes'))
    used = integer(read('/sys/fs/cgroup/memory.current'))
    if used is None:
        used = integer(read('/sys/fs/cgroup/memory/memory.usage_in_bytes'))
    totals = [n for n in (limit, mem.get('MemTotal')) if n is not None]
    available = [n for n in (mem.get('MemAvailable'),
                            max(0, limit - used) if limit is not None and used is not None else None)
                 if n is not None]
    try:
        affinity = len(os.sched_getaffinity(0))
    except AttributeError:
        affinity = os.cpu_count()
    cpu_limit = None
    quota = (read('/sys/fs/cgroup/cpu.max') or '').split()
    if len(quota) == 2 and quota[0] != 'max':
        cpu_limit = int(quota[0]) / int(quota[1])
    disk = shutil.disk_usage(root)
    os_release = {}
    for line in (read('/etc/os-release') or '').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            if key in ('ID', 'VERSION_ID', 'PRETTY_NAME'):
                os_release[key] = value.strip('"')
    return {
        'system': os_release, 'architecture': platform.machine(),
        'cpu_affinity_count': affinity, 'cgroup_cpu_quota': cpu_limit,
        'host_memory_bytes': mem.get('MemTotal'), 'cgroup_memory_limit_bytes': limit,
        'effective_memory_cap_bytes': min(totals) if totals else None,
        'available_memory_estimate_bytes': min(available) if available else None,
        'disk_free_bytes': disk.free,
        'cgroup_memory_events': read('/sys/fs/cgroup/memory.events'),
        'build_policy': 'Start with CARGO_BUILD_JOBS=2 and one build at a time; monitor memory and disk before increasing concurrency.'
    }


if __name__ == '__main__':
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
