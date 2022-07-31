import re
import subprocess
from typing import Any, Dict, List, Match, Optional, overload

try:
    import black
except ImportError:
    HAS_BLACK = False
else:
    HAS_BLACK = True


__all__ = 'generate_stubs',


_FILE_SUFFIX_REGEX = re.compile(r'\.c(pp)?')
_FUNCTION_REGEX = re.compile(r'([\w\d_]+)\s+([\w\d_]+)(\([\w\d*\s\[\],]+\))')
_POINTER_OR_ADDRESS = re.compile(r'[*&]')
_GET_CLASSES_REGEX = re.compile(r'class[\s\n\t]*([\w\d_]+)[\s\n\t]*\{[.\n]*')
_CLASS_REGEX = re.compile(r'class[\s\n\t]*([\w\d_]+)')
_VAR_REGEX = re.compile(r'([\w\d_]+)\s+[*&]*([\w\d_]+)\s*=?\s*[\w\d_]*;')
_ARRAY_REGEX = re.compile(r'([\w\d_]+)\s+[*&]*([\w\d_]+)[\s\t\n]*\[[\s\t]*.*[\s\t]*]\s*=?[\s*{}\w\d_,]+;')


_sentinel: Any = object()


_CTYPES_CONVERSIONS: Dict[str, Optional[type]] = {
    'void': None,
    'bool': bool,
    'char': str,
    'wchar_t': str,
    'short': int,
    'int': int,
    'long': int,
    '__int64': int,
    'size_t': int,
    'ssize_t': int,
    'float': float,
    'double': float
}


_BASE_STRING = '''import abc
import typing

T = typing.TypeVar('T')


class _MutableCollection(typing.Collection[T], abc.ABC):  # this is made to type arrays
    def __getitem__(self, name: str) -> T: ...
    def __setitem__(self, index: int, value: T) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    
# typing for C++ below

'''


@overload
def generate_stubs(path: str) -> None: ...


@overload
def generate_stubs(path: str, format_command: str) -> subprocess.CompletedProcess: ...


def generate_stubs(path: str, format_command: Optional[str] = None) -> Optional[subprocess.CompletedProcess]:
    """
    Generate stub files (``.pyi``) for a C++ file.

    Parameters
    -----------
    path: :class:`str`
        The path to the file.
    format_command: Optional[:class:`str`]
        The format command to run on the file. The command should contain ``{name}`` where the name of the file goes.
        Example: `black {name}`. Defaults to `black {name}` if black is installed. It will be run with ``stdout``
        and ``stderr`` set to ``None``. Use the return type for any output.

    Returns
    -------
    Optional[:class:`subprocess.CompletedProcess`]


    Example of Stub File

    .. code:: py

        import typing

        T = typing.TypeVar('T')


        class _MutableCollection(typing.Collection[T]):  # this is made to type arrays
            def __getitem__(self, name: str) -> T: ...
            def __setitem__(self, index: int, value: T) -> None: ...
            def __delitem__(self, index: int) -> None: ...

        # typing for C++ below

        class Human:
            ...
            name: str
        def hello(human: Human) -> None: ...
                """

    stubs_path = _FILE_SUFFIX_REGEX.sub('.pyi', path)

    with open(path, 'r') as file:
        code = file.read()

    stubs_string = _BASE_STRING
    current_level = 0
    brackets = [0, 0]

    classes = [name for name in _GET_CLASSES_REGEX.findall(code)]
    last_match = ''

    for line in code.split('\n'):
        function_match = _FUNCTION_REGEX.search(line)
        class_match = _CLASS_REGEX.search(line)
        var_match = _VAR_REGEX.search(line)
        array_match = _ARRAY_REGEX.search(line)

        if '{' in line:
            brackets[0] += 1
        if '}' in line:
            brackets[1] += 1

        if class_match:
            stubs_string += ' ' * current_level + f'class {class_match.group(1)}:\n'\
                            + ' ' * (current_level + 4) + '...\n'
            last_match = 'class'

        if function_match:
            stubs_string += _get_function_annotations(function_match, classes, current_level)
            last_match = 'function'

        if var_match and var_match.group(1) != 'return' and (brackets[0] == brackets[1] or last_match != 'function'):
            var_type = _get_name(var_match.group(1), classes)
            stubs_string += ' ' * current_level + f'{var_match.group(2)}: {var_type}\n'
            last_match = 'var'

        if array_match:
            array_type = _get_name(array_match.group(1), classes)
            array_name = array_match.group(2)
            stubs_string += ' ' * current_level + f'{array_name}: _MutableCollection[{array_type}]\n'
            last_match = 'array'

        if '{' in line and not function_match:
            current_level += 4
        if '}' in line and current_level >= 4 and not function_match:
            current_level -= 4

    with open(stubs_path, 'w') as file:
        file.write(stubs_string)

    if format_command is None and HAS_BLACK:
        format_command = 'black {name}'

    if format_command is not None:
        try:
            format_command = format_command.format(name=stubs_path)
        except KeyError:
            pass
        else:
            return subprocess.run(format_command.split(' '), stdout=None, stderr=None,  capture_output=True)


def _get_function_annotations(function_match: Match[str], classes: List[str], current_level: int) -> str:
    name = function_match.group(2)
    signature = ' ' * current_level + f'def {name}('
    parameters = function_match.group(3).replace('(', '').replace(')', '').split(',')

    for parameter in parameters:
        parameter = parameter.strip().replace('  ', ' ')

        parameter_type_string, parameter_name = parameter.split(' ')
        parameter_type_string = _POINTER_OR_ADDRESS.sub('', parameter_type_string)
        parameter_type = _get_name(parameter_type_string, classes)

        parameter_name = _POINTER_OR_ADDRESS.sub('', parameter_name)

        signature += f'{parameter_name}: {parameter_type},'

    return_type_string = function_match.group(1).lstrip('*').replace('unsigned ', '').replace('long ', '')
    return_type = _get_name(return_type_string, classes)

    signature += ') -> '
    signature += return_type
    signature += ': ...\n\n'

    return signature


def _get_name(string: str, classes: List[str]) -> str:
    type_ = _CTYPES_CONVERSIONS.get(string, _sentinel)

    if type_ is _sentinel:
        if string in classes:
            type_ = string
        else:
            type_ = 'typing.Any'

    if isinstance(type_, type):
        type_ = type_.__name__
    return str(type_)
