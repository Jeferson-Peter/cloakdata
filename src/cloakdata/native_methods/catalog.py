from __future__ import annotations

from ..types import MethodCallable

NATIVE_METHODS: dict[str, MethodCallable] = {}
NATIVE_FRAME_METHODS: set[str] = set()


def native_method(
    func: MethodCallable | None = None, *, name: str | None = None, requires_frame: bool = False
):
    """
    Register a built-in method in the native methods catalog.
    """

    def decorator(method: MethodCallable) -> MethodCallable:
        method_name = (name or method.__name__).strip()
        if not method_name:
            raise ValueError("native method name cannot be empty")
        if method_name in NATIVE_METHODS:
            raise ValueError(f"native method '{method_name}' already registered")
        NATIVE_METHODS[method_name] = method
        if requires_frame:
            NATIVE_FRAME_METHODS.add(method_name)
        return method

    if func is None:
        return decorator
    return decorator(func)
