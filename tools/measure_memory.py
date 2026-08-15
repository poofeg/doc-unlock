#!/usr/bin/env python3
"""Run ``doc-unlock`` and report peak resident memory (RSS).

Usage:
    python tools/measure_memory.py unlock INPUT [OPTIONS]

Every argument is forwarded unchanged to ``doc-unlock``. Peak RSS is measured
with the BSD ``time -l`` utility, so this script requires macOS/BSD.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _peak_rss_mib(stats: str) -> float | None:
    for line in stats.splitlines():
        if 'maximum resident set size' in line:
            return int(line.split()[0]) / 1024 / 1024
    return None


def _real_seconds(stats: str) -> str:
    first = stats.splitlines()[0] if stats else ''
    parts = first.split()
    return parts[0] if parts else ''


def main() -> int:
    if not sys.argv[1:]:
        print('usage: python tools/measure_memory.py unlock INPUT [OPTIONS]', file=sys.stderr)
        return 2

    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT / 'src')

    fd, stats_path = tempfile.mkstemp(prefix='doc-unlock-time-')
    os.close(fd)

    cmd = ['/usr/bin/time', '-l', '-o', stats_path, sys.executable, '-m', 'doc_unlock', *sys.argv[1:]]
    proc = subprocess.run(cmd, env=env)

    stats = Path(stats_path).read_text()
    os.unlink(stats_path)

    rss = _peak_rss_mib(stats)
    real = _real_seconds(stats)
    if rss is not None:
        print(f'peak RSS: {rss:.1f} MiB (real {real}s)', file=sys.stderr)

    return proc.returncode


if __name__ == '__main__':
    sys.exit(main())
