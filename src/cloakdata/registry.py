from __future__ import annotations

from .native_methods import NATIVE_METHODS
from .types import MethodCallable
from .validators import validate_signature_only

_CUSTOM_METHODS: dict[str, MethodCallable] = {}


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

    native = build_native_dispatch_map()
    if method_name in native:
        raise ValueError(f"Cannot override native method '{method_name}'. Choose another name.")
    if method_name in _CUSTOM_METHODS:
        raise ValueError(f"Custom method '{method_name}' already exists. Use another name.")

    _CUSTOM_METHODS[method_name] = func
    return method_name


def unregister_method(name: str) -> None:
    _CUSTOM_METHODS.pop(name, None)


def get_registered_methods() -> tuple[str, ...]:
    return tuple(sorted(_CUSTOM_METHODS.keys()))


def get_all_methods() -> tuple[str, ...]:
    all_names = set(build_native_dispatch_map().keys()) | set(_CUSTOM_METHODS.keys())
    return tuple(sorted(all_names))


def build_native_dispatch_map() -> dict[str, MethodCallable]:
    """
    Return the explicitly registered native methods.
    """
    return dict(NATIVE_METHODS)


def build_dispatch_map() -> dict[str, MethodCallable]:
    """
    Final map: native + custom. Custom methods never override native ones.
    """
    dispatch = build_native_dispatch_map()
    for key, value in _CUSTOM_METHODS.items():
        if key not in dispatch:
            dispatch[key] = value
    return dispatch
