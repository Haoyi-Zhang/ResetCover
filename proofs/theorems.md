# Ambiguity supports for reset-limited experiments

These self-contained mathematical arguments accompany the finite checker. They are ordinary proofs, not a proof-assistant development. The article contains all of these acceptance-critical definitions and proofs; no repository-only lemma is required by the article.

## 1. Model and the quantity being minimized

Let H be a finite nonempty set of identities. Identity h has a finite, complete deterministic Mealy machine with states S_h, initial state s_h, ordinary input alphabet A and output alphabet O. Both alphabets are finite and nonempty. Every ordinary state/input pair has exactly one next state and one output. The selected identity is fixed throughout an experiment.

Reset is an additional everywhere-enabled operation when budget remains. It preserves identity, returns its machine to its own initial state and has a hypothesis-independent output. It costs one action and one reset. The first epoch is free of reset cost. A reset budget is a nonnegative integer r or unlimited. A strategy is a finite adaptive action/observation tree. A singleton is identified without an action.

For nonempty J contained in H, Id_r(J) means that such a tree identifies every identity in J with at most r resets on every path. An ambiguity support is a nonempty J for which Id_r(J) is false. Inclusion-minimal means that every proper nonempty subset is identifiable. Minimum means smallest cardinality among all losing subsets. Define mu_r(H) as that minimum, or infinity if there is no losing subset. Restriction of an identifying tree proves that identification is downward closed in J; hence ambiguity is upward closed. Increasing the reset budget cannot hurt.

Identity cannot be quotiented away. Equal spent-state behavior in two machines does not make their initial behavior equal. Reset must restore the correct original root without restoring identities already eliminated by observations.

## 2. Unlimited-reset baseline (article Proposition 3.1)

Two rooted hypotheses are equivalent when every ordinary input word has the same output word in both. A finite relation R between their states witnesses this equivalence when it contains the initial pair and, for every pair in R and every ordinary input, the outputs agree and the next-state pair is in R. Reset closure follows because the initial pair is already present.

If such a pair exists, induction over any adaptive history shows that both identities produce the same observations. Neither ordinary actions nor resets separate them, so the family loses.

Conversely, suppose every rooted pair is inequivalent. Choose two surviving identities, beginning at their initial states, and apply a word that separates them. Every possible resulting output word excludes at least one of the selected two. When more than one identity remains, reset and repeat. Starting with n >= 2 identities, at most n-1 separating words and n-2 resets are needed. If each chosen word has length at most L, the depth is at most (n-1)L+n-2. Thus unlimited-reset identification is equivalent to pairwise rooted inequivalence.

If no separating word exists, all product-state pairs reachable from the initial pair form the required output-agreeing relation. A shortest separating word has length at most |S_i||S_j|: before the final mismatch, repeated product states would permit deletion of a cycle. These are classical baseline arguments, not priority claims.

## 3. Exact game values and checked ranks (article Proposition 3.2 / Theorem 3.3)

A belief B records, for each surviving identity, its unique state after the full observed history. An ordinary input partitions surviving identities by their output and advances each retained state; impossible output branches are absent. Reset keeps the current support, sets its coordinates to the respective initial states and decreases a finite remaining budget. Singleton positions terminate and are not expanded.

For finite r the number of positions is at most

    (r+1) ( product_h (|S_h|+1) - 1 ).

For unlimited reset the budget factor is omitted. This is an exponential bound, not a polynomial algorithm guarantee.

Let W_0 be all singleton positions. Add a position to W_(d+1) when some available action has every possible successor in W_d, also retaining W_d. Induction on d proves that W_d is precisely the set admitting a tree of depth at most d. The first entry rank V is therefore exact minimum worst-case depth. Unentered positions have V=infinity. Finite graphs reach a fixed point; outside it every action has an outside successor.

This trap does not require the adversary to change identity. Along a trap branch, supports are nested and each contains at least two identities. In a finite H they stabilize to a set of size at least two. Every member of the intersection is consistent with the entire sequence of observations and state updates. In particular, every finite proposed tree has a losing branch with at least two identities.

A rank packet lists all reachable nonterminal successors and singleton terminals, with a claimed rank rho per position. The checker reconstructs successors from the raw tables and rejects duplicate, omitted or unreachable rows. The local rank rules are:

