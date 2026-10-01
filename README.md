# Identifiability certificates for finite experiment systems

This standalone repository contains the bounded reference semantics and reproducible finite evidence for **Ambiguity Supports for Reset-Limited Experiments: A Vertex-Cover Boundary**. It does not require the manuscript directory or network access.

## Runtime requirements

The documented bounded runner targets **POSIX/Linux with CPython 3.10 or newer**. It uses only the Python standard library, but it requires `resource.RLIMIT_AS`, `resource.RLIMIT_CPU`, `signal.SIGALRM`, and `signal.setitimer`; the documented command is therefore not claimed to work on Windows or on non-POSIX Python implementations that omit those facilities. One fresh finite validation records the actual Python implementation/version and platform in `results/runtime_reproduction.json`. The older retained-generation timing file did not capture its OS or Python version, so those original environment fields are reported as unknown rather than inferred.

## Reproduce

From the repository root, a fresh generation is:

```sh
python3 reproduce.py --output reproduced
```

This path re-enumerates the 48 main belief games and all auxiliary finite oracles. Its retained scientific summary contains 2,084 exact-game solves.

For retained-output verification, run:

```sh
python3 reproduce.py --output reproduced-check --check
```

The output directory must not already exist. In `--check` mode the runner **does not re-enumerate the 48 retained main position graphs**. It first binds each retained packet to the catalog budget and the full input support, validates the packet with the separate checker, reruns the auxiliary tiny/oracle/construction/mutation/input/cap checks, and compares every deterministic scientific JSON/CSV output and all 48 packet files byte-for-byte against `results/`. `resources.json` separately reports the games actually enumerated by that invocation and the retained semantic count; timing, memory, platform, and run-status records are intentionally excluded from byte comparison.

A pre-change read-only audit found that all existing 48 packets already matched their catalog budgets and full supports; the defect was a latent entry-contract risk, not evidence that a retained scientific result was wrong. The current `--check` invocation now runs two explicit replacement guards. A complete valid certificate for the same transition table but the wrong budget, and a complete valid strict-subset certificate for the target budget, are each accepted by the generic checker and then rejected by the retained-main binding wrapper. The diagnostic echoes the target and replacement budgets and supports. A separate `m=1` private-pair negative control checks budgets 0, 1, and unlimited. The one strict-subset construction plus these three negative-control games are software guards outside the retained 2,084-game scientific count.

Check one retained certificate directly:

```sh
python3 check_certificate.py \
  inputs/graph-triangle-budget-1.json \
  results/certificates/graph-triangle-budget-1.json
```

The runner applies a 2 GiB address-space limit, 180-second CPU/wall limits, and explicit node/obligation caps. A cap breach returns `unknown`; it is never converted into an optimal depth or ambiguity certificate.

## Trust boundary

`src/solver.py` constructs the reachable belief game and emits rank/trap packets and, when available, a strategy DAG. `src/checker.py` reconstructs transitions from raw input machines; it does not import the solver or its transition builder. Positive replay checks an upper bound. Exact optimality or impossibility additionally requires the all-actions rank/trap conditions. The checker deliberately remains generic and can validate a legal certificate for any nonempty support and allowed budget. Only the retained-main entry in `reproduce.py` adds the catalog-specific requirement that the packet budget match the catalog budget and that its support contain every input hypothesis.

`tests/oracles.py` supplies four structurally separate finite baselines: direct unary output-prefix/product reasoning; an explicit-position Bellman recursion for fixed-seed stateful families; exhaustive graph/hypergraph support predicates; and strict-subset one-shot decision-tree recursion. `tests/mutations.py` corrupts certificate rules, strategies, pair witnesses, and raw models and requires rejection. Producer and checker also reject a fixed malformed-input suite. These programs were developed in one research process; software separation is not independent human or blind review.

## Mathematical scope

`proofs/theorems.md` gives the complete model and arguments independently of the article. The central results are:

- one collision pair per test yields a unique forced ambiguity support;
- at most two pairs yields a forced set plus exact vertex covers;
- at most `p` pairs yields a rank-`p` hypergraph-transversal instance and an `O(p^k 2^p |A| poly(|H|+|A|))` bounded-search algorithm for the explicit zero-reset class;
- every finite simple graph with at least one edge has a two-state realization whose minimum zero-reset support is vertex cover while one reset identifies the full family in depth three;
- for the private-pair family, one reset identifies the full family only when `m>=2`; the `m=1` pair remains ambiguous for every finite budget and with unlimited reset;
- binary serialization preserves every support's reset feasibility for finite and unlimited budgets, not action depth; and
- for each finite `r` the sharp one-shot support bound is `q^(r+1)+1`, while no bound depending only on that finite `r` survives for general binary stateful epochs. With unlimited reset, ambiguity contains an equivalent rooted pair and hence a size-two support.

These are mathematical proofs, not proof-assistant formalization. Finite results validate bounded instances and certificate semantics rather than universal quantifiers.

## Evidence inventory

- `inputs/`: the 48 retained families and catalog.
- `results/certificates/`: one checked rank/trap packet per main family, plus successful strategy and rooted-pair witness where applicable.
- `results/*.json` and `main_results.csv`: raw scientific counters, oracle results, mutation/input controls, resource measurements, clean-reproduction and runtime/platform records, plus the frozen scientific-campaign accounting with its explicit cutoff.
- `claim_evidence_ledger.csv`: material claim to proof/check/result/display mapping.
- `reference_audit.csv`: all 67 manuscript references, thematic category, cited status, metadata basis, reading scope, verification state, and redistribution boundary.
- `literature_census.csv`: the 12 same-venue, 5 influential, and 6 adjacent-venue full-paper calibration, including exact-version notes and comparison fields.
- `external_resources.csv`: scholarly and official resources actually accessed; no third-party article text is included.
- `proofs/certificate-format.md`: packet encoding and checker obligations.
- `proofs/literature-boundary.md`: object-level closest-work comparison, completed census boundary, and external-use caveats.

The 16 public-vocabulary fixtures are four authored semantic archetypes under four relabelings. They contain no device trace and establish no hardware mechanism. Inputs were visible during development; there is no held-out statistical-generalization claim.

## License and provenance

The implementation, authored inputs, proofs, and documentation in this standalone repository are released under the MIT license in `LICENSE`. Cited papers, publisher assets, and third-party text are not included or relicensed.

Automated assistance contributed to formulation, proof drafting, implementation, manuscript preparation, and TikZ sources. Finite results were obtained by running the retained programs, not by predicting outcomes. No human author approval, independent external review, submission, acceptance, or guaranteed novelty is asserted. External use requires substantive human review and truthful compliance with the live venue and publisher rules.
