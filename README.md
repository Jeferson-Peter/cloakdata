# CloakData - Data Anonymizer

![PyPI](https://img.shields.io/pypi/v/cloakdata.svg)
![Python](https://img.shields.io/pypi/pyversions/cloakdata.svg)
[![CI](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml/badge.svg)](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml)
![License](https://img.shields.io/github/license/Jeferson-Peter/cloakdata)

A flexible data anonymization library built on [Polars](https://pola.rs/), designed for privacy, compliance, and testing with low overhead.

---

## What's New in 2.0.0

- Improved masking and transformation consistency
- Standardized built-in methods to return `pl.Expr`
- Added `round_date`
- Improved parameter handling and null safety
- Expanded test coverage
- Reorganized built-in methods under `src/cloakdata/native_methods/`

---

## Features

- Masking: full, partial, emails, numbers
- Replacement: static values, exact mapping, contains-based rules
- Sequential IDs: numeric and alphabetical
- Generalization: age, date, number ranges
- Randomization: choices, digits, shuffle, date offsets
- Conditional rules with nested logic
- Custom runtime methods with `register_method(...)`
- Built on Polars for fast vectorized execution

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
    "phone": { "method": "mask_number" },
    "cpf": {
      "method": "replace_with_random_digits",
      "params": { "digits": 11 }
    },
    "status": {
      "method": "replace_exact",
      "params": { "mapping": { "active": "A", "inactive": "I" } }
    },
    "id_seq": { "method": "sequential_numeric", "params": { "prefix": "ID" } },
    "ref_code": { "method": "sequential_alpha", "params": { "prefix": "REF" } },
    "comments": { "method": "truncate", "params": { "length": 5 } },
    "age": { "method": "generalize_age" },
    "birth_date": { "method": "generalize_date", "params": { "mode": "month" } },
    "state": { "method": "random_choice", "params": { "choices": ["SP", "RJ", "MG", "BA"] } },
    "last_access": { "method": "date_offset", "params": { "min_days": -2, "max_days": 2 } },
    "feedback": { "method": "shuffle" }
  }
}
```

---

## Conditional Rules

Single condition:

```json
"cpf": {
  "method": "replace_with_random_digits",
  "params": { "digits": 11 },
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
      "method": "replace_with_random_digits",
      "params": { "digits": 8 },
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

| name | email             | age   | cpf      |
|------|-------------------|-------|----------|
| A.S. | xxxxx@example.com | 20-29 | 48291034 |
| B.J. | xxxxx@example.com | 40-49 | null     |

---

## Examples

Runnable scripts live under [`examples/`](examples).

- Masking: [`examples/masking/full_mask.py`](examples/masking/full_mask.py), [`examples/masking/mask_email.py`](examples/masking/mask_email.py)
- Replacement: [`examples/replace/replace_with_value.py`](examples/replace/replace_with_value.py)
- Generalization: [`examples/generalize/generalize_age.py`](examples/generalize/generalize_age.py)
- Dates: [`examples/random/date_offset.py`](examples/random/date_offset.py)
- Randomization: [`examples/random/random_choice.py`](examples/random/random_choice.py)
- Utilities: [`examples/utils/coalesce.py`](examples/utils/coalesce.py)

---

## Supported Methods

| Method | Description |
|---|---|
| [`full_mask`](examples/masking/full_mask.py) | Fixed mask or literal |
| [`mask_email`](examples/masking/mask_email.py) | Masks the local part of an email |
| [`mask_number`](examples/masking/mask_number.py) | Keeps leading characters and masks the rest |
| [`mask_partial`](examples/masking/mask_partials.py) | Masks the middle while preserving visible edges |
| [`truncate`](examples/masking/truncate.py) | Truncates strings to a fixed length |
| [`initials_only`](examples/initials/initials_only.py) | Converts names to initials |
| [`replace_with_value`](examples/replace/replace_with_value.py) | Replaces all values with a static value |
| [`replace_exact`](examples/replace/replace_exact.py) | Replaces exact values using a mapping |
| [`replace_by_contains`](examples/replace/replace_by_contains.py) | Replaces values that contain substrings |
| [`replace_with_random_digits`](examples/replace/replace_with_random_digits.py) | Generates deterministic digit strings |
| [`sequential_numeric`](examples/sequential/sequential_numeric.py) | Sequential numeric pseudonyms |
| [`sequential_alpha`](examples/sequential/sequential_alpha.py) | Sequential alphabetic pseudonyms |
| [`generalize_age`](examples/generalize/generalize_age.py) | Groups ages into ranges |
| [`generalize_date`](examples/generalize/generalize_date.py) | Reduces date and datetime granularity |
| [`generalize_number_range`](examples/generalize/generalize_number_range.py) | Buckets numeric values into fixed intervals |
| [`random_choice`](examples/random/random_choice.py) | Picks deterministic values from a fixed set |
| [`shuffle`](examples/random/shuffle.py) | Shuffles values while keeping row count |
| [`date_offset`](examples/random/date_offset.py) | Applies deterministic date offsets |
| [`round_number`](examples/round/round_number.py) | Rounds numeric values |
| [`round_date`](examples/round/round_date.py) | Rounds dates to month or year start |
| [`coalesce_cols`](examples/utils/coalesce.py) | Returns the first non-null value across columns |

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
git clone https://github.com/youruser/cloakdata
cd cloakdata
uv sync --extra dev
pre-commit install
pytest -v
```

---

## Roadmap

- Regex-based redaction
- Hashing strategies
- Parallel processing for large datasets

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, how to add a new anonymization method, and the PR checklist.

## Notice

See [NOTICE](NOTICE) for attribution details.

## License

MIT Copyright Jeferson Peter
