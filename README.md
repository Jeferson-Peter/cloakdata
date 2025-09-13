# 🔐 CloakData — Data Anonymizer

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
2. Define anonymization rules in a simple JSON/YAML config.
3. Call `anonymize(df, config)` → get a safe anonymized DataFrame.

---

## 🧪 Example Config

```json
{
  "columns": {
    "name": "initials_only",
    "email": "mask_email",
    "phone": "mask_number",
    "cpf": {
      "method": "replace_with_fake",
      "params": { "digits": 11 }
    },
    "status": {
      "method": "replace_by_dict",
      "params": { "mapping": { "active": "A", "inactive": "I" } }
    },
    "id_seq": { "method": "sequential_numeric", "params": { "prefix": "ID" } },
    "ref_code": { "method": "sequential_alpha", "params": { "prefix": "REF" } },
    "comments": { "method": "truncate", "params": { "length": 5 } },
    "age": "generalize_age",
    "birth_date": { "method": "generalize_date", "params": { "mode": "month_year" } },
    "state": { "method": "random_choice", "params": { "choices": ["SP","RJ","MG","BA"] } },
    "last_access": { "method": "date_offset", "params": { "min_days": -2, "max_days": 2 } },
    "feedback": "shuffle"
  }
}
```

---

## 🧠 Conditional Rules

Apply transformations only when conditions are met:

```json
"cpf": {
  "method": "replace_with_fake",
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
        "name": "initials_only",
        "email": "mask_email",
        "age": "generalize_age"
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
- [ ] CLI interface (`cloakdata file.csv --config config.json`)
- [ ] Parallel processing for large datasets

---

## 📜 License

MIT © [Your Name]
