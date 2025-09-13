from cloakdata import anonymize


def test_coalesce_cols_basic(df_factory, cfg_factory):
    df = df_factory(city=[None, "Curitiba", None], email=["a@x.com", "b@x.com", "c@x.com"])
    cfg = cfg_factory("coalesce_cols", "city", columns=["city", "email"])
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["a@x.com", "Curitiba", "c@x.com"]
    assert set(out.columns) == {"city", "email"}


def test_coalesce_cols_all_nulls_yields_null(df_factory, cfg_factory):
    df = df_factory(a=[None, None], b=[None, None])
    cfg = cfg_factory("coalesce_cols", "a", columns=["a", "b"])
    out = anonymize(df, cfg)
    assert out["a"].to_list() == [None, None]


def test_coalesce_cols_order_matters(df_factory, cfg_factory):
    df = df_factory(primary=[None, "P2", None], backup=["B1", "B2", None], third=["T1", None, "T3"])
    cfg = cfg_factory("coalesce_cols", "primary", columns=["primary", "backup", "third"])
    out = anonymize(df, cfg)
    assert out["primary"].to_list() == ["B1", "P2", "T3"]
