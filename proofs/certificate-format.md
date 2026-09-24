# Model and certificate encoding

## Explicit family

A family is a JSON object containing `actions`, `observations` and `machines`. Actions are distinct nonempty strings of at most 80 characters. Observations are distinct integers, not Booleans. Machine position in the array is the hypothesis identity. Each machine has an integer `initial` and a `table`. Table row is current state; column is ordinary action; a cell is `[output, next_state]`. Both values must be declared and in range. A metadata/name field has no transition semantics.

The implicit reset has action index `len(actions)`, emits integer zero (even when zero is not an ordinary observation label), and returns each surviving identity to its own initial state. It never adds an eliminated identity. It consumes one depth unit and one finite-budget unit. The tables need not supply a reset column. This convention also prevents output-zero being confused with an ordinary action: the action is part of the history.

## Rank/trap packet

A `rank_trap` certificate has a root row index, a nonempty `support` array of distinct hypothesis indices, `resets`, and `rows`. `resets: null` means unlimited reset; otherwise it is an integer in 0–12. A row has a `belief` array, a remaining `budget`, a `rank`, and an `action`. Each belief coordinate is its surviving machine state or minus one for an absent identity. The support of every row is a subset of the initial support. Unlimited-budget rows use minus one for the budget. Rank null means losing; rank zero means exactly one survivor. Finite positive ranks are integers smaller than the number of rows.

Ordinary successors are reconstructed by grouping each surviving identity according to its actual output, advancing its state, and retaining only the chosen output group. A legal reset successor preserves the current support, restores the initial states, and decrements finite budget. Terminal rows have no further obligations. Every nonterminal reconstructed successor must be present; rows must be unique and all reachable from the initial root.

For finite positive rank k, the chosen action must have only finite successors of rank at most k−1, and every action must have some successor with rank at least k−1, treating losing rank as infinity. A losing row must have a losing successor for every action. Singleton and losing rows have no chosen strategy action. These local rules prove both the upper and lower bound; checking only the selected action would not prove optimality.

## Strategy and pair witnesses

A successful packet also has a strategy DAG whose nodes reference game-row indices. Internal nodes supply an action and output/child edges; terminal nodes name a hypothesis. Replay follows the table separately for every fixed identity, checks reset consumption, rejects cycles and missing observed branches, checks correct terminal identity, and requires the worst replay depth to equal the checked root rank. The rank certificate must be checked first. `replay` is not a standalone structural validator for an arbitrary unvalidated game object.

A `rooted_pair` witness names two distinct hypotheses and a duplicate-free finite relation of state pairs. The initial pair must be present. Every ordinary action must produce equal outputs and a successor pair in the relation. Reset closure follows from containment of the initial pair. This proves unlimited-reset ambiguity, so it also proves ambiguity under any smaller reset budget containing both identities. It is not required for a losing finite-reset game, where no such rooted pair may exist.

## Size and trust

The family reader caps bytes at 4 MiB; the direct command-line checker caps a packet at 32 MiB, rank rows at 250,000 and reconstructed successor obligations at 2,000,000. A complete mathematical certificate can exceed those implementation limits and be rejected for size. The retained suite is much smaller. State coordinates need at most five signed bits at the declared state cap, identity indices five bits, finite reset counts four bits and row/rank indices eighteen bits. JSON adds textual overhead. Retained files use small integer labels; the parser byte cap bounds their actual encoding.

There is no solver call or solver import in the checker. This is implementation separation, not a claim of independently conceived science, secure parsing, formal verification of Python, or proof-assistant checking of the general theorems. Extra strategy branches not traversed by any actual hypothesis do not change an accepted strategy's semantic guarantee; reached-node and duplicate-observation rules still apply. All substantive claims concern the parsed mathematical object, not byte canonicalization or minimum certificate size.
