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
from functools import wraps
from pathlib import Path
from typing import Callable
from typing import Tuple
from typing import TypeVar
from typing import Union
from rfc3986 import urlparse
from rfc3986 import ParseResult


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
    if parsed.userinfo:
        raise UriMalformedUrlException(parsed, f'cannot contain userinfo')
    if not parsed.hostname:
        raise UriMalformedUrlException(parsed, f'must contain hostname')
    # if not parsed.port:
    #     raise MalformedUriUrlException(parsed, f'must contain port')
    return parsed


def _validate_file(parsed: ParseResult) -> ParseResult:
    if parsed.scheme not in ('file', None):
        raise UriMalformedFileException(parsed, f'scheme must be "file"')
    if parsed.netloc:
        raise UriMalformedFileException(parsed, f'cannot contain netloc. A file with two forward slashes "file://path" is invalid, must have one "file:/path" or three "file:///path"')
    if not parsed.path:
        raise UriMalformedFileException(parsed, f'must contain path')
    if parsed.params:
        raise UriMalformedFileException(parsed, f'cannot contain params')
    if parsed.query:
        raise UriMalformedFileException(parsed, f'cannot contain query')
    if parsed.fragment:
        raise UriMalformedFileException(parsed, f'cannot contain fragment')
    if parsed.userinfo:
        raise UriMalformedFileException(parsed, f'cannot contain userinfo')
    if parsed.hostname:
        raise UriMalformedFileException(parsed, f'cannot contain hostname')
    if parsed.port:
        raise UriMalformedFileException(parsed, f'cannot contain port')
    # path is correct, but the uri is not!
    # builtin urlparse is buggy when parsing files and does not follow standards!
    #   * urlparse('folder/name.ext').geturl()           -> 'folder/name.ext'           # CORRECT
    #   * urlparse('/folder/name.ext').geturl()          -> '/folder/name.ext'          # CORRECT
    #   * urlparse('file:folder/name.ext').geturl()      -> 'file:///folder/name.ext'   # ERROR -- should be unchanged
    #   * urlparse('file:/folder/name.ext').geturl()     -> 'file:///folder/name.ext'   # CORRECT
    #   * urlparse('file:///folder/name.ext').geturl()   -> 'file:///folder/name.ext'   # CORRECT
    #   * urlparse('./folder/name.ext').geturl()         -> './folder/name.ext'         # CORRECT
    #   * urlparse('file:./folder/name.ext').geturl()    -> 'file:///./folder/name.ext' # OK - BUT NOT A URL
    #   * urlparse('file:/./folder/name.ext').geturl()   -> 'file:///./folder/name.ext' # OK - BUT NOT A URL
    #   * urlparse('file://./folder/name.ext').geturl()  -> 'file://./folder/name.ext'  # INCORRECT
    #   * urlparse('file:///./folder/name.ext').geturl() -> 'file://./folder/name.ext'  # OK - BUT NOT A URL
    # CONCLUSION:
    #   1. only use absolute urls with "file:*"
    #   2. make sure relative urls start with a "./"
    if (parsed.scheme == 'file') and not os.path.abspath(parsed.path):
        raise UriMalformedFileException(parsed, 'path must be absolute if "file:" scheme is used')
    # return result
    return parsed


_SCHEME_VALIDATORS = {
    'http': _validate_url,
    'https': _validate_url,
    'file': _validate_file,
    None:   _validate_file,
}


def _uri_get_validator(parsed: ParseResult) -> Callable[[ParseResult], ParseResult]:
    validator = _SCHEME_VALIDATORS.get(parsed.scheme, None)
    if validator is None:
        raise KeyError(f'invalid uri scheme: {repr(parsed.scheme)}, must be one of: {sorted(_SCHEME_VALIDATORS.keys())}, for uri: {repr(parsed.geturl())}')
    return validator


def uri_validate(uri: Union[str, Path]) -> ParseResult:
    parsed = urlparse(uri)
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
    'http':  UriType.URL,
    'https': UriType.URL,
    'file':  UriType.FILE,
    None:    UriType.FILE,
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


