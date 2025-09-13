from cloakdata import anonymize


def excel_letters(n: int) -> list[str]:
    out = []
    for i in range(1, n + 1):
        s = ""
        x = i
        while x > 0:
            x, r = divmod(x - 1, 26)
            s = chr(65 + r) + s
        out.append(s)
    return out


def test_sequential_alpha_basic(df_factory, cfg_factory):
    df = df_factory(col=["x", "y", "z"])
    cfg = cfg_factory("sequential_alpha", "col", start="A")

    out = anonymize(df, cfg)
    assert out["col"].to_list() == ["A", "B", "C"], f"Expected A,B,C; got {out['col'].to_list()}"


def test_sequential_alpha_wraps_after_z(df_factory, cfg_factory):
    n = 28
    df = df_factory(col=[f"v{i}" for i in range(n)])
    cfg = cfg_factory("sequential_alpha", "col", start="A")

    out = anonymize(df, cfg)
    expected = excel_letters(n)
    assert (
        out["col"].to_list() == expected
    ), f"Expected {expected[-3:]} at the tail; got {out['col'].to_list()[-3:]}"


def test_sequential_numeric_basic(df_factory, cfg_factory):
    df = df_factory(col=["a", "b", "c", "d"])
    cfg = cfg_factory("sequential_numeric", "col", start=1)

    out = anonymize(df, cfg)
    assert out["col"].to_list() == [1, 2, 3, 4], f"Expected [1,2,3,4]; got {out['col'].to_list()}"


def test_sequential_numeric_custom_start(df_factory, cfg_factory):
    df = df_factory(col=["a", "b", "c"])
    cfg = cfg_factory("sequential_numeric", "col", start=100)

    out = anonymize(df, cfg)
    assert out["col"].to_list() == [
        100,
        101,
        102,
    ], f"Expected [100,101,102]; got {out['col'].to_list()}"


def test_sequential_preserves_row_count(df_factory, cfg_factory):
    df = df_factory(col=["x"] * 7)
    cfg_alpha = cfg_factory("sequential_alpha", "col", start="A")
    cfg_num = cfg_factory("sequential_numeric", "col", start=10)

    out_alpha = anonymize(df, cfg_alpha)
    out_num = anonymize(df, cfg_num)

    assert out_alpha.height == df.height
    assert out_num.height == df.height
