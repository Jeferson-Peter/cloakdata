import polars as pl

from .catalog import native_method

@native_method
def sequential_numeric(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    start = int(params.get("start", 1))
    prefix = params.get("prefix", "val")

    uniq_s = df.select(pl.col(col)).unique().to_series()

    if prefix is None:
        labels_int = list(range(start, start + len(uniq_s)))
        mapping = dict(zip(uniq_s.to_list(), labels_int, strict=False))
        expr = pl.col(col).replace(list(mapping.keys()), list(mapping.values()))
        return expr.cast(pl.Int64).alias(col)

    old_utf8 = uniq_s.cast(pl.Utf8).to_list()
    new_utf8 = [f"{prefix} {i}" for i in range(start, start + len(old_utf8))]
    expr = pl.col(col).cast(pl.Utf8).replace(old_utf8, new_utf8).cast(pl.Utf8)
    return expr.alias(col)


@native_method
def sequential_alpha(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    def alpha_to_num(s: str) -> int:
        s = (s or "A").strip().upper()
        if not s:
            return 1
        n = 0
        for ch in s:
            if "A" <= ch <= "Z":
                n = n * 26 + (ord(ch) - 64)
        return max(n, 1)

    def num_to_alpha(n: int) -> str:
        out = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            out = chr(65 + r) + out
        return out

    params = params or {}
    start_label = params.get("start", "A")
    start_idx = alpha_to_num(start_label)
    prefix = params.get("prefix", "val")

    uniques = df.select(pl.col(col)).unique(maintain_order=True).to_series().to_list()
    labels = [
        f"{prefix} {num_to_alpha(idx)}" if prefix is not None else num_to_alpha(idx)
        for idx, _ in enumerate(uniques, start=start_idx)
    ]

    mapping = dict(zip(uniques, labels, strict=False))
    return pl.col(col).replace(list(mapping.keys()), list(mapping.values())).alias(col)
