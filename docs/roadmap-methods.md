# Method Roadmap

This document tracks candidate built-in methods for future CloakData releases.

## High Priority

### `hash_value`
- Value: high
- Effort: medium
- Why: stable pseudonymization is a very common privacy requirement
- Notes:
  - support `sha256` by default
  - optionally support `md5` and `sha1`
  - allow `salt`
  - keep deterministic output for joins

### `redact_regex`
- Value: high
- Effort: medium
- Why: text fields often contain embedded sensitive values
- Notes:
  - mask or replace regex matches inside free text
  - useful for email, CPF, phone, token, and card-like patterns
  - should support custom replacement text

### `noise_numeric`
- Value: high
- Effort: medium
- Why: useful for privacy-preserving analytics when exact values are not needed
- Notes:
  - configurable amplitude
  - deterministic with `seed`
  - clarify whether output is additive or percentage-based

## Medium Priority

### `top_k_bucket`
- Value: high
- Effort: medium
- Why: helps anonymize high-cardinality categorical fields
- Notes:
  - keep top K frequent values
  - replace all others with `OTHER`
  - could optionally preserve nulls separately

### `mask_credit_card`
- Value: medium-high
- Effort: low-medium
- Why: common real-world masking use case
- Notes:
  - preserve last 4 digits
  - support configurable mask char

### `generalize_zip_code`
- Value: medium
- Effort: low-medium
- Why: geographic de-identification is common
- Notes:
  - support prefix length
  - useful for CEP and ZIP-like values

### `coarsen_datetime`
- Value: medium
- Effort: medium
- Why: useful when date-only generalization is not enough
- Notes:
  - support time buckets such as 15, 30, or 60 minutes
  - support labels like `morning`, `afternoon`, `night`

## Lower Priority or Niche

### `mask_cpf`
- Value: medium
- Effort: low
- Why: very useful for Brazil-specific datasets
- Notes:
  - may be worth adding if the library keeps strong Brazil-oriented use cases

### `clip_range`
- Value: medium
- Effort: low
- Why: simple numeric sanitization helper
- Notes:
  - clamp values between min and max

### `null_if_matches`
- Value: medium
- Effort: low
- Why: helps normalize dirty placeholder values before anonymization
- Notes:
  - support exact values and regex
  - examples: `N/A`, `unknown`, `00000000000`

### `replace_with_hash_bucket`
- Value: medium
- Effort: medium
- Why: useful when deterministic grouping is enough and unique pseudonyms are not required
- Notes:
  - hash into a fixed number of buckets
  - output labels like `group_01`

### `map_by_reference`
- Value: medium
- Effort: high
- Why: could unlock more advanced replacement flows
- Notes:
  - may depend on auxiliary mapping data
  - likely needs careful API design

## Suggested Order

1. `hash_value`
2. `redact_regex`
3. `noise_numeric`
4. `top_k_bucket`
5. `mask_credit_card`

## Product Notes

- Prefer methods that solve common real-world privacy workflows over methods that only add variety.
- Keep new methods compatible with the current native method flow:
  - function-based implementation
  - registration with `@native_method`
  - coverage in unit and functional tests
