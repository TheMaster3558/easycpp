import inspect
import re
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from .cpp import _CPPModule
    from types import ModuleType


__all__ = 'generate_stubs',


_FILE_SUFFIX_REGEX = re.compile(r'\.c(pp)?')


def generate_stubs(module: Union["_CPPModule", "ModuleType"]):
    path = _FILE_SUFFIX_REGEX.sub('.pyi', module.__path__)

    with open(path, 'w') as file:
        ...
