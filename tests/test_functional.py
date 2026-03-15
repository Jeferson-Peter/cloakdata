import polars as pl

from cloakdata import anonymize, get_all_methods, register_method, unregister_method


def test_functional_end_to_end_multiple_methods():
    df = pl.DataFrame(
        {
            "name": ["Alice Smith", "Bob Jones"],
            "email": ["alice@example.com", "bob@example.com"],
            "age": [25, 42],
            "city": ["Curitiba", "Joinville"],
            "score": [3.14159, 7.89123],
        }
    )

    config = {
        "columns": {
            "name": {"method": "initials_only"},
            "email": {"method": "mask_email"},
            "age": {"method": "generalize_age"},
            "city": {"method": "replace_exact", "params": {"mapping": {"Curitiba": "CWB"}}},
            "score": {"method": "round_number", "params": {"digits": 2}},
        }
    }

    out = anonymize(df, config)

    assert out["name"].to_list() == ["A.S.", "B.J."]
    assert out["email"].to_list() == ["xxxxx@example.com", "xxxxx@example.com"]
    assert out["age"].to_list() == ["20-29", "40-49"]
    assert out["city"].to_list() == ["CWB", "Joinville"]
    assert out["score"].to_list() == [3.14, 7.89]


def test_functional_built_in_and_custom_method_together():
    def suffix_tag(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        suffix = params.get("suffix", "_anon")
        return (pl.col(col).cast(pl.Utf8) + pl.lit(suffix)).alias(col)

    register_method(suffix_tag, name="suffix_tag")
    try:
        df = pl.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "email": ["alice@example.com", "bob@example.com"],
            }
        )

        config = {
            "columns": {
                "name": {"method": "suffix_tag", "params": {"suffix": "_safe"}},
                "email": {"method": "mask_email"},
            }
        }

        out = anonymize(df, config)

        assert out["name"].to_list() == ["Alice_safe", "Bob_safe"]
        assert out["email"].to_list() == ["xxxxx@example.com", "xxxxx@example.com"]
    finally:
        unregister_method("suffix_tag")


def test_functional_conditional_rule_on_missing_column_creates_output_column():
    df = pl.DataFrame(
        {
            "status": ["active", "inactive"],
            "name": ["Alice", "Bob"],
        }
    )

    config = {
        "columns": {
            "nickname": {
                "method": "replace_with_value",
                "params": {"value": "hidden"},
                "condition": {"column": "status", "operator": "equals", "value": "active"},
            }
        }
    }

    out = anonymize(df, config)

    assert out["nickname"].to_list() == ["hidden", None]


def test_functional_drop_and_transform_can_coexist():
    df = pl.DataFrame(
        {
            "name": ["Alice Smith"],
            "email": ["alice@example.com"],
            "secret": ["top-secret"],
        }
    )

    config = {
        "columns": {
            "name": {"method": "initials_only"},
            "email": {"method": "mask_email"},
            "secret": {"method": "drop"},
        }
    }

    out = anonymize(df, config)

    assert "secret" not in out.columns
    assert out["name"].to_list() == ["A.S."]
    assert out["email"].to_list() == ["xxxxx@example.com"]


def test_functional_public_method_catalog_contains_core_methods():
    methods = get_all_methods()

    assert "full_mask" in methods
    assert "mask_email" in methods
    assert "generalize_age" in methods
    assert "round_date" in methods