* rank zero if and only if the position is a singleton;
* for finite positive k, a selected action has only finite successors of rank <= k-1;
* for that same k, every available action has a successor of rank >= k-1, allowing infinity;
* for infinite rank, every action has an infinite-rank successor.

Induction on finite claimed rank gives V <= rho by following the selected action. Induction on attractor layer gives rho <= V at every winning position. At layer zero the singleton rule suffices. At the next layer an action has all successors in the preceding layer. An infinite claim contradicts its trap obligation; a finite claim greater than the new layer contradicts the all-actions lower bound. The two inequalities prove equality, and an infinite claim cannot lie in the attractor. Actual minimax ranks satisfy all these conditions, proving completeness as well as soundness.

A strategy replayed under each fixed identity proves only a depth upper bound. The all-actions rank checks are indispensable for optimality. A finite reset failure need not have any rooted pair witness. A cap failure is unknown, not an infinite game value.

## 4. One-shot normal form and antichains (article Lemma 4.1 / Proposition 4.2)

An observation table T(h,a) has a two-state realization for each identity: a fresh test emits its table entry and moves to spent; every ordinary action in spent emits a common constant and stays there. Reset restores fresh.

Only the first ordinary action in an epoch can reveal information. Delete subsequent constant-output actions and resets issued while already fresh. Consequently r resets allow at most r+1 useful table queries on a path. Conversely, a table-query tree with at most r+1 queries is realized by resetting between successive queries. For a nonsingleton with minimum finite query depth t, a sufficient reset budget gives minimum action depth 2t-1. The lower bound follows because t useful queries on a worst-case path require t-1 resets; the constructed tree attains it.

In particular, at r=0 a support J loses exactly when every test is noninjective on J. Formally, for every available a there exist distinct h,h' in J with T(h,a)=T(h',a). The colliding pair is allowed to depend on a. Moving the existential pair outside the universal action is invalid.

Let D_t be the inclusion-minimal supports not identifiable with at most t table queries. D_0 is all two-element subsets. Let F_a(t) be members of D_t contained in a single observation block of a. Then

    D_(t+1) = inclusion_minimal { union_a U_a : U_a in F_a(t) for every a }.

If any F_a(t) is empty, the right-hand family is empty. A support J loses within t+1 queries exactly when every first action a has some output block whose intersection with J loses within t queries. That intersection contains a minimal losing U_a. The union of these choices lies in J. Conversely every such union loses, because action a has a branch containing its chosen U_a. Taking minimal members proves the formula. Partial unions containing another partial union can be discarded during construction: further unions preserve inclusion. The number of incomparable sets or join products can be exponential.

## 5. Exact vertex-cover representation (article Proposition 5.1 / Theorem 5.2)

A collision block is an output block with at least two identities. Assume each collision block is a pair, and each test has at most two such pairs. All other blocks are singletons. The table is nonempty in both identities and tests.

An injective test identifies every support, so it rules out ambiguity entirely. Exclude that case. Every one-pair test forces both endpoints into every losing support; let F be the union of these pairs.

For a test with disjoint collision pairs {u,v} and {w,z}, membership of a support in its noninjective subsets has the Boolean condition

    (x_u AND x_v) OR (x_w AND x_z).

It is equivalent to the conjunction of four positive clauses

    (x_u OR x_w), (x_u OR x_z), (x_v OR x_w), (x_v OR x_z).

Indeed, falsifying both conjunctions selects an absent endpoint from each pair and falsifies their cross clause; a false cross clause conversely falsifies both conjunctions. Create the four cross-pair graph edges for every two-pair test, union duplicates, and remove F together with its incident edges. Call the remaining graph G_T on H minus F.

A support J is ambiguous at zero reset if and only if F is contained in J and J minus F is a vertex cover of G_T. Single-pair tests give exactly the forced memberships; two-pair tests give exactly the constructed edge-cover requirements. Edges meeting F are already covered, and all others survive in G_T. It follows that

    mu_0(H) = |F| + tau(G_T),

where tau is minimum vertex-cover size. Removing an unforced identity preserves ambiguity exactly when its removal preserves the cover. Forced identities cannot be removed. Thus inclusion-minimal supports also correspond exactly to inclusion-minimal covers with F adjoined.

