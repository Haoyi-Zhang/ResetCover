"""Strict explicit finite-family input model. No target or network interaction."""
from __future__ import annotations
import json
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024

def integer(x):
    return isinstance(x, int) and not isinstance(x, bool)

def validate(f: dict) -> None:
    if not isinstance(f, dict):
        raise ValueError("family must be an object")
    acts = f.get("actions")
    obs = f.get("observations")
    ms = f.get("machines")
    if not isinstance(acts, list) or not 1 <= len(acts) <= 8:
        raise ValueError("one to eight ordinary actions required")
    if any(not isinstance(a, str) or not a or len(a) > 80 for a in acts) or len(set(acts)) != len(acts):
        raise ValueError("action labels must be distinct short strings")
    if not isinstance(obs, list) or not 1 <= len(obs) <= 8 or any(not integer(o) for o in obs) or len(set(obs)) != len(obs):
        raise ValueError("one to eight distinct integer observations required")
    if not isinstance(ms, list) or not 1 <= len(ms) <= 24:
        raise ValueError("one to twenty-four hypotheses required")
    for m in ms:
        if not isinstance(m, dict):
            raise ValueError("machine must be an object")
        t = m.get("table")
        if not isinstance(t, list) or not 1 <= len(t) <= 16:
            raise ValueError("one to sixteen states per machine required")
        if not integer(m.get("initial")) or not 0 <= m["initial"] < len(t):
            raise ValueError("invalid initial state")
        for row in t:
            if not isinstance(row, list) or len(row) != len(acts):
                raise ValueError("incomplete action row")
            for edge in row:
                if not isinstance(edge, list) or len(edge) != 2:
                    raise ValueError("transition is [output,next_state]")
                o, s = edge
                if not integer(o) or o not in obs or not integer(s) or not 0 <= s < len(t):
                    raise ValueError("transition outside the declared model")

def load(path: str | Path) -> dict:
    p = Path(path)
    with p.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input byte limit exceeded")
    f = json.loads(raw)
    validate(f)
    return f
