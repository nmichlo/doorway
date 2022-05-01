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
    identifier='color_enabled',
    environ_key='DOORWAY_COLOR_ENABLED',
    fallback_value=True,
)


def color_enabled_set_default(color_enabled: Optional[bool]) -> NoReturn:
    return _VAR_HANDLER_USE_COLORS.set_default_value(value=color_enabled)


def color_enabled_get(color_enabled: Optional[bool] = None) -> bool:
    return _VAR_HANDLER_USE_COLORS.get_value(override=color_enabled)


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


def fmt_bytes_to_human(size_bytes: int, decimals: int = 3, color_enabled: Optional[bool] = None, base: int = 1000, old=True) -> str:
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
    if color_enabled:
        unit = f'{_BYTES_UNIT_COLORS[i]}{unit}{c.RST}'
    # format string
    lpad = _BYTES_BASE_PADDING[base]
    return f"{size_div:>{lpad+decimals}.{decimals}f} {unit}"


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'color_enabled_set_default',
    'color_enabled_get',
    'fmt_bytes_to_human',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