The transformation introduces at most four edges per test and is polynomial in the explicit table size. Under the stronger restriction of at most one pair per test, G_T has no edges and F is the unique inclusion-minimal ambiguity support. A single pass extracts F. Large size does not imply hard extraction: m private-pair tests on 2m identities force the entire family, even though every proper subset is identified in one query. For m>=2 the full family is identified with one reset by separating the surviving private pair with a different test.

### Bounded-pair hypergraph form (article Proposition 5.3)

The Boolean derivation extends without changing the one-shot semantics. Suppose every nonsingleton block is a pair and test a has p_a>=1 disjoint collision pairs P_(a,1),...,P_(a,p_a). For each function that chooses one endpoint from every pair of test a, form the set of the p_a chosen endpoints. Let H_T contain every such chosen-endpoint set for every test.

A support J is noninjective for test a exactly when it contains both endpoints of at least one P_(a,i). In indicator notation this is the monotone DNF

    OR_i (x_(i,0) AND x_(i,1)).

By distributivity, this formula is equivalent to the conjunction over all endpoint-choice functions c of the positive clauses

    OR_i x_(i,c(i)).

A clause holds exactly when J intersects its chosen-endpoint set. Therefore every test is noninjective on J if and only if J hits every hyperedge in H_T. Hence the zero-reset ambiguity supports are exactly the transversals of H_T and mu_0(H) is its transversal number.

Test a contributes 2^(p_a) hyperedges, each of size p_a. If every p_a<=p, H_T has rank at most p and at most 2^p|A| edges. For p=1 the singleton hyperedges force the unique union. For p=2, singleton edges are the forced set and the remaining size-two edges are exactly the residual graph construction above.

For the explicit bounded-pair table, the existence of a transversal of size at most k can be decided by the standard bounded-search argument: if an uncovered hyperedge e remains, every solution must choose one of at most p vertices of e. Branch on that choice, delete the hit edges, and recurse at depth at most k. Constructing H_T costs at most 2^p|A| edge generations, so a direct implementation runs in O(p^k 2^p |A| poly(|H|+|A|)). Thus this restricted support problem is fixed-parameter tractable in k+p, and in k for each fixed p. This statement concerns the explicit zero-reset one-shot class only; it is not an FPT result for arbitrary stateful machines or for enumerating all minimal transversals.

The proposition does not cover larger nonsingleton blocks, overlapping collision blocks (which cannot occur in one observation partition), or general stateful epochs.

## 6. Reverse reduction and the easy positive strategy (article Theorem 5.4)

For a finite simple graph G=(V,E) with at least one edge, add anchors a,b to its vertices. The marker test has only collision pair {a,b} and gives a distinct output to each vertex. For each edge {u,v}, add a test with disjoint collision pairs {a,u} and {b,v}; all other blocks are singletons. Edge orientation is arbitrary and only names the endpoints.

The marker forces a,b into a losing support. With both included, the edge test is noninjective precisely when u or v is included. Thus losing supports are exactly {a,b} union C for vertex covers C of G, and their minimum size is 2+tau(G). The four cross edges before forced-set deletion are {a,b},{a,v},{u,b},{u,v}; after deletion exactly {u,v} remains.

Every rooted pair is initially separable. The marker separates all pairs other than {a,b}, and any edge test separates the anchors. Nonetheless no test is injective on the full family, so no-reset identification fails. With one reset, marker/reset/any-edge-test identifies the full family in worst-case depth three. Depth two is impossible: a first ordinary test has a nonsingleton spent branch, and one more ordinary action is constant while one reset yields no information. A reset as the first action is equally unhelpful.

Membership of a proposed zero-reset ambiguity support is checked in polynomial time by scanning output collisions for every test. Hence the size-at-most-k problem for two-pair one-shot tables is in NP. Mapping a vertex-cover instance (G,k) to this table and bound k+2 is a polynomial many-one reduction; edgeless graphs are trivial and may be excluded from the hard subfamily. This proves NP-completeness even with two states per hypothesis, pairwise initial distinguishability and a depth-three full-family strategy at the next reset budget. This is not hardness of finding that positive strategy.

