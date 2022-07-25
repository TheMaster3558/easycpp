import inspect
import re
from typing import TYPE_CHECKING, Any, Union

from .cpp import _CPPModule

if TYPE_CHECKING:
    from types import ModuleType


__all__ = 'generate_stubs',


_FILE_SUFFIX_REGEX = re.compile(r'\.c(pp)?')


def generate_stubs(module: Union["_CPPModule", "ModuleType"]):
    if not isinstance(module, _CPPModule):
        raise TypeError('Expected C++ module from create_cpp_module')

    path = _FILE_SUFFIX_REGEX.sub('.pyi', module.__path__)

    with open(path, 'w') as file:
        ...
