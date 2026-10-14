# Symbol costs of reset-preserving one-shot serialization

## Domain and three policy classes

The source is a total deterministic canonical one-shot table: each candidate
has fresh state 0, every query enters spent state 1, and every spent action
emits zero and stays spent. Identity is fixed. Reset returns each surviving
candidate to its own initial state, costs one symbol, and consumes one reset
unless the budget is unlimited. All candidates, the table, the retained
nonempty support J, the budget, and the same binary coding are known to every
controller. There is no information advantage for the bit-level controller.

For m source queries and q declared outputs, let ell=max(1,ceil(log2 m)) and
c=max(1,ceil(log2 q)). Selectors have ell constant-output inputs. Codes are
indices in the declared observation list, read least-significant bit first.
The implementation's finite domain remains unchanged: n<=24, actions<=8,
states<=16 per encoded machine, and exact rank depth<=12. These caps do not
restrict the mathematical statements, and a cap refusal is not ambiguity.

For an identifiable nonsingleton support, tau is the smallest worst-case
number of informative source queries among policies using at most r resets.
Normal form omits uninformative queries and terminal resets, hence the source
action depth is 2*tau-1. Three encoded classes are compared:

* whole: every issued source query reads its full c-bit result;
* prefix: read until the source output is unique among possible outputs on
  the current support, then stop or reset and choose another query;
* bit: all legal encoded policies, including resetting while several source
  outputs still share the observed prefix.

An identifying terminal has a unique identity. In the whole class the full
result is read even if that identity became known earlier; this intentional
restriction makes it a completion baseline, not the strongest ordinary policy.
The prefix class is an ordinary exact prefix-decoding baseline. Neither
baseline is a novel mechanism, nor an execution of CAMUS or Action Codes.

## Exact macro recurrence

For action a, partition K by source output o into C_o. Ignore actions with a
single nonempty cell. Whole uses d(a,o,K)=c. Prefix uses the smallest d>=1
such that the low d code bits of o differ from those of every other possible
output on K. Define F(K,b)=0 when |K|=1. Otherwise

    F(K,b) = min_a max_o [ell+d(a,o,K)+ continuation(C_o,b)],

where continuation is zero on a singleton, is 1+F(C_o,b-1) on a nonsingleton
with b>0, is 1+F(C_o,infinity) with unlimited budget, and is infinity otherwise.
An action is infeasible when any branch has infinite continuation. A strict
cell shrinks K, so recursion is well-founded even for unlimited reset.

Each prefix requires exactly d reads to determine its output; the remaining
coordinates are in the corresponding response phase. A nonsingleton cannot
issue another source query without resetting. This proves that every policy
in its class obeys the recurrence's lower bound. Conversely, choose its
minimizing action and use its recursive branch policies. They are legal from
fresh state and, following a partial response, reset is legal from that state.
This proves the recurrence exact within each class. It is not an optimality
claim for all encoded policies or general stateful input families.

## Cost sandwich

For every identifiable nonsingleton J and finite or unlimited r,

    tau*(ell+2)-1 <= V_bit <= V_prefix <= V_whole
                   = tau*(ell+c+1)-1.

Singletons have all three depths zero and are excluded from the displayed
formula. Losing families have no finite tau; the inequality is not a numerical
formula for them.

Proof of the upper bound and equality for whole: simulate a query tree, reading
ell+c symbols per query and resetting between its consecutive queries. A path
of t queries costs t*(ell+c+1)-1. Since this is a strictly increasing affine
function of t, minimizing its worst-case cost is equivalent to minimizing t.
Prefix is legal in the bit game. Every whole policy can be shortened at its
uniquely decodable prefixes without extra resets, proving the two dominance
inequalities; an obligatorily completed read is not itself a mandatory-stop
prefix policy.

For the lower bound, normalize an arbitrary successful encoded policy without
increasing its cost or resets. Remove epochs that perform no response read:
selection, invalid selection, and abort yield only constant observations, so
the subsequent fresh-state policy can be used directly with at least as much
remaining reset budget. Remove redundant spent-state inputs. Each remaining
epoch contains a complete valid selector and at least one response read.
Convert this policy to a source-query tree: once the selector is complete,
issue that query, retain its entire source output internally, and reveal only
the prefix bits that the encoded policy asks for. Mirror its resets and stop
at the same identity. Extra internally available output information does not
force the simulation to use it. The source tree is successful with the same
reset bound, so one of its paths has at least tau useful queries. The
corresponding encoded path costs at least tau*(ell+1) plus tau-1 resets.
This is tau*(ell+2)-1. When c=1 both ends coincide, so all three depths agree.

No assertion is made that the lower bound is attained for every table, that
bit strictly improves on ordinary prefix decoding, or that fewer symbols
improve elapsed time, memory, or deployment behavior. The result is a cost
connection for this concrete coding and reset semantics. Action refinement
and adaptive code mechanisms are already prior work; the closest-work audit
does not establish priority for this corollary.

## Executable connection and trust assumptions

`policies.py` implements the recurrence directly from source tables without
importing the solver or binary transition builder. `study.py` solves the
encoded belief game and checks its rank/trap packet before using the bit DAG.
Its interactive controllers choose from observed outputs and the shared model,
not from the fixture identity. `OwnedMachine.cs` is a complete compiled managed
.NET Framework process that reads the generated transition table, keeps one
identity, and implements ordinary actions/reset. It is not AOT native code or
third-party software. This finite table interpreter validates the model-to-
process connection under trusted compiler/CLR/OS and ordinary pipe operation;
it does not validate a physical device, faults, noisy outputs, or a deployment.

Native receipts retain all identity branches, not just a successful example.
Independent verification reconstructs every transition, remaining budget,
surviving belief, terminal answer, and worst-depth maximum from raw receipts.
Process startup, full pipe interaction/exit wall time, self CPU and peak
working-set counters are separate from planning/checking cost. Peak working
set includes shared CLR/library pages, not just private allocation. CPU tick
units do not imply measurement precision. Logical file sizes are not allocated
disk footprint. Python peak memory and OS CPU/address-space limits are not
measured/installed by the portable Windows module runner.
