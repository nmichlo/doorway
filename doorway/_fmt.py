#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2022 Nathan Juraj Michlo
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

import math
from typing import NoReturn
from typing import Optional

import doorway._colors as c
from doorway._utils import VarHandlerBool


# ========================================================================= #
# Variable Handlers                                                         #
# ========================================================================= #


_VAR_HANDLER_USE_COLORS = VarHandlerBool(
    identifier='colors',
    environ_key='DOORWAY_ENABLE_COLORS',
    fallback_value=True,
)


def fmt_use_colors_set_default(use_colors: Optional[bool]) -> NoReturn:
    return _VAR_HANDLER_USE_COLORS.set_default_value(value=use_colors)


def fmt_use_colors_get(use_colors: Optional[bool] = None) -> bool:
    return _VAR_HANDLER_USE_COLORS.get_value(override=use_colors)


# ========================================================================= #
# Byte Formatting                                                           #
# ========================================================================= #


# the names and colours of the different units
_BYTES_UNIT_COLORS = (c.WHT, c.lGRN, c.lYLW, c.lRED, c.lRED, c.lRED, c.lRED, c.lRED, c.lRED)
_BYTES_UNIT_NAMES = {
    1024: ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"),
    1000: ("B", "KB",  "MB",  "GB",  "TB",  "PB",  "EB",  "ZB",  "YB"),
}

# amount of extra padding to add to the left of the dot
_BYTES_BASE_PADDING = {
    1024: 5,
    1000: 4,
}

_BYTES_UNIT_PADDING = {
    1024: 3,
    1000: 2,
}


def fmt_bytes_to_human(
    size_bytes: int,
    base: int = 1024,
    decimals: int = 3,
    align: bool = False,
    use_colors: Optional[bool] = None,
) -> str:
    # TODO: this does not yet handle values greater than YB or YiB
    # check the unit of measurement
    if base not in _BYTES_UNIT_NAMES:
        raise ValueError(f'invalid bytes base number: {repr(base)} must be one of: {sorted(_BYTES_UNIT_NAMES.keys())}')
    # compute the power
    power = math.log(size_bytes, base) if (size_bytes != 0) else 0
    i = int(power)
    size_div = size_bytes / (base**i)
    # get the unit of measurement
    unit = _BYTES_UNIT_NAMES[base][i]
    if fmt_use_colors_get(use_colors):
        unit = f'{_BYTES_UNIT_COLORS[i]}{unit}{c.RST}'
    # format string
    if align:
        lpad = _BYTES_BASE_PADDING[base]
        rpad = _BYTES_UNIT_PADDING[base]
        return f"{size_div:>{lpad+decimals}.{decimals}f} {unit:<{rpad}s}"
    else:
        return f"{size_div:.{decimals}f} {unit}"


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'fmt_use_colors_set_default',
    'fmt_use_colors_get',
    'fmt_bytes_to_human',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
