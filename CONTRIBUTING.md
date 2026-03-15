# Contributing to CloakData

Thanks for your interest in contributing. This guide covers setup, coding standards,
tests, and how to add new built-in anonymization methods.

> For user-facing usage instructions, examples, and supported methods, see `README.md`.

## 0) Code of Conduct
By participating, you agree to uphold a friendly and respectful environment.

## 1) Dev Setup
```bash
git clone https://github.com/youruser/cloakdata
cd cloakdata
uv sync --extra dev

pytest -v
ruff check src/
pre-commit install
pre-commit run --all-files
```

## 2) Branching and Commits
- Create a feature branch from `main`
- Use clear commit messages when possible, for example `feat(core): add round_date`

## 3) Coding Standards
- Python >= 3.12
- Keep functions pure and side-effect free
- Built-in methods should return `pl.Expr`
- Use snake_case for built-in method names
- Add type hints for new public functions
- Keep `ruff` and pre-commit green

## 4) Tests
- Add or extend tests under `tests/` with `pytest`
- Cover happy path plus edge cases such as nulls, wrong types, and empty strings
- Prefer minimal DataFrames to keep tests fast

Example test template:
```python
import polars as pl

from cloakdata import anonymize


def test_mask_partial_basic():
    df = pl.DataFrame({"x": ["abcdef", "12345"]})
    cfg = {
        "columns": {
            "x": {
                "method": "mask_partial",
                "params": {"visible_start": 2, "visible_end": 2},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out["x"].to_list() == ["ab**ef", "12345"]
```

## 5) Adding a New Method
1. Implement a function in the appropriate module under `src/cloakdata/native_methods/`.
2. Use the signature `(df: pl.DataFrame, col: str, params: dict) -> pl.Expr`.
3. Return a Polars expression and do not mutate `df` directly.
4. Export the function in `src/cloakdata/native_methods/__init__.py`.
5. Decorate the function with `@native_method`.
6. Document parameters and behavior with a docstring.
7. Add README examples if the method is user-facing.
8. Add tests for normal behavior and null handling.

Minimal method template:
```python
import polars as pl

from cloakdata.native_methods import native_method


@native_method
def my_strategy(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """One-line description."""
    return pl.col(col)
```

## 6) PR Checklist
- [ ] Tests added or updated and passing
- [ ] Lint passes with `ruff check src/`
- [ ] Pre-commit passes
- [ ] README updated if user-facing behavior changed
- [ ] Backward-compatibility notes included if behavior changed

## 7) Issue Types
- `bug`: incorrect result, crash, or broken docs
- `feat`: new anonymization method or API
- `docs`: README or guide improvements
- `perf`: speed or memory improvements

## 8) Release Notes
We follow SemVer when possible. Breaking changes should bump the major version.

## License and Attribution
By contributing, you agree that your contributions will be licensed under the MIT License of this repository.
