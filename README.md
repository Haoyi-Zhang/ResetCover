# Identifiability certificates for finite experiment systems

This standalone repository contains the bounded reference semantics and reproducible finite evidence for **Ambiguity Supports for Reset-Limited Experiments: A Vertex-Cover Boundary**. It does not require the manuscript directory or network access.

## Reproduce

From the repository root:

```sh
python3 reproduce.py --output reproduced --check
```

The output directory must not already exist. The command verifies all 48 retained main packets, reruns the independent tiny oracles, graph and rank-three hypergraph checks, binary reset-budget comparisons, directed mutations, malformed-input controls, and conservative cap controls. With `--check`, it compares every deterministic scientific JSON/CSV output and every certificate packet byte-for-byte against `results/`; timing, memory, and run-status records are intentionally excluded.

Check one retained certificate directly:

```sh
python3 check_certificate.py \
  inputs/graph-triangle-budget-1.json \
  results/certificates/graph-triangle-budget-1.json
```

The runner uses only Python's standard library. It applies a 2 GiB address-space limit, 180-second CPU/wall limits, and explicit node/obligation caps. A cap breach returns `unknown`; it is never converted into an optimal depth or ambiguity certificate.

## Trust boundary

`src/solver.py` constructs the reachable belief game and emits rank/trap packets and, when available, a strategy DAG. `src/checker.py` reconstructs transitions from raw input machines; it does not import the solver or its transition builder. Positive replay checks an upper bound. Exact optimality or impossibility additionally requires the all-actions rank/trap conditions.

`tests/oracles.py` supplies four structurally separate finite baselines: direct unary output-prefix/product reasoning; an explicit-position Bellman recursion for fixed-seed stateful families; exhaustive graph/hypergraph support predicates; and strict-subset one-shot decision-tree recursion. `tests/mutations.py` corrupts certificate rules, strategies, pair witnesses, and raw models and requires rejection. Producer and checker also reject a fixed malformed-input suite. These programs were developed in one research process; software separation is not independent human or blind review.

## Mathematical scope

`proofs/theorems.md` gives the complete model and arguments independently of the article. The central results are:

- one collision pair per test yields a unique forced ambiguity support;
- at most two pairs yields a forced set plus exact vertex covers;
- at most `p` pairs yields a rank-`p` hypergraph-transversal instance and an `O(p^k 2^p |A| poly(|H|+|A|))` bounded-search algorithm for the explicit zero-reset class;
- every nonempty graph has a two-state realization whose minimum zero-reset support is vertex cover while one reset identifies the full family in depth three;
- binary serialization preserves every support's reset feasibility, not action depth; and
- the sharp one-shot support bound is `q^(r+1)+1`, while no bound depending only on `r` survives for general binary stateful epochs.

These are mathematical proofs, not proof-assistant formalization. Finite results validate bounded instances and certificate semantics rather than universal quantifiers.

## Evidence inventory

- `inputs/`: the 48 retained families and catalog.
- `results/certificates/`: one checked rank/trap packet per main family, plus successful strategy and rooted-pair witness where applicable.
- `results/*.json` and `main_results.csv`: raw scientific counters, oracle results, mutation/input controls, resource measurements, clean-reproduction record, and cumulative campaign accounting.
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
