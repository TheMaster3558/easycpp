import cppyy as _cppyy
import sys as _sys
import re as _re

from typing import Any, IO, Iterable, List, Set


__author__ = 'The Master'
__version__ = '0.1.0'
__name__ = 'easycpp'
__license__ = 'MIT'
__copyright__ = 'copyright (c) The Master 2022-present'


__all__ = 'create_cpp_module',


_INCLUDE_REGEX = _re.compile(r'^#include\s*<\w+\.\w+>')
_OUTSIDE_SUB_REGEX = _re.compile(r'[<>]')


def create_cpp_module(name: str, importable: bool = True):
    """
    Easily use C++ in Python with this function.

    Parameters
    -----------
    name: :class:`str`
        The __name of the C++ file.
    importable: :class:`bool`
        Whether this file should be able to be imported. This is done by adding to `sys.modules`.

    Example
    --------
    `human.cpp`

    .. code:: cpp
    
        class Human {
            public:
            char *name;
        };

        void hello(Human *human) {
            std::cout << "Hello " << human->name << "!";
        }
        
    `main.py`

    .. code:: py

        from easycpp import create_cpp_module

        create_cpp_module('human.cpp')

        from human import Human, hello

        human = Human('The Master')
        hello(human)  # Hello The Master!


    .. note::
        It is useful to add stubs so your editor recognizes the file.

        `human.pyi`

        .. code:: py

            class Human:
                name: str

                def __init__(name: str) -> None: ...


            def hello(human: Human) -> None: ...
    """

    before = _get_names()

    with open(name, 'r') as file:
        code = _include_headers(file)
        _cppyy.cppdef(code)

    after = _get_names()
    new_objects = after - before

    module = _CPPModule(str(name).split('.')[0], new_objects)
    if importable:
        module.register()
    return module


def _include_headers(file: IO) -> str:
    code: str = file.read()
    matches: List[str] = _INCLUDE_REGEX.findall(code)

    for match in matches:
        header = _OUTSIDE_SUB_REGEX.sub('', match.strip('#include')).strip()
        _cppyy.include(header)
        code = _INCLUDE_REGEX.sub('', code)

    return code


def _get_names() -> Set[str]:
    from cppyy import gbl
    return set(dir(gbl))


class _CPPModule:
    def __init__(self, name: str, names: Iterable[str]) -> None:
        from cppyy import gbl

        self.__name = name
        self.__names = {n: getattr(gbl, n) for n in names}

    def register(self) -> None:
        _sys.modules[self.__name] = self  # type: ignore

    def __getattr__(self, name: str) -> Any:
        if name in self.__names:
            return self.__names[name]
        return self.__getattribute__(name)

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            raise AttributeError(f'C++ module {self.__name!r} has no attribute {name!r}')
