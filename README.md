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

```json
{
  "columns": {
    "name": { "method": "initials_only" },
    "email": { "method": "mask_email" },
    "email_hash": {
      "method": "hash_value",
      "params": { "salt": "team-2026" }
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

Multiple rules per column:

```json
"city": [
  { "method": "replace_with_value", "params": { "value": "X" } },
  {
    "method": "mask_partial",
    "params": { "visible_start": 1, "visible_end": 1 },
    "condition": { "column": "country", "operator": "equals", "value": "BR" }
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
`equals`, `not_equals`, `in`, `not_in`, `gt`, `gte`, `lt`, `lte`, `contains`, `not_contains`

Supported groups:
`all`, `any`, `not`

---

## Example Input to Output

Input:

| name        | email             | age | status   |
|-------------|-------------------|-----|----------|
| Alice Smith | alice@example.com | 25  | active   |
| Bob Jones   | bob@example.com   | 42  | inactive |

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

| name | email             | age   | cpf          |
|------|-------------------|-------|--------------|
| A.S. | xxxxx@example.com | 20-29 | *********01  |
| B.J. | xxxxx@example.com | 40-49 | null         |

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

## Notes

- `hash_value` is deterministic and better when you need stable one-way pseudonymization.
- `replace_with_hash_bucket` is deterministic bucketing, not unique pseudonymization. Different input values can land in the same bucket when the number of unique values is greater than the configured number of buckets.

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
uv sync --extra dev
pre-commit install
pytest -v
```

---

## Choosing Methods

- Use `hash_value` when you need stable one-way pseudonymization.
- Use `replace_with_hash_bucket` when you need deterministic grouping and collisions are acceptable.
- Use `generalize_date` when you want period-style date abstraction such as month, quarter, or year.
- Use `round_date` when you want canonical rounded dates such as month-start or year-start.
- Use `coarsen_datetime` when you want timestamp abstraction such as hour buckets, part-of-day labels, weekdays, or business-hours labels.
- Use `null_if_matches` before anonymization when your source data contains placeholders such as `N/A`, `unknown`, or regex-shaped junk values.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, how to add a new anonymization method, and the PR checklist.

## Notice

See [NOTICE](NOTICE) for attribution details.

## License

MIT Copyright Jeferson Peter