# def basename_from_uri(uri: str) -> str:
#     """
#     Get the basename from the path component of a URI
#     """
#     parsed = urlparse(uri)
#     return os.path.basename(parsed.path)


# ========================================================================= #
# URI Class - Errors                                                        #
# ========================================================================= #


class UriIsIncorrectTypeError(Exception):
    """
    This error is thrown if the uri is an incorrect type
    """


class UriIsNotUrlError(UriIsIncorrectTypeError):
    """
    This error is thrown if the uri is not a url
    """


class UriIsNotFileError(UriIsIncorrectTypeError):
    """
    This error is thrown if the uri is not a url
    """


T = TypeVar('T')


def is_url_only(func: T) -> T:
    @wraps(func)
    def wrapper(self: 'Uri', *args, **kwargs):
        if not self.is_url:
            raise UriIsNotUrlError(f'Check `is_url` first before calling `{func.__name__}`, the uri is not of type: `{UriType.URL}`, instead got: `{self.uri_type}`, for: {repr(self.uri)}')
        return func(self, *args, **kwargs)
    return wrapper


def is_file_only(func: T) -> T:
    @wraps(func)
    def wrapper(self: 'Uri', *args, **kwargs):
        if not self.is_file:
            raise UriIsNotFileError(f'Check `is_file` first before calling `{func.__name__}`, the uri is not of type: `{UriType.FILE}`, instead got: `{self.uri_type}`, for: {repr(self.uri)}')
        return func(self, *args, **kwargs)
    return wrapper


# ========================================================================= #
# URI Class                                                                 #
# ========================================================================= #


class Uri(object):

    def __init__(self, uri: Union[str, Path]):
        self._orig_uri = uri
        uri_norm, uri_type, validated = uri_normalize(uri=uri, return_parsed=True)
        self._uri_norm: str = uri_norm
        self._uri_type: UriType = uri_type
        self._parsed: ParseResult = validated

    # ~=~=~ URI ~=~=~ #

    @property
    def uri_norm(self) -> str:
        return self._uri_norm

    @property
    def uri_type(self) -> UriType:
        return self._uri_type

    @property
    def uri_parsed(self) -> ParseResult:
        return self._parsed

    @property
    def uri_basename(self) -> str:
        return os.path.basename(self._parsed.path)

    @property
    def uri(self) -> str:
        return self._parsed.geturl()

    def __repr__(self):
        return f'{self.__class__.__name__}(uri={repr(self._orig_uri)})'

    def __str__(self):
        return self._orig_uri

    # ~=~=~ FILE ~=~=~ #

    @property
    def is_file(self) -> bool:
        return self._uri_type == UriType.FILE

    @property
    @is_file_only
    def file_is_abs(self) -> bool:
        return os.path.isabs(self.uri_norm)

    @property
    @is_file_only
    def file_is_rel(self) -> bool:
        return not os.path.isabs(self.uri_norm)

    @property
    @is_file_only
    def file(self) -> str:
        return self.uri_norm

    @property
    @is_file_only
    def file_abs(self) -> str:
        return os.path.abspath(self.file)

    @property
    @is_file_only
    def path(self) -> Path:
        return Path(self.uri_norm)

    @property
    @is_file_only
    def path_abs(self) -> Path:
        return Path(self.uri_norm).absolute()

    # ~=~=~ URI ~=~=~ #

    @property
    def is_url(self) -> bool:
        return self._uri_type == UriType.URL

    @property
    @is_url_only
    def url_is_http(self) -> bool:
        return self._parsed.scheme == 'http'

    @property
    @is_url_only
    def url_is_https(self) -> bool:
        return self._parsed.scheme == 'https'

    @property
    @is_url_only
    def url(self) -> str:
        return self.uri_norm


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    # errors
    'UriMalformedException',
    'UriMalformedFileException',
    'UriMalformedUrlException',
    'UriIsIncorrectTypeError',
    'UriIsNotUrlError',
    'UriIsNotFileError',
    # functions
    'uri_validate',
    'uri_is_valid',
    'UriType',
    'uri_normalize',
    # class
    'Uri',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
