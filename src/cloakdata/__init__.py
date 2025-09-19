from .engine import AnonymizerEngine
from .methods import AnonymizationMethods
from .registry import (
    get_all_methods,
    get_registered_methods,
    register_method,
    unregister_method,
)

anonymize = AnonymizerEngine.anonymize

__all__ = [
    "anonymize",
    "get_all_methods",
    "get_registered_methods",
    "register_method",
    "unregister_method",
    "AnonymizerEngine",
    "AnonymizationMethods",
]
