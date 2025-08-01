from loguru import logger

def validate_config(config: dict, dispatch_map: dict) -> None:
    """
    Validates the anonymization configuration.

    Parameters:
        config (dict): The loaded configuration dictionary.
        dispatch_map (dict): Dictionary of available anonymization methods.

    Raises:
        ValueError: If any method is invalid or the structure is inconsistent.
    """
    logger.info("🔍 Validating anonymization config...")

    if "columns" not in config:
        raise ValueError("❌ Config is missing required 'columns' section.")

    for col_name, rule in config["columns"].items():
        rules = [rule] if isinstance(rule, (str, dict)) else rule

        for r in rules:
            if isinstance(r, str):
                method = r
            elif isinstance(r, dict):
                method = r.get("method")
            else:
                raise ValueError(f"❌ Invalid rule format for column '{col_name}': must be str, dict, or list")

            if method == "drop":
                logger.debug(f"🗑️ Column '{col_name}' marked to be dropped.")
                continue

            if method not in dispatch_map:
                raise ValueError(f"❌ Method '{method}' for column '{col_name}' is not a valid anonymization method.")

            logger.debug(f"✅ Column '{col_name}': method '{method}' is valid.")

    logger.success("✅ Configuration validation passed.")
