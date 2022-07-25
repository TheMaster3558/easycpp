from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cpp import _CPPModule
    from types import ModuleType


__all__ = 'generate_stubs',


def generate_stubs(module: Union["_CPPModule", "ModuleType"]):
    ...

