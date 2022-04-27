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

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Callable
from typing import Tuple
from typing import Union
from urllib.parse import ParseResult
from urllib.parse import urlparse


LOG = logging.getLogger(__name__)


# ========================================================================= #
# URI validation                                                            #
# ========================================================================= #


class UriMalformedException(Exception):
    def __init__(self, parsed: ParseResult, msg: str):
        super().__init__(f'[Malformed URI]: {msg} -- From URI: {parsed.geturl()}')


class UriMalformedFileException(UriMalformedException):
    pass


class UriMalformedUrlException(UriMalformedException):
    pass


def _validate_url(parsed: ParseResult) -> ParseResult:
    if parsed.scheme not in ('http', 'https'):
        raise UriMalformedUrlException(parsed, f'scheme must be "http" or "https"')
    if not parsed.netloc:
        raise UriMalformedUrlException(parsed, f'must contain netloc')  # netloc is a combined version of hostname and port and other vars
    # if not parsed.path:
    #     raise MalformedUriUrlException(parsed, f'must contain path')
    if parsed.params:
        raise UriMalformedUrlException(parsed, f'cannot contain params')
    # if not parsed.query:
    #     raise MalformedUriUrlException(parsed, f'must contain query')
    # if parsed.fragment:
    #     raise MalformedUriUrlException(parsed, f'must contain fragment')
    if parsed.username:
        raise UriMalformedUrlException(parsed, f'cannot contain username')
    if parsed.password:
        raise UriMalformedUrlException(parsed, f'cannot contain password')
    if not parsed.hostname:
        raise UriMalformedUrlException(parsed, f'must contain hostname')
    # if not parsed.port:
    #     raise MalformedUriUrlException(parsed, f'must contain port')
    return parsed


def _validate_file(parsed: ParseResult) -> ParseResult:
    if parsed.scheme != 'file':
        raise UriMalformedFileException(parsed, f'scheme must be "file"')
    if parsed.netloc:
        raise UriMalformedFileException(parsed, f'cannot contain netloc')
    if not parsed.path:
        raise UriMalformedFileException(parsed, f'must contain path')
    if parsed.params:
        raise UriMalformedFileException(parsed, f'cannot contain params')
    if parsed.query:
        raise UriMalformedFileException(parsed, f'cannot contain query')
    if parsed.fragment:
        raise UriMalformedFileException(parsed, f'cannot contain fragment')
    if parsed.username:
        raise UriMalformedFileException(parsed, f'cannot contain username')
    if parsed.password:
        raise UriMalformedFileException(parsed, f'cannot contain password')
    if parsed.hostname:
        raise UriMalformedFileException(parsed, f'cannot contain hostname')
    if parsed.port:
        raise UriMalformedFileException(parsed, f'cannot contain port')
    return parsed


_SCHEME_VALIDATORS = {
    'http': _validate_url,
    'https': _validate_url,
    'file': _validate_file,
}


def _uri_get_validator(parsed: ParseResult) -> Callable[[ParseResult], ParseResult]:
    validator = _SCHEME_VALIDATORS.get(parsed.scheme, None)
    if validator is None:
        raise KeyError(f'invalid uri scheme: {repr(parsed.scheme)}, must be one of: {sorted(_SCHEME_VALIDATORS.keys())}, for uri: {repr(parsed.geturl())}')
    return validator


def uri_validate(uri: Union[str, Path]) -> ParseResult:
    parsed = urlparse(uri, scheme='file')  # default scheme if none is given
    # get the validator & validate the uri
    validator = _uri_get_validator(parsed)
    validated = validator(parsed)
    return validated


def uri_is_valid(uri: Union[str, Path]) -> bool:
    try:
        uri_validate(uri)
    except UriMalformedException:
        return False
    return True


# ========================================================================= #
# URI parsing                                                               #
# ========================================================================= #


# including `str` as a parent class means we can write: `assert UriType.URL == 'URL'`
# without `str` as a parent class, this does not evaluate to `True`.
# -- HOWEVER: we do not want this feature! It will just cause confusion
#             and can't be type checked!
class UriType(Enum):
    """
    Types of URIs supported by the `parse_uri_and_type` function.
    """
    FILE = 'FILE'
    URL = 'URL'


_SCHEME_TO_TYPE = {
    'http': UriType.URL,
    'https': UriType.URL,
    'file': UriType.FILE,
}


def _uri_get_type(validated: ParseResult) -> UriType:
    result_type = _SCHEME_TO_TYPE.get(validated.scheme, None)
    if result_type is None:
        raise KeyError(f'invalid uri scheme: {repr(validated.scheme)}, must be one of: {sorted(_SCHEME_TO_TYPE.keys())}, for uri: {repr(validated.geturl())}')
    return result_type


def _uri_norm_from_type(validated: ParseResult, uri_type: UriType) -> str:
    if uri_type == UriType.FILE:
        uri_norm = validated.path
    elif uri_type == UriType.URL:
        uri_norm = validated.geturl()
    else:
        raise RuntimeError('This should never happen!')
    return uri_norm


def uri_normalize(uri: Union[str, Path], return_parsed: bool = False) -> Union[Tuple[str, UriType], Tuple[str, UriType, ParseResult]]:
    validated = uri_validate(uri)
    # get the uri type and get the norm string based on that type
    uri_type = _uri_get_type(validated)
    uri_norm = _uri_norm_from_type(validated, uri_type)
    # return the results
    if return_parsed:
        return uri_norm, uri_type, validated
    return uri_norm, uri_type


# ========================================================================= #
# uri helper                                                                #
# ========================================================================= #


def basename_from_uri(uri: str) -> str:
    """
    Get the basename from the path component of a URI
    """
    parsed = urlparse(uri)
    return os.path.basename(parsed.path)


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'UriMalformedException',
    'UriMalformedFileException',
    'UriMalformedUrlException',
    'uri_validate',
    'uri_is_valid',
    'UriType',
    'uri_normalize',
    'basename_from_uri',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
