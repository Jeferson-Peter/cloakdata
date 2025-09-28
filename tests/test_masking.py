import polars as pl

from cloakdata import anonymize


def test_full_mask_default_preserves_nulls(city_df, cfg_factory):
    """Masks non-nulls with '*****' and preserves nulls."""
    cfg = cfg_factory("full_mask", "city")
    out = anonymize(city_df, cfg)["city"]

    non_null = city_df["city"].is_not_null()
    assert (out.filter(non_null) == "*****").all()

    nulls = city_df["city"].is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_full_mask_fixed_custom(city_df, cfg_factory):
    """Masks non-nulls with a fixed custom literal and keeps nulls untouched."""
    cfg = cfg_factory("full_mask", "city", params={"char": "X", "len": 8})
    out = anonymize(city_df, cfg)

    non_null = city_df["city"].is_not_null()
    assert (out["city"].filter(non_null) == "XXXXXXXX").all()

    null_mask = city_df["city"].is_null()
    assert out["city"].filter(null_mask).null_count() == null_mask.sum()


def test_full_mask_literal(city_df, cfg_factory):
    """Uses mask_literal for non-nulls and preserves nulls."""
    cfg = cfg_factory("full_mask", "city", params={"mask_literal": "REDACTED"})
    out = anonymize(city_df, cfg)

    non_null = city_df["city"].is_not_null()
    assert (out["city"].filter(non_null) == "REDACTED").all()

    null_mask = city_df["city"].is_null()
    assert out["city"].filter(null_mask).null_count() == null_mask.sum()


def test_full_mask_dynamic_match_length(city_df, cfg_factory):
    """Produces masks with the same length as the original using the chosen char."""
    cfg = cfg_factory("full_mask", "city", params={"match_length": True, "char": "#"})
    out = anonymize(city_df, cfg)

    orig = city_df["city"]
    masked = out["city"]

    non_null = orig.is_not_null()
    null_mask = orig.is_null()

    assert (masked.str.len_chars().filter(non_null) == orig.str.len_chars().filter(non_null)).all()

    assert masked.filter(non_null).str.contains(r"^#+$", literal=False).all()

    assert masked.filter(null_mask).null_count() == null_mask.sum()


def test_full_mask_overwrite_nulls(city_df, cfg_factory):
    """When preserve_nulls=False, every value becomes the fixed mask."""
    cfg = cfg_factory("full_mask", "city", params={"preserve_nulls": False})
    out = anonymize(city_df, cfg)

    assert (out["city"] == "*****").all()


def test_full_mask_idempotent(city_df, cfg_factory):
    """Applying the same config twice yields the same series."""
    cfg = cfg_factory("full_mask", "city", params={"match_length": True, "char": "*"})
    out1 = anonymize(city_df, cfg)
    out2 = anonymize(out1, cfg)
    assert out1["city"].to_list() == out2["city"].to_list()


def test_mask_email_default(base_df, cfg_factory):
    """Masks local part with 'xxxxx', preserves domain, keeps nulls."""
    cfg = cfg_factory("mask_email", "email")
    out = anonymize(base_df, cfg)["email"]

    valid = base_df["email"].is_not_null() & base_df["email"].str.contains("@", literal=True)
    assert out.filter(valid).str.contains(r"^xxxxx@[^@]+$", literal=False).all()

    invalid = base_df["email"].is_not_null() & ~base_df["email"].str.contains("@", literal=True)
    assert (out.filter(invalid) == "xxxxx@hidden.com").all()

    nulls = base_df["email"].is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_mask_email_custom_mask(df_factory, cfg_factory):
    """Masks local part with a custom mask, uses default fallback, keeps nulls."""
    df = df_factory(email=["a@b.com", "user@site.net", "no-at-here", None])
    cfg = cfg_factory("mask_email", "email", mask="***")
    out = anonymize(df, cfg)["email"]

    valid = df["email"].is_not_null() & df["email"].str.contains("@", literal=True)
    assert out.filter(valid).str.contains(r"^\*\*\*@[^@]+$", literal=False).all()

    invalid = df["email"].is_not_null() & ~df["email"].str.contains("@", literal=True)
    assert (out.filter(invalid) == "***@hidden.com").all()

    nulls = df["email"].is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_mask_email_custom_fallback(df_factory, cfg_factory):
    """Masks local part with 'xxxxx' and uses custom fallback domain for invalid emails."""
    df = df_factory(email=["john@x.io", "bad email", None])
    cfg = cfg_factory("mask_email", "email", fallback_domain="anon.io")
    out = anonymize(df, cfg)["email"]

    valid = df["email"].str.contains("@", literal=True)
    assert out.filter(valid).str.contains(r"^xxxxx@x\.io$", literal=False).all()

    invalid = df["email"].is_not_null() & ~valid
    assert (out.filter(invalid) == "xxxxx@anon.io").all()

    nulls = df["email"].is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_mask_email_overwrite_nulls(df_factory, cfg_factory):
    """When preserve_nulls=False, masks both invalid and null emails with fallback."""
    df = df_factory(email=["ok@d.com", None, "broken"])
    cfg = cfg_factory("mask_email", "email", preserve_nulls=False)
    out = anonymize(df, cfg)["email"]

    assert out.null_count() == 0

    is_invalid_or_null = df["email"].is_null() | ~df["email"].str.contains("@", literal=True)
    assert (out.filter(is_invalid_or_null) == "xxxxx@hidden.com").all()

    valid = df["email"].is_not_null() & df["email"].str.contains("@", literal=True)
    assert out.filter(valid).str.contains(r"^xxxxx@[^@]+$", literal=False).all()


def test_mask_email_idempotent(df_factory, cfg_factory):
    """Applying the same config twice yields the same email series."""
    df = df_factory(email=["a.b@c.com", "no-at", None])
    cfg = cfg_factory("mask_email", "email", mask="###")
    out1 = anonymize(df, cfg)
    out2 = anonymize(out1, cfg)
    assert out1["email"].to_list() == out2["email"].to_list()


def test_mask_partial(city_df, cfg_factory):
    """Masks the middle part of the string, keeping defined prefix and suffix."""
    cfg = cfg_factory("mask_partial", "city", prefix=1, suffix=1, mask="*")
    out = anonymize(city_df, cfg)
    assert len(out["city"][0]) == len(city_df["city"][0])
    assert out["city"][0][0] == city_df["city"][0][0]
    assert out["city"][0][-1] == city_df["city"][0][-1]


def test_truncate(city_df, cfg_factory):
    """Truncates strings to the configured length."""
    cfg = cfg_factory("truncate", "city", length=3)
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == [s[:3] for s in city_df["city"].to_list()]


def test_mask_number(numeric_df, cfg_factory):
    """Masks numeric values, keeping the defined number of leading characters."""
    cfg = cfg_factory("mask_number", "num", keep=1, mask="X")
    out = anonymize(numeric_df, cfg)
    assert out["num"].dtype == pl.Utf8
