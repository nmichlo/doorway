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

from doorway.x._uri import UriMalformedException
from doorway.x._uri import EnumUriType
from doorway.x._uri import uri_parse
from doorway.x._uri import uri_validate


# ========================================================================= #
# TEST UTILS                                                                #
# ========================================================================= #


def test_uri_type_enum():
    assert len(EnumUriType) == 4
    assert list(EnumUriType) == [
        EnumUriType.FILE,
        EnumUriType.URL,
        EnumUriType.S3,
        EnumUriType.SSH,
    ]
    # test types
    assert isinstance(EnumUriType.FILE, EnumUriType)
    assert isinstance(EnumUriType.FILE.value, str)
    assert isinstance(EnumUriType.FILE.name, str)
    # make sure the inverse is not true
    assert not isinstance(EnumUriType.FILE, str)
    assert not isinstance(EnumUriType.FILE.value, EnumUriType)
    assert not isinstance(EnumUriType.FILE.name, EnumUriType)
    # test equivalence
    assert EnumUriType.FILE == EnumUriType.FILE
    assert EnumUriType.FILE != EnumUriType.URL
    assert EnumUriType.URL == EnumUriType.URL
    # check enums are not equal to their values
    assert EnumUriType.FILE != EnumUriType.FILE.value
    assert EnumUriType.FILE != EnumUriType.FILE.name
    assert EnumUriType.URL != EnumUriType.URL.value
    assert EnumUriType.URL != EnumUriType.URL.name
    # check names and values are equivalent
    assert EnumUriType.FILE.name == EnumUriType.FILE.value
    assert EnumUriType.URL.name == EnumUriType.URL.value


def test_filename_from_uri():
    # test paths
    uri_validate("basename")
    uri_validate("basename.ext")
    uri_validate("basename.ext/path")
    uri_validate("/basename.ext/path")
    uri_validate("./basename.ext/path")
    uri_validate("/")
    uri_validate("./")
    uri_validate(".")
    with pytest.raises(
        UriMalformedException, match="field 'path' is required, but got value: None"
    ):
        uri_validate("")

    # test basic urls
    uri_validate("http://prefix/basename.ext/suffix")
    uri_validate("http://basename.ext/suffix")
    uri_validate("HTTP://basename.ext/suffix")
    with pytest.raises(
        UriMalformedException, match="field 'host' is required, but got value: None"
    ):
        uri_validate("http:/basename.ext/suffix")
    with pytest.raises(
        UriMalformedException, match="field 'host' is required, but got value: None"
    ):
        uri_validate("http:///basename.ext/suffix")

    # test url ports
    uri_validate("http://localhost:")
    uri_validate("http://localhost:/suffix")
    uri_validate("http://localhost:3000")
    uri_validate("http://localhost:3000/suffix")
    uri_validate("http://192.168.0.1")
    uri_validate("http://192.168.0.1:")
    uri_validate("http://192.168.0.1:3000")
    with pytest.raises(
        UriMalformedException, match="field 'host' is required, but got value: ''"
    ):
        uri_validate("http://:3000")

    # test urls and fragments etc
    uri_validate("http://basename.ext/suffix?query")
    uri_validate("http://basename.ext/suffix#fragment")
    uri_validate("http://basename.ext/suffix?query#fragment")
    uri_validate("http://basename.ext/suffix?query=5&query2=3#fragment")
    uri_validate("http://basename.ext/suffix;params?query=5&query2=3#fragment")
    uri_validate("http://basename.ext/suffix#fragment?query")
    uri_validate("http://basename.ext/suffix#fragment?query")


def test_uri_paths_alt():
    def uri(inp, targ=None):
        targ = inp if (targ is None) else targ
        assert uri_parse(inp).geturl() == targ

    uri(inp="path/uri_kind.ext")
    uri(inp="/path/uri_kind.ext")

    uri(inp="../path/uri_kind.ext")
    uri(inp="..//path/uri_kind.ext", targ="../path/uri_kind.ext")
    uri(inp="..//path//uri_kind.ext", targ="../path/uri_kind.ext")

    uri(inp="../../path//uri_kind.ext", targ="../../path/uri_kind.ext")
    uri(inp="../path/..//uri_kind.ext", targ="../uri_kind.ext")

    uri(inp="file:/path/uri_kind.ext")
    uri(inp="file:/path/uri_kind.ext")
    uri(inp="file:/./path/uri_kind.ext", targ="file:/path/uri_kind.ext")

    uri(inp="./path/uri_kind.ext", targ="path/uri_kind.ext")
    uri(inp="file:path/uri_kind.ext")
    uri(inp="file:./path/uri_kind.ext", targ="file:path/uri_kind.ext")
    uri(inp="file:.//path/uri_kind.ext", targ="file:path/uri_kind.ext")
    uri(inp="file:.//.//path/uri_kind.ext", targ="file:path/uri_kind.ext")

    uri(inp="file://path/uri_kind.ext", targ="file://path/uri_kind.ext")  # ERROR?
    uri(inp="file://path/uri_kind.ext")  # ERROR?
    uri(inp="file:///path/uri_kind.ext", targ="file:/path/uri_kind.ext")  # ERROR?
    uri(inp="file://./path/uri_kind.ext")  # ERROR?
    uri(inp="file:////path/uri_kind.ext", targ="file://path/uri_kind.ext")  # ERROR?
    uri(inp="file:///./path/uri_kind.ext", targ="file:/path/uri_kind.ext")  # ERROR?

    uri(inp="http://google.com/asdf")


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
