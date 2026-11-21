# Anonymization benchmark

Run from the repository root:

```bash
uv sync --locked --extra dev
uv run --no-sync python benchmarks/benchmark_anonymize.py --repeats 5
```

For a baseline, check out `1152b4b` in a separate directory and set
`PYTHONPATH` to that checkout's `src` when running the same benchmark script.
Leave the benchmark's Python environment and lockfile unchanged. The benchmark
skips HMAC when the imported version does not provide it. Use
`--reference-chain` with the baseline so the truncate-and-mask case makes two
separate calls and produces the same output as the current rule list.

Five independent worker processes per size and case. Each worker creates a frame
with an age column and unique synthetic Unicode identifiers. It times the
transformation and reads peak memory before comparing every output row with an
independent Python reference. A mismatch fails the worker. Neither measurement
includes reference validation. Time also excludes startup and input generation.
Peak resident memory is the maximum of the five process lifetime peaks
(Windows peak working set, or `ru_maxrss` on macOS/Linux). It includes Python,
Polars, the input, and the output. It is not a measurement of allocations
attributable only to the transform. Measurements use Windows 11 x64,
Intel64 family 6 model 186 stepping 2, Python 3.12.9, Polars 1.39.0, and
16 Polars threads. Results depend on machine load, input length, and cardinality.

| Case | Rows | Baseline ms | Updated ms | Baseline peak MiB | Updated peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Length-preserving mask | 10,000 | 7.63 | 3.57 | 59.82 | 59.98 |
| Length-preserving mask | 100,000 | 57.90 | 6.96 | 67.79 | 69.45 |
| Length-preserving mask | 1,000,000 | 585.13 | 42.62 | 148.08 | 166.86 |
| Age generalization | 10,000 | 2.64 | 2.92 | 60.37 | 60.38 |
| Age generalization | 100,000 | 6.72 | 7.82 | 71.86 | 71.81 |
| Age generalization | 1,000,000 | 42.42 | 46.22 | 180.52 | 180.61 |
| Salted SHA-256 | 10,000 | 11.49 | 9.03 | 51.75 | 51.82 |
| Salted SHA-256 | 100,000 | 90.09 | 68.68 | 73.14 | 73.16 |
| Salted SHA-256 | 1,000,000 | 885.21 | 669.76 | 285.61 | 285.88 |
| HMAC-SHA256 | 10,000 | — | 18.66 | — | 51.79 |
| HMAC-SHA256 | 100,000 | — | 163.91 | — | 73.28 |
| HMAC-SHA256 | 1,000,000 | — | 1642.39 | — | 286.00 |
| Conditional fixed mask | 10,000 | 2.19 | 2.13 | 59.80 | 59.82 |
| Conditional fixed mask | 100,000 | 3.40 | 3.43 | 69.92 | 69.98 |
| Conditional fixed mask | 1,000,000 | 20.15 | 14.32 | 164.44 | 164.48 |
| Truncate then mask | 10,000 | 6.92 | 2.79 | 60.27 | 60.33 |
| Truncate then mask | 100,000 | 38.66 | 5.87 | 68.31 | 69.42 |
| Truncate then mask | 1,000,000 | 392.49 | 32.40 | 150.43 | 161.74 |

At one million rows, native padding for a single mask character reduced median
time by about 14× while using 19 MiB more peak memory. Multi-character masks
use a literal-safe regex replacement. The chain comparison measures equivalent
output via two baseline calls versus one current rule list. It includes the
cost of the baseline's intermediate frame and is not a kernel-only comparison.

Copying a preinitialized salted hash state lowered median SHA-256 time by
24% at one million rows and preserved non-null digests. HMAC-SHA256 and SHA-256
still cross into Python per value with `map_elements`. The native Polars hash
is not an equivalent substitute for either cryptographic primitive. Age
generalization and the conditional mask already use native expressions, and
these samples do not justify additional work on either.
