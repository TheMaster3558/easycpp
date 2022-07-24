import cppyy as _cppyy
import sys as _sys
import re as _re


__author__ = 'The Master'
__name__ = 'easycpp'
__license__ = 'MIT'
__copyright__ = 'copyright (c) The Master 2022-present'


__all__ = 'create_cpp_module',


_INCLUDE_REGEX = _re.compile(r'^#include\s*<\w+\.\w+>')
_OUTSIDE_SUB_REGEX = _re.compile(r'[<>]')


def create_cpp_module(name, importable=True):
    """
    Easily use C++ in Python with this function.

    Parameters
    ----------
    name: :class:`str`
        The name of the C++ file.
    importable: :class:bool`
        Whether this file should be able to be imported. This is done by adding to `sys.modules`.

    Example
    -------
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
        easy_cpp_module('human.cpp')

        from human import Human, hello

        human = Human('Kaushal')
        hello(human)  # Hello Kaushal!


    .. note::
        It is useful to add stubs so your editor recognizes the file as importable.

        .. code:: py

            class Human:
                name: str

            def hello(human: Human) -> None: ...
    """

    before = _get_names()

    with open(name, 'r') as file:
        code = _include_headers(file)
        _cppyy.cppdef(code)

    after = _get_names()
    new_objects = after - before

    module = _CPPModule(name.split('.')[0], new_objects)
    if importable:
        module.register()
    return module


def _include_headers(file):
    code = file.read()

    matches = _INCLUDE_REGEX.findall(code)

    for match in matches:
        header = _OUTSIDE_SUB_REGEX.sub('', match.strip('#include')).strip()
        _cppyy.include(header)
        code = _INCLUDE_REGEX.sub('', code)

    return code


def _get_names():
    from cppyy import gbl
    return set(dir(gbl))


class _CPPModule:
    def __init__(self, name, names):
        from cppyy import gbl

        self.name = name
        self.names = {n: getattr(gbl, n) for n in names}

    def register(self):
        _sys.modules[self.name] = self

    def __getattr__(self, name):
        if name in self.names:
            return self.names[name]
        super().__getattr__(name)
