from .core import AnonymizationMethods
from .validate import validate

anonymize = AnonymizationMethods.anonymize

__all__ = ["anonymize", "AnonymizationMethods", "validate"]
