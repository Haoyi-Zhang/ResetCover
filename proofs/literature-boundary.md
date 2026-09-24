# Literature boundary and calibration record

## Bibliography gate

The manuscript bibliography contains **67 scholarly works and every entry is cited in the body**. No `\nocite` command is used. The reference checker enforces a minimum of 55 entries, exact equality between defined and cited BibTeX keys, required fields by entry type, four-digit years no later than 2026, no duplicate normalized titles, no duplicate or malformed DOI values, and exact key agreement with `reference_audit.csv`.

| Literature line | Count |
|---|---:|
| State identification and FSM testing | 20 |
| Active automata learning and successful discrimination | 17 |
| Decision trees and query optimization | 8 |
| Partial-information games, antichains, and equivalence | 12 |
| Synchronization and reset automata | 4 |
| Minimal explanations, complexity, and application boundary | 6 |
| **Total** | **67** |

`reference_audit.csv` records the bibliographic basis, reading scope, verification status, and redistribution boundary for every key. Citation-level screening is not labeled as a complete reading. Cited articles are not redistributed.

## Full-paper calibration

`literature_census.csv` records a structured complete-text review of **21 unique full papers**:

- 12 articles from Information and Computation or its predecessor Information and Control;
- 5 influential full papers; and
- 6 adjacent-venue full papers.

Angluin (1987) and Kanellakis--Smolka (1990) intentionally count in both the same-venue and influential cohorts; their overlap reasons are stated in the census. The latter is marked influential because the work received the 2021 Dijkstra Prize, not because of an inferred award. Berndt et al. (2022) is the sole exact-version caveat: its complete 26-page ECCC version was reviewed and cross-checked against the journal metadata because the exact journal typesetting was unavailable. It is not described as a page-for-page reading of the publisher PDF.

For every census row, the retained fields record: exact version, sections inspected, motivating problem, general principle, proof/performance argument, practical connection, evaluation breadth, artifact strength, narrative sequence, section pattern, bibliography role, figure/table role, and the precise delta to this work. Metadata-only records do not count toward the 12/5/6 totals.

## Object-level closest-work comparison

| Prior line | Object selected or constructed | Boundary relative to ambiguity supports |
|---|---|---|
| Moore, Gill, Lee--Yannakakis, FSM testing and ADS work | A successful distinguishing/identifying word, tree, sequence, or suite | The present variable is the retained hypothesis set of a failing instance, not the test |
| Angluin, Gold, Rivest--Schapire, apartness and later active learning | A learned automaton, observation structure, counterexample transcript, or separating evidence | The candidate family here is explicit; no unknown transition structure is learned |
| Hyafil--Rivest and optimal-query work | A successful decision policy minimizing depth or cost | The graph reduction makes the next-budget positive strategy uniformly depth three while the smallest zero-reset negative support is hard |
| Reif, Berwanger et al., De Wulf et al., symbolic model checking | A winning strategy, losing region, fixed point, or compact belief representation | The belief game supplies semantics; the extra outer problem chooses a smallest losing subfamily |
| Kanellakis--Smolka, Joyal--Nielsen--Winskel, Bonchi--Pous | A behavioral equivalence or bisimulation/up-to witness | Rooted pair equivalence characterizes unlimited-reset failure only; finite budgets may fail without one global pair witness |
| Diagnosis, MUS/MCS, monotone dualization | A smallest inconsistent, faulty, or explanatory core | The monotone analogy is useful, but clauses arise from experiment collisions and the selected elements are hypotheses |
| Synchronizing automata | A word that drives states to a common state | Reset here is an external identity-preserving operation, not a synchronizing word |
| Fractal | A system that improves experimental control and reduces noise on real hardware | Only public action-label vocabulary is reused; no trace, processor mechanism, attack, performance, or hardware-fidelity claim enters the model |

## Claims deliberately not made

The review supports a carefully scoped delta, not a universal firstness claim. The manuscript does not assert that no prior paper ever considered a related obstruction subset, that the bibliography is exhaustive, that citation count proves significance, or that a full-paper census substitutes for independent expert review. A closer future result would require revising the positioning, but would not by itself invalidate the stated mathematical implications.

The current journal-specific Guide for Authors could not be retrieved because the first-party page returned a human-verification/403 barrier. Consequently, live page, supplement, source-upload, repository-link, and declaration rules remain an external-use hold. This is separate from the completed scholarly calibration.
