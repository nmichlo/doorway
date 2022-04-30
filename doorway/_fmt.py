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


# ========================================================================= #
# Ansi Colors                                                               #
# ========================================================================= #


RST = '\033[0m'

# dark colors
GRY = '\033[90m'
lRED = '\033[91m'
lGRN = '\033[92m'
lYLW = '\033[93m'
lBLU = '\033[94m'
lMGT = '\033[95m'
lCYN = '\033[96m'
WHT = '\033[97m'

# light colors
BLK = '\033[30m'
RED = '\033[31m'
GRN = '\033[32m'
YLW = '\033[33m'
BLU = '\033[34m'
MGT = '\033[35m'
CYN = '\033[36m'
lGRY = '\033[37m'


# ========================================================================= #
# Byte Formatting                                                           #
# ========================================================================= #


_BYTES_COLR = (WHT, lGRN, lYLW, lRED, lRED, lRED, lRED, lRED, lRED)
_BYTES_NAME = {
    1024: ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"),
    1000: ("B", "KB",  "MB",  "GB",  "TB",  "PB",  "EB",  "ZB",  "YB"),
}


def bytes_to_human(size_bytes: int, decimals: int = 3, color: bool = True, mul: int = 1024) -> str:
    if size_bytes == 0:
        return "0B"
    if mul not in _BYTES_NAME:
        raise ValueError(f'invalid bytes multiplier: {repr(mul)} must be one of: {list(_BYTES_NAME.keys())}')
    # round correctly
    i = int(math.floor(math.log(size_bytes, mul)))
    s = round(size_bytes / math.pow(mul, i), decimals)
    # generate string
    name = f'{_BYTES_COLR[i]}{_BYTES_NAME[mul][i]}{RST}' if color else f'{_BYTES_NAME[mul][i]}'
    # format string
    return f"{s:{4+decimals}.{decimals}f} {name}"


# ========================================================================= #
# Byte Formatting                                                           #
# ========================================================================= #
