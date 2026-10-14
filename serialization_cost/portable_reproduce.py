"""Explicit Windows module runner, not the POSIX resource-limited CLI.

Run under an owned parent with a timeout. No address-space or OS CPU cap is
claimed. Logical solver caps and per-solve time checks are unchanged.
"""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reproduce


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--check',action='store_true')
    args=ap.parse_args(); out=args.out.resolve()
    if out.exists(): ap.error('new output required')
    out.mkdir(parents=True)
    def measurements():
        return dict(limit_profile='Windows module; owned parent timeout 180s; logical solver caps only; no OS address-space/CPU cap',
                    address_space_limit_bytes=None,os_cpu_limit_seconds=None,peak_rss_kib=None,
                    parent_wall_limit_seconds=180,
                    clocks={k:vars(time.get_clock_info(k)) for k in ('monotonic','process_time')})
    science,metrics=reproduce.run(out,verify_retained_main=args.check,resource_metrics=measurements)
    compared=reproduce.compare_retained(out)
    reproduce.dump(out/'portable_status.json',dict(optimized=not __debug__,check=args.check,
                   compared_scientific_files=compared,science=science,metrics=metrics))
    print(json.dumps(dict(compared_scientific_files=compared,optimized=not __debug__,check=args.check),sort_keys=True))


if __name__=='__main__': main()
