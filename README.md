# Data Anonymizer Script

This project is designed to anonymize sensitive data using configurable methods in Polars.

## 📦 Features

- Full masking
- Email masking
- Phone number masking
- Replace with static values
- Replace by substring or dictionary
- Sequential numeric and alphabetical replacement
- Truncation
- Initials extraction
- Age and date generalization
- Random choice substitution
- Fake numeric generation
- Column shuffling
- Date offset
- Conditional anonymization

## ⚙️ How it works

1. The script reads a CSV file into a Polars DataFrame.
2. It loads a JSON config describing which columns to anonymize and how.
3. Each rule is applied and the resulting DataFrame is written to output.

## 🧪 Example Config

```json
{
  "columns": {
    "name": "initials_only",
    "email": "mask_email",
    "phone": "mask_number",
    "cpf": {
      "method": "replace_with_fake",
      "params": {
        "digits": 11
      }
    },
    "username": {
      "method": "replace_by_contains",
      "params": {
        "mapping": {
          "admin": "user",
          "root": "guest"
        }
      }
    },
    "status": {
      "method": "replace_by_dict",
      "params": {
        "mapping": {
          "active": "A",
          "inactive": "I"
        }
      }
    },
    "id_seq": {
      "method": "sequential_numeric",
      "params": {
        "prefix": "ID"
      }
    },
    "ref_code": {
      "method": "sequential_alpha",
      "params": {
        "prefix": "REF"
      }
    },
    "comments": {
      "method": "truncate",
      "params": {
        "length": 5
      }
    },
    "age": "generalize_age",
    "birth_date": {
      "method": "generalize_date",
      "params": {
        "mode": "month_year"
      }
    },
    "state": {
      "method": "random_choice",
      "params": {
        "choices": [
          "SP",
          "RJ",
          "MG",
          "BA"
        ]
      }
    },
    "last_access": {
      "method": "date_offset",
      "params": {
        "min_days": -2,
        "max_days": 2
      }
    },
    "feedback": "shuffle"
  }
}
```

## 🧠 Conditional Rules

You can also apply rules based on other column values:

```json
"cpf": {
  "method": "replace_with_fake",
  "params": {
    "digits": 11
  },
  "condition": {
    "column": "status",
    "operator": "equals",
    "value": "active"
  }
}
```

## ⚖️ Supported Condition Operators

| Operator        | Description                            |
|----------------|----------------------------------------|
| equals         | Equal to                               |
| not_equals     | Not equal to                           |
| in             | Value in list                          |
| not_in         | Value not in list                      |
| gt             | Greater than                           |
| gte            | Greater than or equal to               |
| lt             | Less than                              |
| lte            | Less than or equal to                  |
| contains       | Substring exists in string             |
| not_contains   | Substring does not exist in string     |

## 📁 Project Structure

```
.
├── main.py                 # Entry point to run anonymization
├── anonymizer.py           # Core logic for applying anonymization rules
├── config.json             # Example configuration file
├── sensitive_data.csv      # Input file to be anonymized
├── README.md               # Project documentation
└── requirements.txt        # Project dependencies
```

## 🛠️ Requirements

- Python 3.12+
- [Polars](https://pola.rs/) >= 1.31.0
- Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 🚀 Run the script

```bash
python main.py
```

Make sure to update paths for input CSV and config JSON as needed.

## 🔮 Possible Future Features

- Hashing support for specific fields
- Redaction rules using regex
- Support for nested or JSON-style fields
- CLI interface with rich options
- Parallel processing for large datasets