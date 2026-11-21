# CloakData - Data Anonymizer

![PyPI](https://img.shields.io/pypi/v/cloakdata.svg)
![Python](https://img.shields.io/pypi/pyversions/cloakdata.svg)
[![CI](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml/badge.svg)](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml)
![License](https://img.shields.io/github/license/Jeferson-Peter/cloakdata)

A flexible data anonymization library built on [Polars](https://pola.rs/), designed for privacy, compliance, and testing with low overhead.

---

## Current Highlights

- Built-in methods are organized by domain under `src/cloakdata/native_methods/`
- Native methods are registered automatically with `@native_method`
- Practical support for masking, replacement, generalization, randomization, and data cleanup
- Config-driven anonymization with conditional rules
- Runnable examples for the main built-in methods
- Built on Polars for fast vectorized execution

---

## Features

- Masking:
  - `full_mask`
  - `mask_email`
  - `mask_number`
  - `mask_credit_card`
  - `mask_cpf`
  - `mask_partial`
- Replacement and pseudonymization:
  - `replace_with_value`
  - `replace_exact`
  - `replace_by_contains`
  - `replace_with_random_digits`
  - `hash_value`
  - `hmac_value`
  - `replace_with_hash_bucket`
  - `redact_regex`
- Generalization:
  - `generalize_age`
  - `generalize_date`
  - `generalize_number_range`
  - `generalize_zip_code`
  - `top_k_bucket`
  - `coarsen_datetime`
- Randomization and transforms:
  - `random_choice`
  - `shuffle`
  - `noise_numeric`
  - `date_offset`
  - `round_number`
  - `round_date`
  - `clip_range`
- Utilities:
  - `coalesce_cols`
  - `null_if_matches`
- Sequential pseudonyms:
  - `sequential_numeric`
  - `sequential_alpha`
- Conditional rules with nested logic
- Custom runtime methods with `register_method(...)`

---

## How It Works

1. Load data into a Polars `DataFrame`
2. Define rules in a config dictionary
3. Call `anonymize(df, config)`
4. Receive a transformed `DataFrame`

The engine validates the configuration and gets a snapshot of the method registry.
Built-in and custom methods return Polars expressions. Independent columns are
evaluated against the input, and each chain uses a lazy projection per rule.
Custom methods keep the `(df, col, params) -> pl.Expr` signature. When a custom
method runs inside a chain, its input includes the current target column and the
original values for other available columns.

---

## Quickstart

```python
import polars as pl

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "name": ["Alice Smith", "Bob Jones"],
        "email": ["alice@example.com", "bob@example.com"],
        "age": [25, 42],
    }
)

config = {
    "columns": {
        "name": {"method": "initials_only"},
        "email": {"method": "mask_email"},
        "age": {"method": "generalize_age"},
    }
}

out = anonymize(df, config)
print(out)
```

---

## Example Config

Apply this configuration to a DataFrame containing all the listed columns.
Each target refers to an existing column unless it has a conditional rule.

```json
{
  "columns": {
    "name": { "method": "initials_only" },
    "email": { "method": "mask_email" },
    "email_hash": {
      "method": "hash_value",
      "params": { "salt": "public-example-salt" }
    },
    "phone": { "method": "mask_number", "params": { "keep": 3 } },
    "cpf": {
      "method": "mask_cpf",
      "params": { "keep_last": 2 }
    },
    "status": {
      "method": "replace_exact",
      "params": { "mapping": { "active": "A", "inactive": "I" } }
    },
    "notes": {
      "method": "redact_regex",
      "params": {
        "pattern": "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}",
        "replacement": "[EMAIL]"
      }
    },
    "id_seq": { "method": "sequential_numeric", "params": { "prefix": "ID" } },
    "ref_code": { "method": "sequential_alpha", "params": { "prefix": "REF" } },
    "comments": { "method": "truncate", "params": { "length": 5 } },
    "age": { "method": "generalize_age" },
    "birth_date": { "method": "generalize_date", "params": { "mode": "month" } },
    "zip_code": { "method": "generalize_zip_code", "params": { "visible_prefix": 3 } },
    "state": { "method": "random_choice", "params": { "choices": ["SP", "RJ", "MG", "BA"] } },
    "last_access": { "method": "date_offset", "params": { "min_days": -2, "max_days": 2 } },
    "event_time": { "method": "coarsen_datetime", "params": { "mode": "part_of_day" } },
    "feedback": { "method": "shuffle" },
    "score": { "method": "clip_range", "params": { "min": 0, "max": 100 } }
  }
}
```

---

## Conditional Rules

Single condition:

```json
"cpf": {
  "method": "mask_cpf",
  "params": { "keep_last": 2 },
  "condition": {
    "column": "status",
    "operator": "equals",
    "value": "active"
  }
}
```

Multiple rules per column run in list order. Each method reads the previous
result for its target. Conditions use the original values for every column,
including the target. A false or null predicate keeps the previous result.

```json
"email": [
  { "method": "mask_email" },
  {
    "method": "truncate",
    "params": { "length": 5 },
    "condition": { "column": "share_domain", "operator": "is_false" }
  }
]
```

Nested conditions:

```json
"age": {
  "method": "generalize_age",
  "condition": {
    "all": [
      { "column": "country", "operator": "equals", "value": "BR" },
      {
        "any": [
          { "column": "status", "operator": "equals", "value": "active" },
          { "column": "status", "operator": "equals", "value": "archived" }
        ]
      }
    ]
  }
}
```

Supported operators:
`equals`, `not_equals`, `in`, `not_in`, `gt`, `gte`, `lt`, `lte`, `between`,
`contains`, `not_contains`, `startswith`, `endswith`, `is_null`, `not_null`,
`is_true`, and `is_false`. The `contains` operators use regex patterns.
For compatibility, `is_false` also matches null input flags. This preserves
policies that redact when a flag is missing.

Supported groups include `all`, `any`, `not`, non-empty lists (implicit AND),
and `{"conditions": [...], "logical": "and" | "or"}`.

---

## Example Input to Output

Input:

| name        | email             | age | status   | cpf         |
|-------------|-------------------|-----|----------|-------------|
| Alice Smith | alice@example.com | 25  | active   | 00000000001 |
| Bob Jones   | bob@example.com   | 42  | inactive | null        |

Config:

```json
{
  "columns": {
    "name": { "method": "initials_only" },
    "email": { "method": "mask_email" },
    "age": { "method": "generalize_age" },
    "cpf": {
      "method": "mask_cpf",
      "params": { "keep_last": 2 },
      "condition": {
        "column": "status",
        "operator": "equals",
        "value": "active"
      }
    }
  }
}
```

Output:

| name | email             | age   | status   | cpf           |
|------|-------------------|-------|----------|---------------|
| A.S. | xxxxx@example.com | 20-29 | active   | `*********01` |
| B.J. | xxxxx@example.com | 40-49 | inactive | null          |

---

## Examples

Runnable scripts live under [`examples/`](examples).

- Masking: [`examples/masking/full_mask.py`](examples/masking/full_mask.py), [`examples/masking/mask_email.py`](examples/masking/mask_email.py), [`examples/masking/mask_number.py`](examples/masking/mask_number.py), [`examples/masking/mask_partials.py`](examples/masking/mask_partials.py), [`examples/masking/mask_credit_card.py`](examples/masking/mask_credit_card.py), [`examples/masking/mask_cpf.py`](examples/masking/mask_cpf.py), [`examples/masking/truncate.py`](examples/masking/truncate.py)
- Replacement: [`examples/replace/replace_with_value.py`](examples/replace/replace_with_value.py), [`examples/replace/replace_exact.py`](examples/replace/replace_exact.py), [`examples/replace/replace_by_contains.py`](examples/replace/replace_by_contains.py), [`examples/replace/replace_with_random_digits.py`](examples/replace/replace_with_random_digits.py), [`examples/replace/hash_value.py`](examples/replace/hash_value.py), [`examples/replace/redact_regex.py`](examples/replace/redact_regex.py), [`examples/replace/replace_with_hash_bucket.py`](examples/replace/replace_with_hash_bucket.py)
- Generalization: [`examples/generalize/generalize_age.py`](examples/generalize/generalize_age.py), [`examples/generalize/generalize_date.py`](examples/generalize/generalize_date.py), [`examples/generalize/generalize_number_range.py`](examples/generalize/generalize_number_range.py), [`examples/generalize/generalize_zip_code.py`](examples/generalize/generalize_zip_code.py), [`examples/generalize/top_k_bucket.py`](examples/generalize/top_k_bucket.py), [`examples/generalize/coarsen_datetime.py`](examples/generalize/coarsen_datetime.py)
- Randomization: [`examples/random/random_choice.py`](examples/random/random_choice.py), [`examples/random/noise_numeric.py`](examples/random/noise_numeric.py), [`examples/random/shuffle.py`](examples/random/shuffle.py), [`examples/random/date_offset.py`](examples/random/date_offset.py)
- Numeric transforms: [`examples/round/round_number.py`](examples/round/round_number.py), [`examples/round/round_date.py`](examples/round/round_date.py), [`examples/round/clip_range.py`](examples/round/clip_range.py)
- Sequential: [`examples/sequential/sequential_numeric.py`](examples/sequential/sequential_numeric.py), [`examples/sequential/sequential_alpha.py`](examples/sequential/sequential_alpha.py)
- Utilities: [`examples/utils/coalesce.py`](examples/utils/coalesce.py), [`examples/utils/null_if_matches.py`](examples/utils/null_if_matches.py)

---

## Supported Methods

| Method | Description |
|---|---|
| [`full_mask`](examples/masking/full_mask.py) | Fixed mask or literal |
| [`mask_email`](examples/masking/mask_email.py) | Masks the local part of an email |
| [`mask_number`](examples/masking/mask_number.py) | Keeps leading characters and masks the rest |
| [`mask_credit_card`](examples/masking/mask_credit_card.py) | Masks card digits while preserving the last visible digits |
| [`mask_cpf`](examples/masking/mask_cpf.py) | Masks Brazilian CPF values while preserving the final visible digits |
| [`mask_partial`](examples/masking/mask_partials.py) | Masks the middle while preserving visible edges |
| [`truncate`](examples/masking/truncate.py) | Truncates strings to a fixed length |
| [`initials_only`](examples/initials/initials_only.py) | Converts names to initials |
| [`replace_with_value`](examples/replace/replace_with_value.py) | Replaces all values with a static value |
| [`hash_value`](examples/replace/hash_value.py) | Generates deterministic hashes, with optional salt |
| [`hmac_value`](#keyed-pseudonyms) | Creates deterministic HMAC-SHA256 pseudonyms using secret key bytes |
| [`redact_regex`](examples/replace/redact_regex.py) | Redacts regex matches inside free text |
| [`replace_with_hash_bucket`](examples/replace/replace_with_hash_bucket.py) | Replaces values with deterministic hash buckets |
| [`replace_exact`](examples/replace/replace_exact.py) | Replaces exact values using a mapping |
| [`replace_by_contains`](examples/replace/replace_by_contains.py) | Replaces values that contain substrings |
| [`replace_with_random_digits`](examples/replace/replace_with_random_digits.py) | Generates deterministic digit strings |
| [`sequential_numeric`](examples/sequential/sequential_numeric.py) | Sequential numeric pseudonyms |
| [`sequential_alpha`](examples/sequential/sequential_alpha.py) | Sequential alphabetic pseudonyms |
| [`generalize_age`](examples/generalize/generalize_age.py) | Groups ages into ranges |
| [`generalize_date`](examples/generalize/generalize_date.py) | Reduces date and datetime granularity |
| [`generalize_number_range`](examples/generalize/generalize_number_range.py) | Buckets numeric values into fixed intervals |
| [`generalize_zip_code`](examples/generalize/generalize_zip_code.py) | Preserves a visible postal-code prefix and masks the rest |
| [`coarsen_datetime`](examples/generalize/coarsen_datetime.py) | Coarsens timestamps into buckets, minute-of-day buckets (time-only or full datetime), hour, part-of-day, weekday, weekend/weekday, or configurable business-hours labels |
| [`top_k_bucket`](examples/generalize/top_k_bucket.py) | Keeps the top-k most frequent categories and buckets the rest |
| [`random_choice`](examples/random/random_choice.py) | Picks deterministic values from a fixed set |
| [`noise_numeric`](examples/random/noise_numeric.py) | Adds deterministic numeric noise within configured bounds |
| [`shuffle`](examples/random/shuffle.py) | Shuffles values while keeping row count |
| [`date_offset`](examples/random/date_offset.py) | Applies deterministic date offsets |
| [`clip_range`](examples/round/clip_range.py) | Constrains numeric values to configured min/max bounds |
| [`round_number`](examples/round/round_number.py) | Rounds numeric values |
| [`round_date`](examples/round/round_date.py) | Rounds dates to month or year start |
| [`coalesce_cols`](examples/utils/coalesce.py) | Returns the first non-null value across columns |
| [`null_if_matches`](examples/utils/null_if_matches.py) | Converts known placeholders or regex matches into null |

---

## Privacy and threat model

- **Masking** hides selected characters or values. Partial masks expose some
  characters, and length-preserving masks reveal length. CPF and card masks
  recognize specific formats and may leave unrecognized inputs unchanged.
- **Hashing** creates a deterministic digest. `hash_value` preserves its
  legacy digest for non-null values. With `preserve_nulls=False`, null hashes
  like the empty string. An observer who knows the salt can test guesses
  for predictable emails, phone numbers, and identifiers.
- **Keyed pseudonymization** reduces offline guessing when the recipient
  lacks the secret and cannot query a service that produces tokens for chosen
  inputs. Identical strings under the same key produce identical tokens, which
  expose equality and frequency. Other columns can still identify people.
- **Anonymization** is a property of the released dataset in context. Review
  auxiliary data, rare combinations, access controls, and residual linkage.
  Using these methods alone does not establish compliance with
  [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) or
  [LGPD](https://planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm).

Seeded random choices, numeric noise, and date offsets can depend on row
position. Hash buckets can collide. Polars does not guarantee
[`Expr.hash` stability across versions](https://docs.pola.rs/api/python/version/1/reference/expressions/api/polars.Expr.hash.html).
Sequential labels are local to the input, and shuffle keeps the original set
of values. These methods offer no cryptographic protection.

### Keyed pseudonyms

`hmac_value` casts inputs to Polars strings, hashes their UTF-8 bytes using
HMAC-SHA256, and leaves nulls unchanged. Supply at least 32 random bytes from a
secret store. Use separate keys for datasets that should not be linkable. Keep
keys, configs containing keys, and source records out of logs and version control.

```python
import os

from cloakdata import anonymize
from cloakdata.validate import validate

key = bytes.fromhex(os.environ["CLOAKDATA_HMAC_KEY_HEX"])
config = {"columns": {"email": {"method": "hmac_value", "params": {"key": key}}}}
validate(config)
out = anonymize(df, config)
```

Generate the key once with a cryptographic generator such as
`secrets.token_bytes(32)` and store its hex encoding securely. Rotating the key
changes all tokens. Normalize input explicitly if equivalent identifiers should
produce the same token.

## Validation and troubleshooting

- `validate(config)` raises `ValueError` for invalid rule structure, conditions,
  and native parameters that can be checked without the data. This includes
  malformed regex patterns in conditions and native methods. Use
  [Polars regex syntax](https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.str.contains.html).
  Validation does not run custom methods or check the input schema.
- `anonymize(df, config)` also checks target and predicate columns. Unknown
  methods, malformed conditions, empty rule lists, and missing unconditional
  targets now fail. A missing conditional target still starts as null.
- Use `"drop"` or `{"method": "drop"}` as the sole rule for a column. It is safe
  to drop an absent column. Dropped columns cannot be used by other rules.
- `anonymize` raises `ValueError` or `TypeError` for invalid settings. For a valid config that fails on the
  data, catch `cloakdata.TransformationError` and inspect its chained cause
  privately. Polars exceptions can include input values. Missing columns used
  inside method expressions still raise Polars `ColumnNotFoundError`.
- Polars calculates both sides of conditional expressions. A transformation
  must accept the column data types even where its predicate is false.

---

## Project Structure

```text
src/
  cloakdata/
    native_methods/  # Built-in methods organized by domain
tests/               # Pytest suite
examples/            # Runnable examples
README.md
pyproject.toml
```

Built-in methods live under `src/cloakdata/native_methods/` and are registered automatically with `@native_method`.

---

## Installation

```bash
pip install cloakdata
```

Or with `uv`:

```bash
uv add cloakdata
```

---

## Development

```bash
git clone https://github.com/Jeferson-Peter/cloakdata
cd cloakdata
uv sync --locked --extra dev
uv run ruff check .
uv run coverage run -m pytest
uv run coverage report
uv build
```

---

## Choosing Methods

- Use `hmac_value` for stable pseudonyms of predictable identifiers when you can protect a key.
- Use `hash_value` when you need to reproduce existing unkeyed digests.
- Use `replace_with_hash_bucket` when you need deterministic grouping and collisions are acceptable.
- Use `generalize_date` when you want period-style date abstraction such as month, quarter, or year.
- Use `round_date` when you want canonical rounded dates such as month-start or year-start.
- Use `coarsen_datetime` when you want timestamp abstraction such as hour buckets, part-of-day labels, weekdays, or business-hours labels.
- Use `null_if_matches` before anonymization when your source data contains placeholders such as `N/A`, `unknown`, or regex-shaped junk values.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, how to add a new anonymization method, and the PR checklist.

See the [engineering assessment](docs/engineering-assessment.md),
[benchmarks](docs/benchmarks.md), and [portfolio case study](CASE_STUDY.md)
for the design decisions and measurements.
See the [unreleased notes](release-notes/UNRELEASED.md) for compatibility changes.

## Notice

See [NOTICE](NOTICE) for attribution details.

## License

MIT Copyright Jeferson Peter
