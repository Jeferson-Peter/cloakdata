# 🔐 CloakData — Data Anonymizer

![PyPI](https://img.shields.io/pypi/v/cloakdata.svg)
![Python](https://img.shields.io/pypi/pyversions/cloakdata.svg)
![Downloads](https://img.shields.io/pypi/dm/cloakdata.svg)
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

## 📜 License

MIT © Jeferson Peter
