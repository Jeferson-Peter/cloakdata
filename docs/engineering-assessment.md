# CloakData engineering assessment

Baseline: GitHub `development` at `1152b4b` (CloakData 3.2.1).

The engine accepts a Polars DataFrame and a column-to-rules mapping. The registry
dispatches to one callable contract, `(df, col, params) -> Expr`. Most native
strategies build expressions. Top-K and sequential labelers inspect values during
construction. Conditions compile to Polars expressions. The public validator and
engine originally followed independent paths.

| Priority | Baseline finding | Reproduction |
| --- | --- | --- |
| P0 | The build succeeds but distributions omit all Python source. | Run `uv build`. The wheel contains only `cloakdata/py.typed` and metadata, and the sdist has no Python modules. Hatch's global include rule selects only the type marker. |
| P1 | A later rule can recover part of a value already replaced by an earlier rule. | With `id=["SECRET", None]`, run `replace_with_value(value="SAFE")` then `truncate(length=3)`. Actual `["SEC", None]`, expected `["SAF", "SAF"]`. |
| P1 | An invalid operator can broaden a transformation or silently disappear from a nested group. | Apply `full_mask` with `{"col":"allow","op":"typo","value":true}` to a row with `allow=false`. It masks the row instead of rejecting the rule. |
| P1 | Invalid protection rules can return original data. | Configure `{"columns":{"id":"full_maks"}}` or `{"columns":{"id":"drop"}}`. Both return the original `id`. Missing unconditional targets are silently skipped. |
| P1 | Regex masks can leave input characters in place. | With `id=["AB\nCD"]`, `full_mask(match_length=True)` returns `["**\n**"]`. A literal mask of `$0` is interpreted as the matched text and exposes the input. The same replacement mechanism is used by other native masks. |
| P2 | Hash null handling disagrees with its configuration. | For `id=[None]`, `hash_value(preserve_nulls=False)` returns null because Polars skips nulls before calling Python. |
| P2 | Standalone validation covers method names but misses invalid rule data. | `validate({"columns":{"id":{"method":"full_mask","params":[]}}})` succeeds. |
| P2 | An unsupported rounding mode returns the original date. | Apply `round_date(mode="typo")` to `"2025-04-03"`. Its fallback is the input string. |
| P2 | A substring replacement can be matched again within the same rule. | Apply `replace_by_contains(mapping={"first":"second","second":"MASK"})` to `"first"`. The second check uses the previous replacement. |

Salted hashes of predictable identifiers can still be checked against candidate
values when the salt is available. Stable outputs can reveal duplicates and
enable joins. Seeded Polars methods are for transformation and reproducibility
within the assumptions of each method. Credit card and CPF masks have explicit
input shape limits, and partial masking intentionally exposes some characters.
None of these mechanisms alone establishes anonymity for a released dataset.
Condition values were interpolated into debug logs and can contain sensitive data.

Baseline verification: 220 tests passed. Branch-enabled coverage was 92% overall
and 71% in the validator. Existing chain tests used constant transformations,
which hid read-after-write defects. Validation, nested malformed rules, and
null hashing lacked regression checks. Ruff reported 26 violations across
tracked source, tests, and examples. CI ran tests and a package build only
when the release workflow detected a version change.

Implementation order: enforce shared validation and correct rule composition,
then apply narrowly scoped privacy fixes and add keyed pseudonyms. Measure time
and process memory before changing performance-sensitive paths. Finish with
regression tests, checks on pushes and pull requests, an installed wheel smoke
test, and user-facing guidance.
See [benchmark methodology and measurements](benchmarks.md) and the
[case study](../CASE_STUDY.md).

The baseline benchmark found the largest measured costs in salted hashing and
length-preserving masking. At one million rows they took 885.21 and 585.13 ms,
respectively. Native string padding addressed masking; reuse of a salted hash
state reduced setup work in the Python callback. The benchmark measures the
increase in memory that accompanied faster masking.

## Implementation and verification

| Change | Compatibility and regression checks |
| --- | --- |
| Sequential engine | A method reads the previous target value. Predicates and references to other columns retain input semantics. Predicates stay outside the staged schema, so custom selectors cannot read them. Tests cover Top-K, custom methods on both sides of a chain, and legacy `is_false` behavior for null flags. |
| Configuration and errors | Shared parsing rejects invalid structures, operators, methods, and parameters. Both entry points reject malformed regex syntax using Polars' own regex engine. Missing unconditional targets, invalid date modes, and invalid drop chains raise. Conditional targets still start as null. Missing method source columns still produce Polars `ColumnNotFoundError`. |
| Privacy | Tests cover literal mask characters, newlines, first-match replacement, keyed output agreement with Python's HMAC, different keys, Unicode, nulls, invalid keys, and empty inputs. Existing non-null hash digests are preserved. The explicit null-encoding option now works. |
| Build and CI | The rebuilt wheel and sdist include the Python modules. CI checks lint, branch-enabled tests, build, and isolated installation of both archives. The release workflow calls those same checks on the release commit and only publishes artifacts uploaded by that run after both Python jobs pass. |

Local verification on Python 3.12.9 and 3.13.3 passed 268 tests on each version,
with 94% combined statement and branch coverage. Ruff and actionlint passed,
and both distributions passed the isolated smoke test on both interpreters.
The validator improved from 71% to 99% coverage. The installed-package smoke
test exercises chain, condition, and HMAC behavior.
