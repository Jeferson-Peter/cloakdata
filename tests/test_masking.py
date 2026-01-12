import polars as pl
import pytest

from cloakdata import anonymize

KEEP_DEFAULT = 3
KEEP_TWO = 2
FIXED_LEN_4 = 4
MASK_STAR = "*"
MASK_X = "X"
MASK_HASH = "#"
SUFFIX_LEN4 = "#" * FIXED_LEN_4


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
    cfg = cfg_factory("full_mask", "city", char="X", len=8)
    out = anonymize(city_df, cfg)

    non_null = city_df["city"].is_not_null()
    assert (out["city"].filter(non_null) == "XXXXXXXX").all()

    null_mask = city_df["city"].is_null()
    assert out["city"].filter(null_mask).null_count() == null_mask.sum()


def test_full_mask_literal(city_df, cfg_factory):
    """Uses mask_literal for non-nulls and preserves nulls."""
    cfg = cfg_factory("full_mask", "city", mask_literal="REDACTED")
    out = anonymize(city_df, cfg)

    non_null = city_df["city"].is_not_null()
    assert (out["city"].filter(non_null) == "REDACTED").all()

    null_mask = city_df["city"].is_null()
    assert out["city"].filter(null_mask).null_count() == null_mask.sum()


def test_full_mask_dynamic_match_length(city_df, cfg_factory):
    """Produces masks with the same length as the original using the chosen char."""
    cfg = cfg_factory("full_mask", "city", match_length=True, char="#")
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
    cfg = cfg_factory("full_mask", "city", preserve_nulls=False)
    out = anonymize(city_df, cfg)

    assert (out["city"] == "*****").all()


def test_full_mask_idempotent(city_df, cfg_factory):
    """Applying the same config twice yields the same series."""
    cfg = cfg_factory("full_mask", "city", match_length=True, char="*")
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


def test_truncate_basic(city_df, cfg_factory):
    """Truncates strings to the configured length."""
    cfg = cfg_factory("truncate", "city", length=3)
    out = anonymize(city_df, cfg)["city"]

    expected = [s[:3] if s is not None else None for s in city_df["city"].to_list()]
    assert out.to_list() == expected


def test_truncate_preserves_nulls(city_df, cfg_factory):
    """Nulls must remain null (default preserve_nulls=True)."""
    cfg = cfg_factory("truncate", "city", length=2)
    out = anonymize(city_df, cfg)["city"]

    null_mask = city_df["city"].is_null()
    assert out.filter(null_mask).null_count() == null_mask.sum()


def test_truncate_no_preserve_nulls(df_factory, cfg_factory):
    """When preserve_nulls=False, nulls become empty string truncated to ''."""
    df = df_factory(city=["Porto", None, "Roma"])
    cfg = cfg_factory("truncate", "city", length=2, preserve_nulls=False)

    out = anonymize(df, cfg)["city"].to_list()
    assert out == ["Po", None, "Ro"]


def test_truncate_zero_length(df_factory, cfg_factory):
    """length=0 returns empty strings but preserves nulls."""
    df = df_factory(city=["ABCDE", None, "XYZ"])
    cfg = cfg_factory("truncate", "city", length=0)

    out = anonymize(df, cfg)["city"].to_list()
    assert out == ["", None, ""]


def test_truncate_works_with_non_string_inputs(df_factory, cfg_factory):
    """Non-string inputs must be cast to string before truncation."""
    df = df_factory(col=[12345, True, None, -50])
    cfg = cfg_factory("truncate", "col", length=3)

    out = anonymize(df, cfg)["col"].to_list()
    expected = [str(v)[:3] if v is not None else None for v in df["col"].to_list()]
    assert out == expected


def test_truncate_length_validation(df_factory, cfg_factory):
    """Invalid length values must raise ValueError."""
    df = df_factory(col=["abc", "def"])

    with pytest.raises(ValueError, match=">= 0"):
        anonymize(df, cfg_factory("truncate", "col", length=-1))

    with pytest.raises(ValueError, match="integer"):
        anonymize(df, cfg_factory("truncate", "col", length="abc"))


def test_truncate_idempotent(df_factory, cfg_factory):
    """Applying the same truncate config twice must yield the same result."""
    df = df_factory(col=["NewYork", "Berlin", None])
    cfg = cfg_factory("truncate", "col", length=3)

    out1 = anonymize(df, cfg)
    out2 = anonymize(out1, cfg)

    assert out1["col"].to_list() == out2["col"].to_list()


