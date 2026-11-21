"""Check behavior through an installed CloakData distribution."""

import hmac
from pathlib import Path

import polars as pl

import cloakdata


def main() -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    assert not Path(cloakdata.__file__).resolve().is_relative_to(source)

    key = bytes(range(32))  # Public fixture, never a production key.
    frame = pl.DataFrame({"id": ["private-a", "private-b"], "allow": [True, None]})
    config = {
        "columns": {
            "id": [
                {
                    "method": "replace_with_value",
                    "params": {"value": "SAFE"},
                    "condition": {"col": "allow", "op": "is_false"},
                },
                {"method": "hmac_value", "params": {"key": key}},
            ]
        }
    }
    expected = [hmac.digest(key, value, "sha256").hex() for value in (b"private-a", b"SAFE")]
    assert cloakdata.anonymize(frame, config)["id"].to_list() == expected


if __name__ == "__main__":
    main()
