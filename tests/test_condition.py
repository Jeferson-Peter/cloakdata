from cloakdata import anonymize


def test_condition_apply_only_when_true(df_factory, cfg_factory):
    df = df_factory(age=[22, 31, 41], city=["Curitiba", "Joinville", "São Paulo"])
    cfg = {
        "columns": {
            "city": {
                "method": "replace_with_value",
                "params": {"value": "REDACTED"},
                "condition": {"col": "age", "op": ">", "value": 30},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["Curitiba", "REDACTED", "REDACTED"]


def test_condition_leaves_others_untouched(df_factory, cfg_factory):
    df = df_factory(age=[10, 20, 30], city=["A", "B", "C"])
    cfg = {
        "columns": {
            "city": {
                "method": "replace_with_value",
                "params": {"value": "X"},
                "condition": {"col": "age", "op": ">", "value": 30},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["A", "B", "C"]


def test_condition_on_missing_target_column_creates_and_sets(df_factory, cfg_factory):
    df = df_factory(age=[18, 35, 50])
    cfg = {
        "columns": {
            "flag": {
                "method": "replace_with_value",
                "params": {"value": "ADULT"},
                "condition": {"col": "age", "op": ">=", "value": 35},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out.columns == ["age", "flag"]
    assert out["flag"].to_list() == [None, "ADULT", "ADULT"]


def test_multiple_rules_on_same_column_with_and_without_condition(df_factory, cfg_factory):
    df = df_factory(age=[25, 40, 60], city=["A", "B", "C"])
    cfg = {
        "columns": {
            "city": [
                {"method": "replace_with_value", "params": {"value": "DEFAULT"}},
                {
                    "method": "replace_with_value",
                    "params": {"value": "COND"},
                    "condition": {"col": "age", "op": ">=", "value": 40},
                },
            ]
        }
    }
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["DEFAULT", "COND", "COND"]


def test_condition_with_nulls_in_condition_column(df_factory, cfg_factory):
    df = df_factory(age=[None, 29, 31], city=["X", "Y", "Z"])
    cfg = {
        "columns": {
            "city": {
                "method": "replace_with_value",
                "params": {"value": "OK"},
                "condition": {"col": "age", "op": ">", "value": 30},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["X", "Y", "OK"]


def test_condition_contains_string(df_factory, cfg_factory):
    df = df_factory(city=["Rua A", "Avenida Central", "Travessa B"])
    cfg = {
        "columns": {
            "city": {
                "method": "replace_with_value",
                "params": {"value": "MASK"},
                "condition": {"col": "city", "op": "contains", "value": "Avenida"},
            }
        }
    }
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["Rua A", "MASK", "Travessa B"]
