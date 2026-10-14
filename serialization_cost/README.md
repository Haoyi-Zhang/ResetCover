# Serialization cost experiment

This study connects the explicit one-shot table to a complete owned compiled
managed Windows process and compares three equal-information controllers.
It does not execute prior software or a physical device.

## Reproduction

Dependencies for the owned process: Windows, the installed .NET Framework C#
compiler/CLR, and CPython 3.12. The solvers/controllers/verifier use the Python
standard library. Figure regeneration additionally uses Matplotlib 3.10.7 and
its FontTools dependency (4.66.1 in the recorded environment). With the installed
TeX Gyre Termes CFF OTF supplied through `plot.py --font`, the plotter converts
the same face to temporary TrueType outlines for embedded Type42 PDF text;
character mapping, advance widths and copyright metadata are retained. This
does not change plotted observations or run an experiment, install a font, or
distribute a converted font file. TeX Gyre retains its GUST Font License.
No package installation, networking, privileged operations, or external solver
is required. The classical POSIX runner and its real resource limits remain
separate; `portable_reproduce.py` invokes its module with an explicit Windows
measurement profile and requires an owned parent timeout. It does not pretend
to install POSIX limits.

Use a fresh owned output directory. Compiler path and output path are explicit;
classic `csc.exe` needs Windows backslash paths (the retained failed forward-
slash invocation was not a source/program failure).

```powershell
& 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe' /nologo /optimize+ /platform:x64 /warnaserror+ /out:OWNED_OUTPUT\OwnedMachine.exe .\serialization_cost\OwnedMachine.cs
python -B -S serialization_cost/study.py --out serialization_cost/NEW_NORMAL --exe OWNED_OUTPUT/OwnedMachine.exe
python -B -S -O serialization_cost/study.py --out serialization_cost/NEW_OPTIMIZED --exe OWNED_OUTPUT/OwnedMachine.exe
python -B -S serialization_cost/verify.py --normal serialization_cost/NEW_NORMAL --optimized serialization_cost/NEW_OPTIMIZED --out OWNED_OUTPUT/verification
```

Run from `artifact/`. Replace OWNED_OUTPUT with a directory you own. The verifier
binds results within the project tree; its data paths should therefore be in
this tree. Every owned process read/exit has a five-second timeout and a 64-step
bound. For whole-run resource control, call these commands through an owned
parent with `subprocess.run(..., timeout=180)` or equivalent. The retained
campaign did so for each invocation. A manually run module alone has no
independently enforced whole-process wall or memory limit.

The process table is a separate simple integer format generated from the full
encoded JSON: hypothesis count, action count, then each machine's state count,
initial state and all output/target pairs in row-major order. It does not
replace the existing certificate JSON or its reset convention. The compiled
program keeps a fixed identity; command 2 resets to its own initial state and
decrements only its remaining finite reset budget. No OS state is reset.

## Contract and cohorts

`proofs/serialization-cost.md` states all mathematical premises. `policies.py`
contains an exact source-table recurrence for whole-result and ordinary prefix
decoding; neither imports the producer's transition construction. `study.py`
uses the checked bit-game certificate for that arm. All arms share complete
table knowledge, support, budget, observation-code order and exact output
semantics. Controllers never choose actions from the known fixture identity;
that identity is used for process initialization and final ground truth only.

The 258-case tiny cohort is 246 exhaustive configurations plus twelve fixed
seeds. It is not an exhaustive census of the executable domain. The process
catalog has 37 configurations, with 22 identified, 14 ambiguous and one depth-
cap unknown. Native process receipts cover only the 22 **common admitted**
configurations, all their identities and two repetitions per arm: 176 runs
per arm, 528 per Python mode. The excluded 15 configurations remain in raw
inputs/plans/configs; they are not counted as failed or successful process runs.

## Results and negative

