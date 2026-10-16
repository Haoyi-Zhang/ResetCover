# ResetCover: finite experiment systems

This artifact supplies bounded experiment semantics, reset-limited belief-game
solving, rank/trap certificate checking, strategy replay, and finite reference
oracles for *Ambiguity Supports for Reset-Limited Experiments: A Vertex-Cover
Boundary*. It runs independently of the manuscript directory.

## Requirements

Full reproduction and `check_certificate.py` require POSIX/Linux with CPython
3.10 or later, `resource.RLIMIT_AS`, `resource.RLIMIT_CPU`, and signal timers.
Only the standard library is needed. Portable unit tests also run on Windows.

## Portable tests

From the artifact root:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B -O -m unittest discover -s tests -p 'test_*.py' -v
```

These cover serializer admission, literal finite-game rank/trap comparisons,
row/history binding, and the separate serialization-cost consumer. They are
software regressions, separate from retained campaign denominators.

## Reproduction and direct replay

Choose an output directory that does not already exist:

```sh
python3 reproduce.py --output reproduced
python3 reproduce.py --output reproduced-check --check
```

Fresh generation re-enumerates the 48 main belief games and auxiliary finite
oracles. Retained-output checking binds each existing packet to its catalog
budget and full support, replays it, reruns auxiliary checks, and compares
deterministic scientific JSON/CSV and packet files with `results/`.
The checking route reuses, rather than re-enumerates, the main position graphs.
`resources.json` distinguishes actual enumeration from the retained semantic
count of 2,084 exact-game solves; runtime and host fields are not byte-compared.

Check one retained packet directly on POSIX:

```sh
python3 check_certificate.py inputs/graph-triangle-budget-1.json results/certificates/graph-triangle-budget-1.json
```

The runner enforces 2 GiB address space, 180-second CPU/wall limits, and explicit
node/obligation caps. Cap exhaustion yields unknown rather than a depth or
ambiguity result. The generic checker accepts any admissible support/budget;
the retained-main wrapper additionally requires the exact catalog budget and
full input support. Its replacement guards exercise both distinctions.

The scientific CI runs unit tests in normal/optimized modes, finite generation,
retained-output checking and binding guards on Ubuntu; it uploads raw logs after
failure as well as success. Consult the current Actions runs for execution status.

## Model and checking boundary

`src/solver.py` constructs belief games and emits rank/trap packets and strategy
DAGs. `src/checker.py` reconstructs raw transitions without importing the solver
or its transition builder. Strategy replay gives an upper bound; exact depth
or impossibility additionally requires all-action rank/trap obligations.
`tests/oracles.py` implements four finite baselines, and `tests/mutations.py`
checks rejection of corrupted models and evidence.

Binary serialization accepts the canonical one-shot two-state realization:
initial state zero, fresh actions enter state one, and spent actions emit zero
and remain there. It preserves support/reset feasibility, not action depth;
general reusable or stateful experiments require the general game model.

The written proofs are mathematical arguments rather than proof-assistant
formalizations. Producer/checker source separation is not independent human
review. Public-vocabulary fixtures are relabeled authored archetypes, not device
traces or held-out deployment data.

## Material map

- `figures/draw_schematics.py`: Python-direct cover and serialization vector
  diagrams; run with `--outdir PATH`. Requires Matplotlib, embeds STIX fonts,
  checks label bounds and does not execute an experiment or call TeX.
- `inputs/`: the 48 retained families and catalog.
- `results/certificates/`: packets, strategies, and rooted-pair witnesses.
- `results/`: scientific tables, auxiliary controls and actual run/resource records.
- [proofs/theorems.md](proofs/theorems.md): model and support/reset results.
- [proofs/certificate-format.md](proofs/certificate-format.md): encoding and obligations.
- [serialization_cost/README.md](serialization_cost/README.md): equal-information
  complete-result, prefix, and bit-game cost comparison, interpreter and verifier.
- `claim_evidence_ledger.csv`: claim/proof/check/output mapping.
- `reference_audit.csv`, `literature_census.csv`, `external_resources.csv`,
  and [proofs/literature-boundary.md](proofs/literature-boundary.md): source and
  comparison records with their stated reading scope.

The serialization study attributes its observed depth improvement to ordinary
prefix handling; it records no additional bit-over-prefix benefit. Its counts
are separate from the historical 2,084-game summary. Runtime reproduction files
record the actual current host; missing historical environment fields remain
unknown.

## License and provenance

Original code, authored inputs, proofs, and documentation use [LICENSE](LICENSE).
Third-party papers and publisher assets are cited rather than redistributed.
Finite results come from executed programs. Human approval and external review
are separate from these checks.
