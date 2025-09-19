from __future__ import annotations

from .methods import AnonymizationMethods
from .types import MethodCallable
from .validators import validate_signature_only

_CUSTOM_METHODS: dict[str, MethodCallable] = {}


def register_method(func: MethodCallable, name: str | None = None) -> str:
    """
    Registra um método customizado (valida assinatura).
    - NÃO permite sobrescrever método nativo.
    - NÃO sobrescreve custom existente (evita colisão).
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
    Retorna apenas os métodos nativos (estáticos) da class `AnonymizationMethods`.
    """
    import inspect

    exclude = {
        "apply_conditioned_expr",
        "anonymize",
        "build_dispatch_map",
        "build_native_dispatch_map",
    }
    dispatch: dict[str, MethodCallable] = {}
    for name, func in inspect.getmembers(AnonymizationMethods, predicate=inspect.isfunction):
        if name.startswith("_") or name in exclude:
            continue
        dispatch[name] = func
    return dispatch


def build_dispatch_map() -> dict[str, MethodCallable]:
    """
    Mapa final: nativos + custom. (Custom NUNCA sobrescrevem nativos.)
    """
    dispatch = build_native_dispatch_map()
    for k, v in _CUSTOM_METHODS.items():
        if k not in dispatch:
            dispatch[k] = v
    return dispatch
