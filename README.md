# 🔐 CloakData — Data Anonymizer

![PyPI](https://img.shields.io/pypi/v/cloakdata.svg)
![Python](https://img.shields.io/pypi/pyversions/cloakdata.svg)
[![CI](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml/badge.svg)](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml)
![License](https://img.shields.io/github/license/Jeferson-Peter/cloakdata)

> A flexible and extensible **data anonymization library** built on [Polars](https://pola.rs/).
> Designed for **privacy, compliance, and testing** with minimal overhead.

---

## 🧾 What’s New (1.1.1)

- ✅ Added configurable params for `full_mask`: `char`, `len`, `mask_literal`, `match_length`, `preserve_nulls`.
- ✅ Added configurable params for `mask_email`: `mask`, `fallback_domain`, `preserve_nulls`.
- ✅ Moved detailed method examples into [examples/](examples).

---

## ✨ Features

- 🔒 **Masking**: full, partial, emails, phone numbers.
- 🔄 **Replacement**: static values, dictionaries, substrings.
- 🔢 **Sequential IDs**: numeric or alphabetical.
- ✂️ **Truncation & initials extraction**.
- 📊 **Generalization**: ages into ranges, dates into month/year.
- 🎲 **Randomization**: choices, digits, shuffling.
- 📅 **Date offsetting** with reproducible seeds.
- 🧩 **Conditional rules** — multi-rules, nested (`all`/`any`/`not`), logical groups (`and`/`or`).
- ⚡ Built on **Polars** → fast & scalable.

---

## ⚙️ How it works

1. Load your dataset into a Polars `DataFrame`.
2. Define anonymization rules in a simple JSON config.
3. Call `anonymize(df, config)` → get a safe anonymized DataFrame.

---

## 🧪 Example Config

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
    "birth_date": { "method": "generalize_date", "params": { "mode": "month_year" } },
    "state": { "method": "random_choice", "params": { "choices": ["SP","RJ","MG","BA"] } },
    "last_access": { "method": "date_offset", "params": { "min_days": -2, "max_days": 2 } },
    "feedback": { "method": "shuffle" }
  }
}
```

---

## 🧠 Conditional Rules

Apply transformations only when conditions are met.

### Single condition

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

### Multiple rules per column

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

### Nested conditions

```json
"age": {
  "method": "generalize_age",
  "condition": {
    "all": [
      { "column": "country", "operator": "equals", "value": "BR" },
      { "any": [
          { "column": "status", "operator": "equals", "value": "active" },
          { "column": "status", "operator": "equals", "value": "archived" }
        ]
      }
    ]
  }
}
```

**Operators supported**:
`equals`, `not_equals`, `in`, `not_in`, `gt`, `gte`, `lt`, `lte`, `contains`, `not_contains`
**Groups**: `all`, `any`, `not`
**Logical**: `and`, `or`

---

## 🔍 Example Input → Output

**Input DataFrame:**

| name         | email              | age | status   |
|--------------|--------------------|-----|----------|
| Alice Smith  | alice@example.com  | 25  | active   |
| Bob Jones    | bob@example.com    | 42  | inactive |

**Config:**

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

**Output DataFrame:**

| name | email             | age   | cpf       |
|------|-------------------|-------|-----------|
| A.S. | xxxxx@example.com | 20-29 | 48291034  |
| B.J. | xxxxx@example.com | 40-49 | (null)    |

---

## 🧩 Examples

Runnable, self-contained scripts are in the [examples/](examples) folder.

- Masking: [masking/full_mask.py](examples/masking/full_mask.py), [masking/mask_email.py](examples/masking/mask_email.py)
- Replacement: [replacement/replace_with_value.py](examples/replacement/replace_with_value.py)
- Generalization: [generalization/generalize_age.py](examples/generalization/generalize_age.py)
- Dates: [dates/date_offset.py](examples/dates/date_offset.py)
- Randomization: [randomization/random_choice.py](examples/randomization/random_choice.py)
- Utilities: [utilities/coalesce_cols.py](examples/utilities/coalesce_cols.py)

---

## 📊 Supported Methods
| Method                                                            | Description                                                                                                                                                                                | Example Input → Output                                                                                                                                                                |
|-------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`full_mask`](examples/masking/full_mask.py)                      | Fixed mask or literal; supports `char`, `len`, `mask_literal`, `match_length`, `preserve_nulls`.                                                                                           | `12345` → `*****` / `XXXXXXXX` / `REDACTED`                                                                                                                                           |
| [`mask_email`](examples/masking/mask_email.py)                    | Masks local part; supports `mask`, `fallback_domain`, `preserve_nulls`.                                                                                                                    | `john@example.com` → `xxxxx@example.com`                                                                                                                                              |
| [`mask_number`](examples/masking/mask_number.py)                  | Keep first N digits, then mask the rest (configurable `keep`, `mask`, `len`, `preserve_nulls`)                                                                                             | `123456789` → `123*****` <br> `98765` + `keep=2, mask="X"` → `98XXX` <br> `42` + `keep=2, len=4, mask="#"` → `42####`                                                                 |
| `mask_partial`                                                    | Show start & end, mask the middle                                                                                                                                                          | `abcdef` → `a****f`                                                                                                                                                                   |
| [`replace_with_value`](examples/replace/replace_with_value.py)    | Replace entire column with a static **value** (dtype preserved). Optionally keep nulls with `preserve_nulls=True`. **Requires** `value`.                                                   | `["a", None, "b"]` + `value="X"` → `"X","X","X"` • `preserve_nulls=True` → `"X", None, "X"` • `value=123` → `123,123,123`                                                             |
| [`replace_exact`](examples/replace/replace_exact.py)              | Replace values that exactly match keys in a mapping. Values not in the mapping are unchanged. Dtype is inferred from replacements (no forced Utf8).                                        | `["a","b","c"]` + `{"a":"X"}` → `["X","b","c"]` • `[1,2,3]` + `{1:99,3:-1}` → `[99,2,-1]` • `[True,False]` + `{True:False}` → `[False,False]`                                         |
| [`replace_by_contains`](examples/replace/replace_by_contains.py)  | Replace values when they **contain** given substrings. Literal by default; first match wins; nulls preserved. Options: `mapping`, `substr`+`replacement`, `case_sensitive`, `use_regex`.   | `["foo","bar","baz"]` + `{"ba":"X"}` → `["foo","X","X"]` • `case_sensitive=False`: `"Hello"` + `{"hello":"X"}` → `"X"` • `use_regex=True`: `{"\\d{3}":"HIT"}` on `"id=123"` → `"HIT"` |
| `replace_with_random_digits`                                      | Replace with random digits of fixed length                                                                                                                                                 | `11111` → `80239`                                                                                                                                                                     |
| [`sequential_numeric`](examples/sequential/sequential_numeric.py) | Sequential numeric pseudonyms with optional prefix (`prefix=None` → raw integers, default `"val"`)                                                                                         | `["Alice","Bob","Alice"]` → `["val 1","val 2","val 1"]`                                                                                                                               |
| [`sequential_alpha`](examples/sequential/sequential_alpha.py)     | Sequential alphabetic pseudonyms with optional prefix; duplicates get the same label; order by first appearance                                                                            | `["Alice","Bob","Alice"]` → `["val A","val B","val A"]`                                                                                                                               |
| [`truncate` ](examples/masking/truncate.py)                       | Truncates strings to a maximum length (nulls preserved unless configured)                                                                                                                  | `"Porto Alegre"` → `"Port"`                                                                                                                                                           |
| [`initials_only`](examples/initials/initials_only.py)             | Convert names to initials                                                                                                                                                                  | `John Doe` → `J.D.`                                                                                                                                                                   |
| [`generalize_age`](examples/generalize/generalize_age.py)         | Group ages into ranges                                                                                                                                                                     | `25` → `20-29`                                                                                                                                                                        |
| [`generalize_date`](examples/generalize/generalize_date.py)       | Generalize dates/datetimes by reducing granularity (`year`, `month`, `quarter`, `semester`, `week`, `date`, `datetime`)                                                                    | `2025-07-20` → `2025-07` ; `2025-07-20` → `2025-Q3`                                                                                                                                   |
| `generalize_number_range`                                         | Bucketize numbers by interval                                                                                                                                                              | `23` → `20-29`                                                                                                                                                                        |
| [`random_choice`](examples/random/random_choice.py)               | Replace values with a deterministic pseudo-random choice from a fixed set (null-safe) | `São Paulo` → `X` / `Y` (with seed) |
| `shuffle`                                                         | Shuffle column values                                                                                                                                                                      | `[A,B,C]` → `[B,C,A]`                                                                                                                                                                 |
| `date_offset`                                                     | Apply random offset within day range                                                                                                                                                       | `2025-07-20` → `2025-07-18`                                                                                                                                                           |
| `coalesce_cols`                                                   | Take first non-null from multiple columns                                                                                                                                                  | `(None, Y)` → `Y`                                                                                                                                                                     |
| `round_number`                                                    | Round numeric values to fixed decimals                                                                                                                                                     | `3.14159` → `3.14`                                                                                                                                                                    |
| `round_date`                                                      | Round date down to month or year start                                                                                                                                                     | `2025-07-29` → `2025-07-01`                                                                                                                                                           |

---

## 📂 Project Structure

```
src/
 └── cloakdata/           # Core library
tests/                    # Test suite (pytest + Polars)
examples/                 # Sample CSVs & configs
README.md                 # Project docs
pyproject.toml            # Build system (uv/hatch)
```

---

## ⚡ Installation

```bash
pip install cloakdata
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add cloakdata
```

---

## 🚀 Quickstart

```python
import polars as pl
from cloakdata import anonymize

df = pl.DataFrame({
    "name": ["Alice Smith", "Bob Jones"],
    "email": ["alice@example.com", "bob@example.com"],
    "age": [25, 42]
})

config = {
    "columns": {
        "name": { "method": "initials_only" },
        "email": { "method": "mask_email" },
        "age": { "method": "generalize_age" }
    }
}

out = anonymize(df, config)
print(out)
```

---

## 🛠️ Development

```bash
git clone https://github.com/youruser/cloakdata
cd cloakdata
uv sync
pre-commit install
pytest -v
```

---

## 🔮 Roadmap

- [ ] Regex-based redaction
- [ ] Hashing strategies (SHA256, bcrypt)
- [ ] Parallel processing for large datasets

---

## 🤝 Contributing

We love contributions! See **[CONTRIBUTING.md](https://github.com/Jeferson-Peter/cloakdata/blob/development/CONTRIBUTING.md)** for setup, coding standards, how to add a new anonymization method, tests and the PR checklist.

## 📄 Notice

See **[NOTICE](https://github.com/Jeferson-Peter/cloakdata/blob/development/NOTICE)** for attribution details.

## 📜 License

MIT © Jeferson Peter
