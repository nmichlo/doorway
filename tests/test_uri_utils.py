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

from doorway import UriMalformedFileException
from doorway import UriMalformedUrlException
from doorway import UriType
from doorway import uri_validate


# ========================================================================= #
# TEST UTILS                                                                #
# ========================================================================= #


def test_uri_type_enum():
    assert len(UriType) == 2
    assert list(UriType) == [UriType.FILE, UriType.URL]
    # test types
    assert isinstance(UriType.FILE, UriType)
    assert isinstance(UriType.FILE.value, str)
    assert isinstance(UriType.FILE.name, str)
    # make sure the inverse is not true
    assert not isinstance(UriType.FILE, str)
    assert not isinstance(UriType.FILE.value, UriType)
    assert not isinstance(UriType.FILE.name, UriType)
    # test equivalence
    assert UriType.FILE == UriType.FILE
    assert UriType.FILE != UriType.URL
    assert UriType.URL  == UriType.URL
    # check enums are not equal to their values
    assert UriType.FILE != UriType.FILE.value
    assert UriType.FILE != UriType.FILE.name
    assert UriType.URL != UriType.URL.value
    assert UriType.URL != UriType.URL.name
    # check names and values are equivalent
    assert UriType.FILE.name == UriType.FILE.value
    assert UriType.URL.name == UriType.URL.value


def test_filename_from_uri():
    # test paths
    uri_validate('basename')
    uri_validate('basename.ext')
    uri_validate('basename.ext/path')
    uri_validate('/basename.ext/path')
    uri_validate('./basename.ext/path')
    uri_validate('/')
    uri_validate('.')
    with pytest.raises(UriMalformedFileException, match='must contain path'): uri_validate('')

    # test basic urls
    uri_validate('http://prefix/basename.ext/suffix')
    uri_validate('http://basename.ext/suffix')
    uri_validate('HTTP://basename.ext/suffix')
    with pytest.raises(UriMalformedUrlException, match='must contain netloc'): uri_validate('http:/basename.ext/suffix')
    with pytest.raises(UriMalformedUrlException, match='must contain netloc'): uri_validate('http:///basename.ext/suffix')

    # test url ports
    uri_validate('http://localhost:')
    uri_validate('http://localhost:/suffix')
    uri_validate('http://localhost:3000')
    uri_validate('http://localhost:3000/suffix')
    uri_validate('http://192.168.0.1')
    uri_validate('http://192.168.0.1:')
    uri_validate('http://192.168.0.1:3000')
    with pytest.raises(UriMalformedUrlException, match='must contain hostname'): uri_validate('http://:3000')

    # test urls and fragments etc
    uri_validate('http://basename.ext/suffix?query')
    uri_validate('http://basename.ext/suffix#fragment')
    uri_validate('http://basename.ext/suffix?query#fragment')
    uri_validate('http://basename.ext/suffix?query=5&query2=3#fragment')
    with pytest.raises(UriMalformedUrlException, match='cannot contain params'): uri_validate('http://basename.ext/suffix;params?query=5&query2=3#fragment')
    uri_validate('http://basename.ext/suffix#fragment?query')
    uri_validate('http://basename.ext/suffix#fragment?query')


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
