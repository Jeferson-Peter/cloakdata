# Unreleased

- Rules on the same target now compose in list order. Conditions still use
  original values, including the target. The legacy behavior where
  `is_false` matches null flags is preserved.
- Validation rejects unknown methods, malformed rules and regexes, and missing
  unconditional targets. A missing conditional target still starts as null.
  Custom methods keep the `(df, col, params) -> pl.Expr` signature.
- Use either `"drop"` or `{"method": "drop"}` as the only rule for a column.
  Invalid date rounding modes now raise an error.
- `replace_by_contains` selects the first matching entry against the input
  for that rule. It no longer applies a second mapping to the replacement.
- `hash_value` preserves existing non-null digests. With
  `preserve_nulls=False`, null now receives the digest for the empty string.
  `hmac_value` provides keyed SHA-256 pseudonyms. See the
  [privacy guidance](../README.md#privacy-and-threat-model) for key handling and limitations.
- Fixed wheel and sdist file selection. CI tests both installed distributions
  and gates publication on successful checks for the exact release commit.
