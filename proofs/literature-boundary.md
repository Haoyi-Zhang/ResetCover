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
| Diagnosis, MUS/MCS, monotone dualization | A smallest core, correction set, or hitting set, including grouped constraints | Generic monotone duality also covers support selection with an appropriate failure predicate; hypotheses and reset-limited game semantics specialize the object, not the dualization mechanism |
| Synchronizing automata | A word that drives states to a common state | Reset here is an external identity-preserving operation, not a synchronizing word |
| Fractal | A system that improves experimental control and reduces noise on real hardware | Only public action-label vocabulary is reused; no trace, processor mechanism, attack, performance, or hardware-fidelity claim enters the model |

## Claims deliberately not made

The review supports a carefully scoped delta, not a universal firstness claim. The manuscript does not assert that no prior paper ever considered a related obstruction subset, that the bibliography is exhaustive, that citation count proves significance, or that a full-paper census substitutes for independent expert review. A closer future result would require revising the positioning, but would not by itself invalidate the stated mathematical implications.

The current journal-specific Guide for Authors could not be retrieved because the first-party page returned a human-verification/403 barrier. Consequently, live page, supplement, source-upload, repository-link, and declaration rules remain an external-use hold. This is separate from the completed scholarly calibration.

## Primary-source comparison for the symbol-cost study

The ICALP 2023 published **Action Codes**, 20 pages, was read through its
references. It defines contraction/refinement, concretization conditions,
composition and adaptors, and explicitly discusses adaptive codes. The longer
arXiv appendices and Coq artifact were not inspected/executed in this study.
Source: <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2023.137>.
The support-wise reset property and cost sandwich are specialized statements,
not evidence that its framework cannot express or adapt to this construction.

The author-hosted CAMUS paper **Algorithms for Computing Minimal Unsatisfiable
Subsets of Constraints**, all 42 PDF pages, was read including Theorem 1,
algorithms, grouped constraints in section 7.2, costs, negatives and references.
This copy is dated 2007-10-10; it is not the exact 33-page JAR 2008 typesetting.
Source: <https://sun.iwu.edu/~mliffito/publications/jar_liffiton_CAMUS.pdf>.
MUS/MCS duality is a direct standard overlap. Let M be the maximal identifiable
supports. A set J fails iff it meets every H\K for K in M, so its minimal
failures are the blocker of those complements. A generic game-predicate oracle
or encoding can therefore cover the outer minimization; collision-rank two
gives the explicit specialized representation. No CAMUS/MiniSAT runtime,
universal novelty exclusion, or superior implementation cost is claimed.

Lee--Yannakakis 1994 full text was not obtained in the current comparison.
The 21-paper retained census and the 67-entry metadata audit are historical
records, not a fresh certification that every primary source was fully read.
The cost experiment's ordinary prefix baseline eliminates all observed
worst-depth differences from the bit game; its negative is retained.
