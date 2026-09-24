#!/usr/bin/env python3
"""Check a retained certificate directly, without importing the producer."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import resource
import signal
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from checker import check_rank, check_pair, replay, InvalidCertificate


def read_json(path: Path, maximum: int):
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("input byte bound exceeded")
    return json.loads(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    def expired(signum, frame):
        raise TimeoutError("certificate-check wall bound exceeded")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        family = read_json(args.family, 4 * 1024**2)
        packet = read_json(args.packet, 32 * 1024**2)
        if type(packet) is not dict or "game" not in packet:
            raise InvalidCertificate("packet must contain a game certificate")
        report = {"rank_trap": check_rank(family, packet["game"])}
        if report["rank_trap"]["status"] == "identified":
            report["replay"] = replay(family, packet["game"], packet.get("strategy"))
        elif packet.get("strategy") is not None:
            raise InvalidCertificate("losing packet must not contain an identifying strategy")
        if packet.get("unlimited_pair") is not None:
            report["rooted_pair"] = check_pair(family, packet["unlimited_pair"])
        print(json.dumps({"status": "accepted", "checks": report}, indent=2))
        return 0
    except (InvalidCertificate, ValueError, TypeError, KeyError, OSError, TimeoutError, MemoryError) as exc:
        print(f"REJECTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    raise SystemExit(main())
