#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2021 Nathan Juraj Michlo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

import logging
from pathlib import Path
from typing import Union


LOG = logging.getLogger(__name__)


# ========================================================================= #
# Formatting                                                                #
# ========================================================================= #


# TODO: combine all these functions



def modify_file_name(file: Union[str, Path], prefix: str = None, suffix: str = None, sep='.') -> Union[str, Path]:
    # get path components
    path = Path(file)
    assert path.name, f'file name cannot be empty: {repr(path)}, for name: {repr(path.name)}'
    # create new path
    prefix = '' if (not prefix) else f'{prefix}{sep}'
    suffix = '' if (not suffix) else f'{sep}{suffix}'
    new_path = path.parent.joinpath(f'{prefix}{path.name}{suffix}')
    # return path with same format as input
    return str(new_path) if isinstance(file, str) else new_path


def modify_name_keep_ext(file: Union[str, Path], prefix: str = None, suffix: str = None, name_contains_sep: bool = False) -> Union[str, Path]:
    # get path components
    path = Path(file)
    name = path.name
    assert name, f'file name cannot be empty: {repr(path)}, for name: {repr(name)}'
    # handle suffix
    if suffix:
        components = name.rsplit('.', 1) if name_contains_sep else path.name.split('.', 1)
        if len(components) >= 2:
            [name, ext] = components
            name = f'{name}{suffix}.{ext}'
        else:
            [name] = components
            name = f'{name}{suffix}'
    # handle prefix
    if prefix:
        name = f'{prefix}{name}'
    # create new path
    new_path = path.parent.joinpath(name)
    # return path with same format as input
    return str(new_path) if isinstance(file, str) else new_path


def modify_ext(file: Union[str, Path], ext: str, name_contains_sep: bool = True) -> Union[str, Path]:
    assert not ext.startswith('.'), f'please specify the extension without the starting period: {repr(ext)}'
    # get path components
    path = Path(file)
    name = path.name
    assert name, f'file name cannot be empty: {repr(path)}, for name: {repr(name)}'
    # update the path name
    (name, *_) = name.rsplit('.', 1) if name_contains_sep else path.name.split('.', 1)
    name = f'{name}.{ext}'
    new_path = path.parent.joinpath(name)
    # return path with same format as input
    return str(new_path) if isinstance(file, str) else new_path


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
