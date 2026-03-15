import polars as pl
import pytest

from cloakdata.native_methods import NATIVE_METHODS, native_method


def test_native_catalog_is_populated_on_import():
    assert "full_mask" in NATIVE_METHODS
    assert "round_date" in NATIVE_METHODS
    assert "coalesce_cols" in NATIVE_METHODS


def test_native_method_decorator_registers_default_name():
    initial = dict(NATIVE_METHODS)

    @native_method
    def temp_native(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        return pl.col(col)

    try:
        assert "temp_native" in NATIVE_METHODS
        assert NATIVE_METHODS["temp_native"] is temp_native
    finally:
        NATIVE_METHODS.clear()
        NATIVE_METHODS.update(initial)


def test_native_method_decorator_registers_alias_name():
    initial = dict(NATIVE_METHODS)

    @native_method(name="temp_alias")
    def temp_native_alias(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        return pl.col(col)

    try:
        assert "temp_alias" in NATIVE_METHODS
        assert NATIVE_METHODS["temp_alias"] is temp_native_alias
    finally:
        NATIVE_METHODS.clear()
        NATIVE_METHODS.update(initial)


def test_native_method_decorator_rejects_duplicate_name():
    initial = dict(NATIVE_METHODS)

    @native_method(name="temp_duplicate")
    def first_temp_native(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        return pl.col(col)

    try:
        with pytest.raises(ValueError):

            @native_method(name="temp_duplicate")
            def second_temp_native(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
                return pl.col(col)
    finally:
        NATIVE_METHODS.clear()
        NATIVE_METHODS.update(initial)
