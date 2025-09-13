import importlib


def test_import_and_public_api():
    mod = importlib.import_module("cloakdata")
    assert hasattr(mod, "anonymize")
    assert callable(mod.anonymize)
    assert hasattr(mod, "validate")
    assert callable(mod.validate)