The same semantic results hold in ordinary and optimized Python. Each mode has
2,894 actual operations and zero reconstructed trace mismatches. Prefix improves
worst depth over whole in 11/22 common admitted configurations, whereas bit
improves over prefix in **0/22**. The tiny cohort likewise has ten whole-to-
prefix improvements and zero prefix-to-bit improvements among its 72 identified
cases. Ordinary prefix decoding accounts for every observed worst-depth gain.
No new decoding algorithm or benefit over CAMUS/Action Codes is claimed.

Total process operations per mode are whole 1,046, prefix 916, bit 932. The bit
solver minimizes worst depth, not aggregate work; a tie-selected policy can
therefore do more total work than the prefix arm. Planning wall totals over all
37 configurations are 2.144/2.894/43.585 ms (normal whole/prefix/bit), and
2.068/2.882/44.404 ms (`-O`). Rank-check totals are 13.871/14.372 ms. These are
small deterministic fixtures, not scalability or statistical generalization.

Normal full-process wall totals are 3.896/3.891/3.872 s; optimized totals are
3.852/3.853/3.854 s. Their medians are near 22 ms and do not establish a robust
runtime improvement. Startup is included, not subtracted. The self-reported
CPU sample is before END receipt/exit, whereas parent wall time includes exit.
Observed CPU samples are quantized, including zeros. Peak working set includes
shared CLR/library pages and is not exclusive allocation. Parent Python memory
was not measured. Compile invocation costs are separate from repeated process
costs; no amortization or deployment model is assumed.

`verification/verified.json` gives every aggregate, `depths.csv` preserves all
37 configurations, and `raw-bindings.json` binds the 1,358 retained raw study
files (679 per mode). They contain 2,663,552 normal and 2,665,120 optimized
logical bytes. These totals are serialized file lengths, not physical disk
allocation, total compiler installation, retained review workspace, or WAL.
Per-process stdout/stderr/argv/exit and literal before/after beliefs are retained
in 1,056 trace JSONs. `compiler_executable` in the raw summaries names the owned
compiled executable, not the C# compiler; actual compiler version is 4.8.9222.0.

The observed CPU is Intel Core i7-12700KF (12 cores/20 logical processors), OS
Windows 11 Pro build 28000, CPython 3.12.14, CLR 4.0.30319.42000. Python wall and
CPU clocks report QueryPerformanceCounter/GetProcessTimes with nominal 1e-7 s
resolution. No claim about the underlying device clock accuracy is inferred.

## Source boundary

The central zero-reset minimum-support comparison is `support_baselines.py`.
It implements owned exhaustive direct search, maximal-identifiable-set blocker
duality, and existing forced-set/cover selection with the same complete table
and minimum-cardinality guarantee. All 75 cases (71 graphs, three private-pair
and one injective control) agree; 4,388 literal membership comparisons check
the duality, including empty supports. Each arm's 100 repetitions include input
admission, table extraction, transformation, selection and final witness check.
Normal total wall costs are direct 0.264 s, duality 1.305 s, cover 0.283 s;
optimized totals are 0.263/1.303/0.281 s. Fewer selection tests for cover do not
translate into a total-time improvement over direct enumeration here. Raw
records preserve all inputs, all 22,500 timed invocations per mode, counts and
answers in `support-normal/` and `support-optimized/`. Predicate-call counts
are not an equivalent unit to collision-grouping preprocessing, which remains
included in total wall cost. This comparator is not native CAMUS or a large-
instance/SAT/FPT performance claim. To reproduce under an owned parent:

```powershell
python -B -S serialization_cost/support_baselines.py --out serialization_cost/NEW_SUPPORT_NORMAL
python -B -S -O serialization_cost/support_baselines.py --out serialization_cost/NEW_SUPPORT_OPTIMIZED
```

Read the precise current comparison in `proofs/literature-boundary.md` and its
primary links. Action Codes already supplies refinement/adaptive-code concepts.
CAMUS supplies generic MUS/MCS/grouped hitting-set duality. The recorded cost
bound is a specialized connection, not a priority guarantee. Lee--Yannakakis
1994 full text and the Action Codes extended appendices remain uninspected in
this study; native prior implementations and POSIX/remote-CI re-execution also
remain outside its completed evidence.