def test_mask_number_default(df_factory, cfg_factory):
    """Default (keep=3, mask='*', dynamic rest): preserve first 3 and fill the rest with '*'."""
    df = df_factory(num=["123456789", "42", None])
    cfg = cfg_factory("mask_number", "num")
    out = anonymize(df, cfg)["num"]
    orig = df["num"].cast(pl.Utf8)

    nn = orig.is_not_null()
    assert (out.filter(nn).str.len_chars() == orig.filter(nn).str.len_chars()).all()
    assert (out.str.slice(0, 3) == orig.str.slice(0, 3)).all()

    tail_gt3 = orig.str.len_chars() > KEEP_DEFAULT
    assert out.filter(tail_gt3).str.slice(3).str.contains(r"^\*+$", literal=False).all()

    nulls = orig.is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_mask_number_custom_keep_mask(df_factory, cfg_factory):
    """Custom keep/mask: keep=2, mask='X'."""
    df = df_factory(num=["987654321", "1", "abc123"])
    cfg = cfg_factory("mask_number", "num", keep=2, mask="X")
    out = anonymize(df, cfg)["num"]
    orig = df["num"].cast(pl.Utf8)

    assert (out.str.slice(0, 2) == orig.str.slice(0, 2)).all()

    tail_gt2 = orig.str.len_chars() > KEEP_TWO
    assert out.filter(tail_gt2).str.slice(2).str.contains(r"^X+$", literal=False).all()


def test_mask_number_fixed_len(df_factory, cfg_factory):
    """Fixed length: keep=2, mask='#', len=4 → result len = min(len(orig),2) + 4 (non-nulls)."""
    df = df_factory(num=["55555", "7", "1234567890", ""])
    cfg = cfg_factory("mask_number", "num", keep=2, mask="#", len=4)
    out = anonymize(df, cfg)["num"]
    orig = df["num"].cast(pl.Utf8)

    tmp = pl.DataFrame({"v": orig}).with_columns(
        expected_len=pl.min_horizontal(pl.col("v").str.len_chars(), pl.lit(2)) + 4
    )
    nn = orig.is_not_null()
    assert (out.filter(nn).str.len_chars() == tmp.filter(nn)["expected_len"]).all()

    ge2 = orig.str.len_chars() >= KEEP_TWO
    assert (out.filter(ge2).str.slice(0, 2) == orig.filter(ge2).str.slice(0, 2)).all()

    lt2 = orig.str.len_chars() < KEEP_TWO
    assert out.filter(lt2).str.starts_with(orig.filter(lt2)).all()

    assert out.filter(nn).str.ends_with("####").all()


def test_mask_number_handles_short_values(df_factory, cfg_factory):
    """Values shorter than keep are unchanged with dynamic rest."""
    df = df_factory(num=["9", "12", "123"])
    cfg = cfg_factory("mask_number", "num")
    out = anonymize(df, cfg)["num"].to_list()
    assert out == ["9", "12", "123"]


def test_mask_number_non_string_inputs(df_factory, cfg_factory):
    """Non-strings are cast to string and masked."""
    df = df_factory(num=[12345, 7, None, -38])
    cfg = cfg_factory("mask_number", "num")
    out = anonymize(df, cfg)["num"]
    orig = df["num"].cast(pl.Utf8)

    nn = orig.is_not_null()
    assert (out.filter(nn).str.len_chars() == orig.filter(nn).str.len_chars()).all()
    assert (out.str.slice(0, 3) == orig.str.slice(0, 3)).all()

    tail_gt3 = orig.str.len_chars() > KEEP_DEFAULT
    assert out.filter(tail_gt3).str.slice(3).str.contains(r"^\*+$", literal=False).all()

    nulls = orig.is_null()
    assert out.filter(nulls).null_count() == nulls.sum()


def test_mask_number_idempotent(df_factory, cfg_factory):
    """Applying the same config twice yields the same series."""
    df = df_factory(num=["123456", "42", None])
    cfg = cfg_factory("mask_number", "num", keep=2, mask="X")
    out1 = anonymize(df, cfg)
    out2 = anonymize(out1, cfg)
    assert out1["num"].to_list() == out2["num"].to_list()
