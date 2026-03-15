import polars as pl
import pytest

from cloakdata import (
    anonymize,
    get_all_methods,
    get_registered_methods,
    register_method,
    unregister_method,
)
from cloakdata.registry import build_native_dispatch_map


def _cleanup_custom(name: str):
    try:
        unregister_method(name)
    except Exception:
        pass


def test_register_rejects_bad_signature():
    def bad(df, col):
        return pl.col(col)

    with pytest.raises(TypeError):
        register_method(bad)


def test_register_allows_underscore_params():
    def ok(_df, _col, _params):
        return pl.lit("X")

    register_method(ok, name="ok_under")
    assert "ok_under" in get_registered_methods()
    _cleanup_custom("ok_under")


def test_register_blocks_override_of_native():
    def full_mask(df, col, params):
        return pl.lit("NOPE")

    with pytest.raises(ValueError):
        register_method(full_mask, name="full_mask")


def test_register_blocks_duplicate_custom_name():
    def m1(df, col, params):
        return pl.lit("A")

    def m2(df, col, params):
        return pl.lit("B")

    register_method(m1, name="dup_name")
    with pytest.raises(ValueError):
        register_method(m2, name="dup_name")
    _cleanup_custom("dup_name")


def test_dispatch_executes_custom_in_anonymize():
    def mask_vowels(df, col, params):
        return (
            pl.col(col).str.slice(0, 1)
            + pl.col(col).str.slice(1).str.replace_all(r"(?i)[aeiou]", "*")
        ).alias(col)

    try:
        register_method(mask_vowels)

        df = pl.DataFrame({"name": ["Alice", "Bob"]})
        cfg = {"columns": {"name": [{"method": "mask_vowels"}]}}

        out = anonymize(df, cfg)
        assert out.get_column("name").to_list() == ["Al*c*", "B*b"]
    finally:
        unregister_method("mask_vowels")


def test_native_dispatch_map_uses_explicit_catalog():
    dispatch = build_native_dispatch_map()

    assert "full_mask" in dispatch
    assert "round_date" in dispatch
    assert "coalesce_cols" in dispatch


def test_get_all_methods_includes_native_and_custom():
    def temp_custom(_df, _col, _params):
        return pl.lit("X")

    register_method(temp_custom, name="temp_custom")
    try:
        all_methods = get_all_methods()
        assert "full_mask" in all_methods
        assert "temp_custom" in all_methods
    finally:
        unregister_method("temp_custom")
