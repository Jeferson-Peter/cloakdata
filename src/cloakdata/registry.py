from __future__ import annotations

from threading import Lock

from .native_methods import NATIVE_METHODS
from .types import MethodCallable
from .validators import validate_signature_only

_CUSTOM_METHODS: dict[str, MethodCallable] = {}
_REGISTRY_LOCK = Lock()


def register_method(func: MethodCallable, name: str | None = None) -> str:
    """
    Register a custom method after validating its signature.
    """
    if not callable(func):
        raise TypeError("func must be callable")

    validate_signature_only(func)
    method_name = (name or func.__name__).strip()
    if not method_name:
        raise ValueError("name cannot be empty")

    if method_name == "drop" or method_name in NATIVE_METHODS:
        raise ValueError(f"Cannot override native method '{method_name}'. Choose another name.")

    with _REGISTRY_LOCK:
        if method_name in _CUSTOM_METHODS:
            raise ValueError(f"Custom method '{method_name}' already exists. Use another name.")
        _CUSTOM_METHODS[method_name] = func
    return method_name


def unregister_method(name: str) -> None:
    with _REGISTRY_LOCK:
        _CUSTOM_METHODS.pop(name, None)


def get_registered_methods() -> tuple[str, ...]:
    with _REGISTRY_LOCK:
        return tuple(sorted(_CUSTOM_METHODS))


def get_all_methods() -> tuple[str, ...]:
    return tuple(sorted(build_dispatch_map()))


def build_native_dispatch_map() -> dict[str, MethodCallable]:
    """
    Return the explicitly registered native methods.
    """
    return dict(NATIVE_METHODS)


def build_dispatch_map() -> dict[str, MethodCallable]:
    """
    Final map: native + custom. Custom methods never override native ones.
    """
    with _REGISTRY_LOCK:
        return _CUSTOM_METHODS | NATIVE_METHODS