## 7. Binary serialization (article Theorem 6.1)

Let the one-shot table have m>=1 tests and q>=1 distinct response symbols, including its spent output. Choose fixed selector width ell=max(1,ceil(log2 m)) and response width c=max(1,ceil(log2 q)). Both ordinary inputs and outputs of the encoding are {0,1}; reset remains an additional distinguished operation.

During ell selector inputs every output is zero. A valid fixed-width selector chooses exactly one test and enters its response chain. An invalid selector enters the common all-zero spent state. Input zero in the response phase emits its next code bit; after the final bit the machine is spent. Input one aborts, emitting zero and becoming spent. Reset from any phase returns to the initial selector state. The retained implementation uses MSB-first selectors and LSB-first response codes; the proof requires only fixed lengths and injective codes.

For every nonempty J and every finite or unlimited reset budget, identification in the table is equivalent to identification in this encoding. In the forward direction, simulate a query by its selector and full response code, using exactly the original resets.

For the converse, simulate an arbitrary successful encoded strategy. All outputs before valid selection are constant, so the selected test depends only on prior history and known constants. If no valid selection occurs, the entire epoch can be simulated without a table query. At valid selection, make that one table query and use its complete output code to simulate the encoded strategy's requested bits. Extra bits known to the simulator are ignored. Partial reading, early termination, aborts and premature reset are therefore simulated faithfully. There can be no second useful query before reset, since no ordinary transition returns from response/spent to selector. The resulting table strategy uses at most the same number of resets and terminates with the same correct identity.

There are fewer than 2^ell selector states, at most mc response states before suffix sharing, and one spent state. Since 2^ell <= 2m, construction size per hypothesis is O(m(1+log q)). Symbol depth is not preserved: a query expands to several ordinary actions. The asymptotic construction is not bounded by the small executable cap of sixteen states.

Combining this preservation with the reduction gives NP-hardness of minimum ambiguity-support selection for general finite binary machines. It does not give NP membership for those general machines; verifying their loss can require a large belief game.

## 8. Sharp support arity (article Theorem 6.2 / Corollary 6.3)

For one-shot tests with at most q>=2 outcomes and r resets, put t=r+1. Every identifying t-query tree has at most q^t leaves. Any support of size q^t+1 therefore loses; a larger support contains such a proper losing subset and cannot be inclusion-minimal. Thus every inclusion-minimal ambiguity support has size at most q^(r+1)+1.

To attain equality, order n=q^t+1 identities and supply all partitions of the order into at most q consecutive intervals. A query returns the containing interval. The full family loses by capacity. A proper subset has at most q^t members. Divide these ordered surviving members into at most q consecutive groups of size at most q^(t-1), choose interval cuts between groups, and recurse. Such cuts are available even when nonsurvivors lie between groups. Induction on t, with singleton identification at t=0, gives a depth-t tree for every proper subset. The full family is therefore inclusion-minimal losing of size q^t+1. Since q^t+1<=q^(t+1), one additional query/reset suffices for the full family.

Fix r and let q grow. Each resulting full family is the unique minimal losing support, with all proper subsets winning. Binary serialization preserves this statement for every support and the same reset budget. Hence no function of r alone bounds minimal or minimum ambiguity-support arity for general binary finite-state experiments. Their state spaces grow; this does not contradict any fixed-dimensional finite input cap. Binary one-shot outcomes and binary symbol streams inside a stateful epoch have different information capacities.

## 9. Boundaries of the executable evidence

The main suite and tiny exhaustive comparisons test instances of these theorems, not their universal quantifiers. The vertex-cover equivalence is tested for every nonempty support of every nonempty labeled graph on two through four vertices; serialization is additionally tested on four selected graph shapes and their supports. The unary oracle uses pairwise output-stream periods rather than the belief-game algorithm. The one-shot decision-tree oracle recurses on strict subsets and is compared with antichain joins. These are different implementations within one research process, not independent human review.

The general claims require total deterministic transitions, a fixed identity, a reliable identity-preserving reset, nonempty alphabets and finite successful trees. They establish no physical-device, noise, timing, security, conformance-to-hardware or performance property. Literature access and journal-calibration limits are documented separately in `literature-boundary.md`.
