# CloakData: Making configurable privacy transformations safer

CloakData is a Python library that transforms columns in Polars DataFrames.
The engineering challenge was to make declarative rules compose reliably while
preserving the callable contract for custom transformations and the behavior of
existing valid configurations.

## From reproduction to design

An existing test applied two constant replacements to the same column. It
verified which rule won, but it could not tell where the second rule read its
input. A regression test replaced a synthetic identifier with `SAFE`, then
truncated it. The original engine returned `SEC` from `SECRET`. This was
data exposure for callers who reasonably assumed rule composition.

The revised engine builds a separate lazy projection per rule in a column
chain. Predicates still evaluate against the input snapshot, which preserves
the behavior of existing conditional policies. Other columns also read the
input snapshot. Predicates live outside the staged frame. Review found that a
custom selector could otherwise read an internal predicate as a consent flag.
Regression tests exercise custom selectors before and after another rule and
preserve the legacy behavior that `is_false` matches null flags.
A custom method or native strategy that inspects values gets
a real DataFrame at its point in the chain. This choice allows Polars to
optimize expression-only stages while retaining the custom extension API.

The execution engine and public validator share parsing. Unknown methods,
missing unconditional targets, and malformed nested conditions fail with
context. Regex parameters compile using Polars during validation, so invalid
patterns fail before any input rows are evaluated. The registry is process-local
and snapshots registrations for each
call. Tests cover the distinction between rejected configurations and valid
rules that fail on incompatible data.

## Privacy model

Stable identifiers are useful for joins, but ordinary salted hashes are
guessable when recipients know the salt and the input space is small. The
new HMAC-SHA256 strategy uses caller-controlled secret bytes. It protects
against offline guessing under that assumption while still exposing equality
and frequency. Existing digest formats remain usable, and the documented
null-handling option now takes effect. The library does not determine whether a
released dataset can identify someone or establish GDPR or LGPD compliance.

## Measurement and trade-offs

The [benchmark](docs/benchmarks.md) used five independent processes per case
at 10,000, 100,000, and 1,000,000 rows. Workers verified every row against a
Python reference after measuring wall time and process peak memory. At one
million rows, length-preserving masking fell from 585.13 ms to 42.62 ms with
about 19 MiB more peak working set. Salted SHA-256 fell from 885.21 ms to
669.76 ms with little change in memory. HMAC took 1,642.39 ms at the same
scale. A truncate-and-mask chain took 32.40 ms where two baseline calls
produced the same result in 392.49 ms.

A public LazyFrame API could help with scan-based pipelines and pushdown.
Several installed strategies and the custom-method contract require eager
data access, though. The change keeps internal laziness where it helps and
defers new public semantics until a streaming use case can define the contract.
For larger workloads, a future benchmark could compare a reviewed native
cryptographic plugin, including its platform support and key-handling costs.

## Verification

Regression tests cover composition, data-dependent custom methods, invalid
conditions and parameters, Unicode, empty data, nulls, and independent HMAC
keys. CI checks lint, tests with branch coverage enabled, and packaging on
Python 3.12 and 3.13. Inspecting an initial wheel exposed a packaging defect:
the build succeeded but shipped only the typing marker. Correcting Hatch's
file selection and testing both installed distributions in CI verifies the
artifacts a user receives. Publication reuses the full CI matrix at the exact
release commit and consumes the validated artifacts from that run. The
[engineering assessment](docs/engineering-assessment.md) records the baseline
and the priority of each change.
