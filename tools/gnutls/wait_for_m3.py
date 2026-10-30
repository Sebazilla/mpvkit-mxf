#!/usr/bin/env python3
"""Wait for other RushDeck gates/builds; never signal another process."""
import os
from pathlib import Path
import shlex
import subprocess
import time


def blockers(rows, own_pid):
    parents = {pid: ppid for pid, ppid, _ in rows}
    ancestors = set()
    current = own_pid
    while current > 0 and current not in ancestors:
        ancestors.add(current)
        current = parents.get(current, 0)
    found = []
    for pid, _, command in rows:
        if pid in ancestors:
            continue
        try:
            args = shlex.split(command)
        except ValueError:
            continue
        if any(arg.startswith("--selftest") for arg in args) or any(Path(arg).name in {"build.sh", "deploy.sh"} for arg in args):
            found.append(pid)
    return found


def wait():
    started = time.monotonic()
    while True:
        rows = []
        for line in subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True).splitlines():
            fields = line.strip().split(None, 2)
            try:
                if len(fields) == 3:
                    rows.append((int(fields[0]), int(fields[1]), fields[2]))
            except ValueError:
                continue
        busy = blockers(rows, os.getpid())
        if not busy:
            print("M3 process check: no foreign selftest/build/deploy", flush=True)
            return
        if time.monotonic() - started >= 180 * 60:
            raise SystemExit("M3 remains busy after 180 min: " + ", ".join(map(str, busy)))
        print("M3 busy; waiting 120s, foreign process IDs: " + ", ".join(map(str, busy)), flush=True)
        time.sleep(120)


if __name__ == "__main__":
    wait()
