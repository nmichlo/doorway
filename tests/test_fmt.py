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
import pytest

from doorway._fmt import fmt_bytes_to_human
from doorway._ctx import ctx_temp_environ


# ========================================================================= #
# TEST UTILS                                                                #
# ========================================================================= #


def test_fmt_bytes_to_human():
    with ctx_temp_environ(DOORWAY_ENABLE_COLORS="false"):
        assert fmt_bytes_to_human(1000**1, base=1024, align=True) == "1000.000 B  "
        assert fmt_bytes_to_human(1000**2, base=1024, align=True) == " 976.562 KiB"
        assert fmt_bytes_to_human(1000**3, base=1024, align=True) == " 953.674 MiB"
        assert fmt_bytes_to_human(1000**4, base=1024, align=True) == " 931.323 GiB"
        assert fmt_bytes_to_human(1000**5, base=1024, align=True) == " 909.495 TiB"

        assert fmt_bytes_to_human(1024**1, base=1024, align=True) == "   1.000 KiB"
        assert fmt_bytes_to_human(1024**2, base=1024, align=True) == "   1.000 MiB"
        assert fmt_bytes_to_human(1024**3, base=1024, align=True) == "   1.000 GiB"
        assert fmt_bytes_to_human(1024**4, base=1024, align=True) == "   1.000 TiB"
        assert fmt_bytes_to_human(1024**5, base=1024, align=True) == "   1.000 PiB"

        assert fmt_bytes_to_human(3070**1, base=1024, align=True) == "   2.998 KiB"
        assert fmt_bytes_to_human(3070**2, base=1024, align=True) == "   8.988 MiB"
        assert fmt_bytes_to_human(3070**3, base=1024, align=True) == "  26.947 GiB"
        assert fmt_bytes_to_human(3070**4, base=1024, align=True) == "  80.789 TiB"
        assert fmt_bytes_to_human(3070**5, base=1024, align=True) == " 242.210 PiB"

        assert fmt_bytes_to_human(1000**1, base=1024) == "1000.000 B"
        assert fmt_bytes_to_human(1000**2, base=1024) == "976.562 KiB"
        assert fmt_bytes_to_human(1000**3, base=1024) == "953.674 MiB"
        assert fmt_bytes_to_human(1000**4, base=1024) == "931.323 GiB"
        assert fmt_bytes_to_human(1000**5, base=1024) == "909.495 TiB"

        assert fmt_bytes_to_human(1024**1, base=1024) == "1.000 KiB"
        assert fmt_bytes_to_human(1024**2, base=1024) == "1.000 MiB"
        assert fmt_bytes_to_human(1024**3, base=1024) == "1.000 GiB"
        assert fmt_bytes_to_human(1024**4, base=1024) == "1.000 TiB"
        assert fmt_bytes_to_human(1024**5, base=1024) == "1.000 PiB"

        assert fmt_bytes_to_human(3070**1, base=1024) == "2.998 KiB"
        assert fmt_bytes_to_human(3070**2, base=1024) == "8.988 MiB"
        assert fmt_bytes_to_human(3070**3, base=1024) == "26.947 GiB"
        assert fmt_bytes_to_human(3070**4, base=1024) == "80.789 TiB"
        assert fmt_bytes_to_human(3070**5, base=1024) == "242.210 PiB"

        assert fmt_bytes_to_human(999, base=1024) == "999.000 B"
        assert fmt_bytes_to_human(1000, base=1024) == "1000.000 B"
        assert fmt_bytes_to_human(1001, base=1024) == "1001.000 B"
        assert fmt_bytes_to_human(1999, base=1024) == "1.952 KiB"
        assert fmt_bytes_to_human(2000, base=1024) == "1.953 KiB"
        assert fmt_bytes_to_human(2001, base=1024) == "1.954 KiB"

        assert fmt_bytes_to_human(1023, base=1024) == "1023.000 B"
        assert fmt_bytes_to_human(1024, base=1024) == "1.000 KiB"
        assert fmt_bytes_to_human(1025, base=1024) == "1.001 KiB"
        assert fmt_bytes_to_human(2047, base=1024) == "1.999 KiB"
        assert fmt_bytes_to_human(2048, base=1024) == "2.000 KiB"
        assert fmt_bytes_to_human(2049, base=1024) == "2.001 KiB"

        assert fmt_bytes_to_human(999, base=1000) == "999.000 B"
        assert fmt_bytes_to_human(1000, base=1000) == "1.000 KB"
        assert fmt_bytes_to_human(1001, base=1000) == "1.001 KB"
        assert fmt_bytes_to_human(1999, base=1000) == "1.999 KB"
        assert fmt_bytes_to_human(2000, base=1000) == "2.000 KB"
        assert fmt_bytes_to_human(2001, base=1000) == "2.001 KB"

        assert fmt_bytes_to_human(1023, base=1000) == "1.023 KB"
        assert fmt_bytes_to_human(1024, base=1000) == "1.024 KB"
        assert fmt_bytes_to_human(1025, base=1000) == "1.025 KB"
        assert fmt_bytes_to_human(2047, base=1000) == "2.047 KB"
        assert fmt_bytes_to_human(2048, base=1000) == "2.048 KB"
        assert fmt_bytes_to_human(2049, base=1000) == "2.049 KB"

        # check out of valid range of units
        assert fmt_bytes_to_human(1025**10, base=1024) == "1058861.117 YiB"
        assert fmt_bytes_to_human(1025**10, base=1000) == "1280084.544 YB"

        with pytest.raises(
            ValueError, match="invalid size in bytes, cannot be negative: -1337"
        ):
            fmt_bytes_to_human(-1337, base=1000)

        # check rounding with +1 or -1 values

        assert fmt_bytes_to_human(1024**2 - 1, base=1024) == "1023.999 KiB"
        assert fmt_bytes_to_human(1024**2 + 0, base=1024) == "1.000 MiB"
        assert fmt_bytes_to_human(1024**2 + 1, base=1024) == "1.000 MiB"

        assert (
            fmt_bytes_to_human(1024**3 - 1, base=1024, round_unit=False)
            == "1024.000 MiB"
        )
        assert fmt_bytes_to_human(1024**3 - 1, base=1024) == "1.000 GiB"
        assert fmt_bytes_to_human(1024**3 + 0, base=1024) == "1.000 GiB"
        assert fmt_bytes_to_human(1024**3 + 1, base=1024) == "1.000 GiB"

        assert fmt_bytes_to_human(1000**3 - 1, base=1024) == "953.674 MiB"
        assert fmt_bytes_to_human(1000**3 + 0, base=1024) == "953.674 MiB"
        assert fmt_bytes_to_human(1000**3 + 1, base=1024) == "953.674 MiB"

        assert fmt_bytes_to_human(1024**3 - 1, base=1000) == "1.074 GB"
        assert fmt_bytes_to_human(1024**3 + 0, base=1000) == "1.074 GB"
        assert fmt_bytes_to_human(1024**3 + 1, base=1000) == "1.074 GB"

        assert (
            fmt_bytes_to_human(1000**3 - 1, base=1000, round_unit=False)
            == "1000.000 MB"
        )
        assert fmt_bytes_to_human(1000**3 - 1, base=1000) == "1.000 GB"
        assert fmt_bytes_to_human(1000**3 + 0, base=1000) == "1.000 GB"
        assert fmt_bytes_to_human(1000**3 + 1, base=1000) == "1.000 GB"

        # check rounding styles

        assert (
            fmt_bytes_to_human(1024**3 - 1, base=1024, round_unit=True) == "1.000 GiB"
        )
        assert (
            fmt_bytes_to_human(1024**3 - 1, base=1024, round_unit=False)
            == "1024.000 MiB"
        )
        assert (
            fmt_bytes_to_human(1024**3 - 524, base=1024, round_unit=True) == "1.000 GiB"
        )
        assert (
            fmt_bytes_to_human(1024**3 - 524, base=1024, round_unit=False)
            == "1024.000 MiB"
        )
        assert (
            fmt_bytes_to_human(1024**3 - 525, base=1024, round_unit=True)
            == "1023.999 MiB"
        )
        assert (
            fmt_bytes_to_human(1024**3 - 525, base=1024, round_unit=False)
            == "1023.999 MiB"
        )

        assert fmt_bytes_to_human(1000**3 - 1, base=1000, round_unit=True) == "1.000 GB"
        assert (
            fmt_bytes_to_human(1000**3 - 1, base=1000, round_unit=False)
            == "1000.000 MB"
        )
        assert (
            fmt_bytes_to_human(1000**3 - 500, base=1000, round_unit=True) == "1.000 GB"
        )
        assert (
            fmt_bytes_to_human(1000**3 - 500, base=1000, round_unit=False)
            == "1000.000 MB"
        )
        assert (
            fmt_bytes_to_human(1000**3 - 501, base=1000, round_unit=True)
            == "999.999 MB"
        )
        assert (
            fmt_bytes_to_human(1000**3 - 501, base=1000, round_unit=False)
            == "999.999 MB"
        )

        # check default values
        assert fmt_bytes_to_human(1000**4, base=1024) == fmt_bytes_to_human(1000**4)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
