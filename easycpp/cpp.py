import cppyy as cppyy
import sys as sys
import re as re
from types import ModuleType
from typing import Any, Iterable, List, Set, TextIO


__all__ = 'create_cpp_module',


_INCLUDE_REGEX = re.compile(r'^#include\s*<\w+\.\w+>')
_OUTSIDE_SUB_REGEX = re.compile(r'[<>]')


def create_cpp_module(path: str, importable: bool = True):
    """
    Easily use C++ in Python with this function.

    Parameters
    -----------
    path: :class:`str`
        The path to the C++ file.
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

    with open(path, 'r') as file:
        code = _include_headers(file)
        cppyy.cppdef(code)

    after = _get_names()
    new_objects = after - before

    module = _CPPModule(str(path).split('.')[0].replace('/', '.'), new_objects, path)
    if importable:
        module.register()
    return module


def _include_headers(file: TextIO) -> str:
    code: str = file.read()
    matches: List[str] = _INCLUDE_REGEX.findall(code)

    for match in matches:
        header = _OUTSIDE_SUB_REGEX.sub('', match.strip('#include')).strip()
        cppyy.include(header)
        code = _INCLUDE_REGEX.sub('', code)

    return code


def _get_names() -> Set[str]:
    from cppyy import gbl
    return set(dir(gbl))


class _CPPModule(ModuleType):
    def __init__(self, name: str, names: Iterable[str], path) -> None:
        from cppyy import gbl

        self._name = name
        self._names = {n: getattr(gbl, n) for n in names}
        super().__init__(name)

        self.__path__: str = path

    def register(self) -> None:
        sys.modules[self._name] = self  # type: ignore

    def __dir__(self) -> Iterable[str]:
        items = list(super().__dir__())
        items.extend(list(self._names))
        return items

    def __getattr__(self, name: str) -> Any:
        if name in self._names:
            return self._names[name]
        return self.__getattribute__(name)

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            raise AttributeError(f'C++ module {self._name!r} has no attribute {name!r}')
