# 🔐 CloakData — Data Anonymizer

![PyPI](https://img.shields.io/pypi/v/cloakdata.svg)
![Python](https://img.shields.io/pypi/pyversions/cloakdata.svg)
[![CI](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml/badge.svg)](https://github.com/Jeferson-Peter/cloakdata/actions/workflows/publish.yml)
![License](https://img.shields.io/github/license/Jeferson-Peter/cloakdata)

> A flexible and extensible **data anonymization library** built on [Polars](https://pola.rs/).
> Designed for **privacy, compliance, and testing** with minimal overhead.

---

## ✨ Features

- 🔒 **Masking**: full, partial, emails, phone numbers.
- 🔄 **Replacement**: static values, dictionaries, substrings.
- 🔢 **Sequential IDs**: numeric or alphabetical.
- ✂️ **Truncation & initials extraction**.
- 📊 **Generalization**: ages into ranges, dates into month/year.
- 🎲 **Randomization**: choices, digits, shuffling.
- 📅 **Date offsetting** with reproducible seeds.
- 🧩 **Conditional rules** based on other columns.
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

Apply transformations only when conditions are met:

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

### Supported operators

| Operator      | Description                          |
|---------------|--------------------------------------|
| equals        | Equal to                             |
| not_equals    | Not equal to                         |
| in            | Value in list                        |
| not_in        | Value not in list                    |
| gt / gte      | Greater than / greater or equal      |
| lt / lte      | Less than / less or equal            |
| contains      | Substring exists in string           |
| not_contains  | Substring does not exist in string   |

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

## 🧩 Examples by Method

Below are minimal examples of how each anonymization method works.

All examples assume:

```python
import polars as pl
from cloakdata import anonymize
```

---

### 🔒 Masking

**Full mask**

```python
df = pl.DataFrame({"ssn": ["123-45-6789", "987-65-4321"]})
config = {"columns": {"ssn": {"method": "full_mask"}}}
print(anonymize(df, config))
```

**Mask email**

```python
df = pl.DataFrame({"email": ["john@example.com", "invalid"]})
config = {"columns": {"email": {"method": "mask_email"}}}
print(anonymize(df, config))
```

**Mask number**

```python
df = pl.DataFrame({"phone": ["123456789", "987654321"]})
config = {"columns": {"phone": {"method": "mask_number"}}}
print(anonymize(df, config))
```

**Mask partial**

```python
df = pl.DataFrame({"code": ["abcdef", "12345"]})
config = {"columns": {"code": {"method": "mask_partial", "params": {"visible_start": 2, "visible_end": 2}}}}
print(anonymize(df, config))
```

---

### 🔄 Replacement

**Static value**

```python
df = pl.DataFrame({"city": ["NY", "LA"]})
config = {"columns": {"city": {"method": "replace_with_value", "params": {"value": "Unknown"}}}}
print(anonymize(df, config))
```

**Exact mapping**

```python
df = pl.DataFrame({"status": ["active", "inactive"]})
config = {"columns": {"status": {"method": "replace_exact", "params": {"mapping": {"active": "A", "inactive": "I"}}}}}
print(anonymize(df, config))
```

**Substring mapping**

```python
df = pl.DataFrame({"text": ["error: 404", "ok"]})
config = {"columns": {"text": {"method": "replace_by_contains", "params": {"mapping": {"error": "ERR"}}}}}
print(anonymize(df, config))
```

---

### 🔢 Sequential IDs

```python
df = pl.DataFrame({"user": ["Alice", "Bob", "Charlie"]})
config = {"columns": {
    "user": {"method": "sequential_numeric", "params": {"prefix": "U"}}
}}
print(anonymize(df, config))
```

---

### ✂️ Truncation & Initials

```python
df = pl.DataFrame({"name": ["Alice Smith", "Bob Jones"]})
config = {"columns": {
    "short": {"method": "truncate", "params": {"length": 3}},
    "initials": {"method": "initials_only"}
}}
print(anonymize(df, config))
```

---

### 📊 Generalization

```python
df = pl.DataFrame({"age": [25, 42], "date": ["2025-07-20", "2025-01-15"], "salary": [2300, 12500]})
config = {"columns": {
    "age": {"method": "generalize_age"},
    "date": {"method": "generalize_date", "params": {"mode": "year"}},
    "salary": {"method": "generalize_number_range", "params": {"interval": 5000}}
}}
print(anonymize(df, config))
```

---

### 🎲 Randomization

```python
df = pl.DataFrame({
    "state": ["SP", "RJ", "MG"],
    "cpf": ["11111", "22222", "33333"],
    "col": ["A", "B", "C"]
})

config = {"columns": {
    "state": {"method": "random_choice", "params": {"choices": ["AA", "BB"], "seed": 42}},
    "cpf": {"method": "replace_with_random_digits", "params": {"digits": 5}},
    "col": {"method": "shuffle", "params": {"seed": 42}}
}}

print(anonymize(df, config))
```

---

### 📅 Dates

```python
df = pl.DataFrame({"d": ["2025-07-29", "2025-07-30"]})
config = {"columns": {
    "offset": {"method": "date_offset", "params": {"min_days": -2, "max_days": 2, "seed": 42}},
    "rounded": {"method": "round_date", "params": {"mode": "month"}}
}}
print(anonymize(df, config))
```

---

### 🧩 Utilities

```python
df = pl.DataFrame({"a": [None, "X"], "b": ["Y", None], "n": [3.14159, 2.71828]})
config = {"columns": {
    "coalesced": {"method": "coalesce_cols", "params": {"columns": ["a", "b"]}},
    "rounded": {"method": "round_number", "params": {"digits": 2}}
}}
print(anonymize(df, config))
```

---

## 📊 Supported Methods

| Method                   | Description                                      | Example Input → Output                  |
|--------------------------|--------------------------------------------------|-----------------------------------------|
| `full_mask`              | Replace all values with `*****`                  | `12345` → `*****`                       |
| `mask_email`             | Hide local part of email, keep domain            | `john@example.com` → `xxxxx@example.com`|
| `mask_number`            | Keep first 3 chars, mask rest                   | `123456789` → `123*****`                |
| `mask_partial`           | Show start & end, mask middle                   | `abcdef` → `ab**ef`                     |
| `replace_with_value`     | Replace with a static value                     | `NY` → `Unknown`                        |
| `replace_exact`          | Replace exact matches by mapping                | `active` → `A`                          |
| `replace_by_contains`    | Replace if substring exists                     | `error: 404` → `ERR`                    |
| `sequential_numeric`     | Sequential numeric pseudonyms                   | `Alice, Bob` → `U 1, U 2`               |
| `sequential_alpha`       | Sequential alphabetic pseudonyms                | `Alice, Bob` → `U A, U B`               |
| `truncate`               | Truncate strings to fixed length                | `Alexander` → `Alex`                    |
| `initials_only`          | Convert names to initials                       | `John Doe` → `J.D.`                     |
| `generalize_age`         | Group ages in 10y ranges                        | `25` → `20-29`                          |
| `generalize_date`        | Reduce granularity (year or month_year)         | `2025-07-20` → `2025`                   |
| `generalize_number_range`| Bucketize numbers by interval                   | `23` → `20-29`                          |
| `random_choice`          | Randomly pick value from list                   | `SP` → `AA` or `BB`                     |
| `replace_with_random_digits` | Random digits with fixed length              | `11111` → `80239`                       |
| `shuffle`                | Shuffle column values                          | `[A,B,C]` → `[B,C,A]`                   |
| `date_offset`            | Random offset within day range                  | `2025-07-20` → `2025-07-18`             |
| `coalesce_cols`          | Take first non-null from multiple cols          | `(None, Y)` → `Y`                       |
| `round_number`           | Round numeric values to fixed decimals          | `3.14159` → `3.14`                      |
| `round_date`             | Round date down to month or year start          | `2025-07-29` → `2025-07-01`             |

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

We love contributions! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, coding standards, how to add a new anonymization method, tests and the PR checklist.

## 📄 Notice

See **[NOTICE](NOTICE)** for attribution details.

## 📜 License

MIT © Jeferson Peter
