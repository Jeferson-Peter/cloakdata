from loguru import logger

from .registry import build_dispatch_map


def validate_config(config: dict, dispatch_map: dict) -> None:
    """
    Validate the anonymization configuration.
    """
    logger.info("Validating anonymization config...")

    if "columns" not in config:
        raise ValueError("Config is missing required 'columns' section.")

    for col_name, rule in config["columns"].items():
        rules = [rule] if isinstance(rule, str | dict) else rule

        for item in rules:
            if isinstance(item, str):
                method = item
            elif isinstance(item, dict):
                method = item.get("method")
            else:
                raise ValueError(
                    f"Invalid rule format for column '{col_name}': must be str, dict, or list"
                )

            if method == "drop":
                logger.debug(f"Column '{col_name}' marked to be dropped.")
                continue

            if method not in dispatch_map:
                raise ValueError(
                    f"Method '{method}' for column '{col_name}' is not a valid anonymization method."
                )

            logger.debug(f"Column '{col_name}': method '{method}' is valid.")

    logger.success("Configuration validation passed.")


def validate(config: dict) -> None:
    """
    Public API: validate the configuration using the built-in dispatch map.
    """
    dispatch_map = build_dispatch_map()
    return validate_config(config, dispatch_map)
