from cloakdata import anonymize


def test_initials_only_basic_preserves_nulls(df_factory, cfg_factory):
    """Converts simple names into initials and preserves null values."""
    df = df_factory(name=["John Doe", "Mary Jane", None])
    cfg = cfg_factory("initials_only", "name")

    out = anonymize(df, cfg)["name"]

    assert out.to_list()[:2] == ["J.D.", "M.J."]
    assert out.null_count() == 1
    assert out[-1] is None


def test_initials_only_handles_extra_spaces(df_factory, cfg_factory):
    """Handles multiple spaces and trims correctly before extracting initials."""
    df = df_factory(name=["  Ana   Clara  Silva ", " João   "])
    cfg = cfg_factory("initials_only", "name")

    out = anonymize(df, cfg)["name"].to_list()

    assert out == ["A.C.S.", "J."]


def test_initials_only_single_word_and_empty(df_factory, cfg_factory):
    """
    A single-word name yields a single initial;
    empty/whitespace-only strings return an empty string.
    """
    df = df_factory(name=["Madonna", "   ", " X "])
    cfg = cfg_factory("initials_only", "name")

    out = anonymize(df, cfg)["name"].to_list()

    assert out[0] == "M."
    assert out[1] == ""
    assert out[2] == "X."


def test_initials_only_overwrite_nulls(df_factory, cfg_factory):
    """
    Null values should remain null even when preserve_nulls=False.
    """
    df = df_factory(name=["John Doe", None])
    cfg = cfg_factory("initials_only", "name", preserve_nulls=False)

    out = anonymize(df, cfg)["name"].to_list()

    assert out == ["J.D.", None]


def test_initials_only_idempotent(df_factory, cfg_factory):
    """Applying the method twice should produce identical results."""
    df = df_factory(name=["John Doe", "Ana Clara"])
    cfg = cfg_factory("initials_only", "name")

    out1 = anonymize(df, cfg)
    out2 = anonymize(out1, cfg)

    assert out1["name"].to_list() == out2["name"].to_list()
