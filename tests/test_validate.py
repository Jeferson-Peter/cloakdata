from cloakdata.validate import validate


def test_validate_accepts_valid_public_config() -> None:
    config = {
        "columns": {
            "email": {"method": "mask_email"},
            "age": {"method": "generalize_age"},
        }
    }

    validate(config)
