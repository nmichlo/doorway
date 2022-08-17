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

from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union


# ========================================================================= #
# Basename formatting                                                       #
# ========================================================================= #


def basename_split_ext(
    basename: str,
    name_contains_sep: bool = True,
) -> Tuple[str, str]:
    # split the name from the basename
    if name_contains_sep:
        components = basename.rsplit('.', 1)
    else:
        components = basename.split('.', 1)
    # handle the case where there is no extension
    if len(components) == 1:
        return components[0], ''
    elif len(components) == 2:
        return components[0], f'.{components[1]}'
    else:
        raise NotImplementedError('this is a bug!')


def basename_modify(
    basename: str,
    ext: Optional[str] = None,
    name_prefix: Optional[str] = None,
    name_suffix: Optional[str] = None,
    basename_prefix: Optional[str] = None,
    basename_suffix: Optional[str] = None,
    name_contains_sep: bool = True,
) -> str:
    # 1. surround the name & replace the extension
    if name_suffix or ext:
        name, dot_ext = basename_split_ext(basename, name_contains_sep=name_contains_sep)
        if ext:
            dot_ext = f'.{ext}'
        if name_suffix:
            name = f'{name}{name_suffix}'
        basename = f'{name}{dot_ext}'
    if name_prefix:
        basename = f'{name_prefix}{basename}'
    # 2. surround the basename
    if basename_suffix:
        basename = f'{basename}{basename_suffix}'
    if basename_prefix:
        basename = f'{basename_prefix}{basename}'
    # done
    return basename


# ========================================================================= #
# Path Formatting                                                           #
# ========================================================================= #


def path_basename_modify(
    file: Union[str, Path],
    ext: Optional[str] = None,
    name_prefix: Optional[str] = None,
    name_suffix: Optional[str] = None,
    basename_prefix: Optional[str] = None,
    basename_suffix: Optional[str] = None,
    name_contains_sep: bool = True,
) -> Union[str, Path]:
    # get path components
    path = Path(file)
    basename = path.name
    if not basename:
        raise ValueError(
            f'file basename cannot be empty, '
            f'got basename: {repr(basename)}, '
            f'from file: {repr(str(file))}'
        )
    # update the basename
    basename = basename_modify(
        basename=basename,
        ext=ext,
        name_prefix=name_prefix,
        name_suffix=name_suffix,
        basename_prefix=basename_prefix,
        basename_suffix=basename_suffix,
        name_contains_sep=name_contains_sep,
    )
    # recombine the path and basename
    path = path.parent.joinpath(basename)
    # return path with same format as input
    return str(path) if isinstance(file, str) else path


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'basename_split_ext',
    'basename_modify',
    'path_basename_modify',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
