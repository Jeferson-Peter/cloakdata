# Contributing to CloakData

Thanks for your interest in contributing! This guide explains how to set up your environment, coding standards,
how to add a new anonymization method, write tests, and open great pull requests.

> For user-facing usage instructions, examples, and supported methods, see **README.md**.

## 0) Code of Conduct
By participating, you agree to uphold a friendly and respectful environment. (If a `CODE_OF_CONDUCT.md` exists, it applies here.)

## 1) Dev Setup
```bash
# clone & install dev deps
git clone https://github.com/youruser/cloakdata
cd cloakdata
uv sync

# run checks locally
pytest -v
ruff check src/
pre-commit install
pre-commit run --all-files
```

## 2) Branching & Commits
- Create a feature branch from `main`: `git checkout -b feat/<short-name>`
- Use conventional-ish messages when possible (e.g., `feat(core): add round_date`)

## 3) Coding Standards
- Python ≥ 3.10
- Keep functions **pure** and side-effect free; methods return **`pl.Expr`**
- Naming: public methods in `AnonymizationMethods` should be **snake_case** and self-explanatory
- Type hints required for new public functions
- Linting: `ruff`; pre-commit must pass

## 4) Tests
- Add/extend tests under `tests/` with `pytest`
- Cover happy-path + edge cases (nulls, wrong types, empty strings)
- Prefer minimal DataFrames to keep tests fast

**Example test template**
```python
import polars as pl
from cloakdata.core import AnonymizationMethods as AM

def test_mask_partial_basic():
    df = pl.DataFrame({"x": ["abcdef", "12345"]})
    cfg = {"columns": {"x": {"method": "mask_partial", "params": {"visible_start": 2, "visible_end": 2}}}}
    out = AM.anonymize(df, cfg)
    assert out["x"].to_list() == ["ab**ef", "12345"]
```

## 5) Adding a New Method
1. Implement a `@staticmethod` in `AnonymizationMethods` (in `core.py`).
   - Signature: `(df: pl.DataFrame, col: str, params: dict) -> pl.Expr`
   - Return a **Polars expression**; do **not** mutate `df` directly
2. The method is auto-registered by `build_dispatch_map()` if it is public
3. Document parameters and behavior via docstring
4. Add examples to README ("Examples by Method") if applicable
5. Add tests that validate typical usage + null preservation

**Minimal method template**
```python
@staticmethod
def my_strategy(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """One-line description.

    Params:
        - foo (str): what it does
    """
    return pl.col(col)  # replace with your expression
```

## 6) PR Checklist
- [ ] Tests added/updated and passing (`pytest -v`)
- [ ] Lint passes (`ruff check src/`)
- [ ] Pre-commit passes (`pre-commit run --all-files`)
- [ ] README updated (examples/table) if a user-facing method changed
- [ ] Backward-compat notes included if behavior changed

## 7) Issue Types
- **bug:** incorrect result, crash, or broken docs
- **feat:** new anonymization method or API
- **docs:** README/guide improvements
- **perf:** speed/memory improvements

## 8) Release Notes
We follow SemVer when possible. Breaking changes bump **MAJOR**. Deprecations should include a warning in one release before removal.

---

## Code of Conduct
By participating in this project you agree to foster a friendly, respectful environment.
If a `CODE_OF_CONDUCT.md` is present, it applies. Otherwise, please follow the spirit of the Contributor Covenant.

## License & Attribution
By contributing, you agree that your contributions will be licensed under the MIT License of this repository.
