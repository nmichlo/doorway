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
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import NoReturn
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import Union

from rfc3986 import normalizers
from rfc3986 import ParseResult


LOG = logging.getLogger(__name__)


# ========================================================================= #
# PATCH                                                                     #
# ========================================================================= #


_ORIG_REMOVE_DOT_SEGMENTS = normalizers.remove_dot_segments


@contextmanager
def _rfc3986_patch_context__remove_dot_segments(disabled=False):
    # set new function, this no longer matches: http://tools.ietf.org/html/rfc3986#section-5.2.4
    # -- make sure that '..' and '.' at the start of a path are not removed!
    # -- '' might become '.' which should actually not be allowed!
    if not disabled:
        normalizers.remove_dot_segments = os.path.normpath
    # move into context
    try:
        yield
    # restore original function
    finally:
        normalizers.remove_dot_segments = _ORIG_REMOVE_DOT_SEGMENTS


# ========================================================================= #
# URI validation                                                            #
# ========================================================================= #


class UriMalformedException(Exception):
    def __init__(self, parsed: ParseResult, msg: str):
        super().__init__(f'[Malformed URI]: {msg} -- From URI: {parsed.unsplit()}')


class EnumValMode(Enum):
    OPTIONAL = 'OPTIONAL'
    REQUIRED = 'REQUIRED'
    FORBIDDEN = 'FORBIDDEN'


class UriFieldValidator(object):
    def __init__(
        self,
        mode: EnumValMode = EnumValMode.OPTIONAL,
        validator: Callable[[ParseResult, str, str, Any], ParseResult] = None,
        one_of: Optional[Sequence[Any]] = None,
    ):
        self._mode = mode
        self._validator = validator
        self._one_of = one_of

    def __call__(self, parsed: ParseResult, uri_kind: str, field_name: str, field_value: Any) -> NoReturn:
        # validate based on the mode
        if self._mode == EnumValMode.REQUIRED:
            if not field_value:
                raise UriMalformedException(parsed, f'field {repr(field_name)} is required, but got value: {repr(field_value)}')
        elif self._mode == EnumValMode.FORBIDDEN:
            if field_value:
                raise UriMalformedException(parsed, f'field {repr(field_name)} is forbidden, but got value: {repr(field_value)}')
        elif self._mode != EnumValMode.OPTIONAL:
            raise NotImplementedError('This should never happen!')
        # validate based on required values
        if self._one_of is not None:
            if field_value not in self._one_of:
                raise UriMalformedException(parsed, f'field {repr(field_name)} has value: {repr(field_value)}, but must be one of: {list(self._one_of)}')
        # validate based on the validator function
        if self._validator is not None:
            self._validator(parsed, uri_kind, field_name, field_value)


class UriValidator(object):
    # override these in subclasses
    validate_scheme:   UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_userinfo: UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_host:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_port:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_path:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_query:    UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_fragment: UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)

    def __call__(self, uri: Union[str, Path]) -> ParseResult:
        return self.validate(uri)

    def validate(self, uri: Union[str, Path]) -> ParseResult:
        parsed = uri_parse(uri)
        # validate everything
        self.validate_scheme  (parsed=parsed, uri_kind=self.uri_kind, field_name='scheme',   field_value=parsed.scheme)
        self.validate_userinfo(parsed=parsed, uri_kind=self.uri_kind, field_name='userinfo', field_value=parsed.userinfo)
        self.validate_host    (parsed=parsed, uri_kind=self.uri_kind, field_name='host',     field_value=parsed.host)
        self.validate_port    (parsed=parsed, uri_kind=self.uri_kind, field_name='port',     field_value=parsed.port)
        self.validate_path    (parsed=parsed, uri_kind=self.uri_kind, field_name='path',     field_value=parsed.path)
        self.validate_query   (parsed=parsed, uri_kind=self.uri_kind, field_name='query',    field_value=parsed.query)
        self.validate_fragment(parsed=parsed, uri_kind=self.uri_kind, field_name='fragment', field_value=parsed.fragment)
        # final result
        return parsed

    # override these

    @property
    def uri_kind(self) -> str:
        raise NotImplementedError

    @property
    def uri_type(self) -> 'EnumUriType':
        raise NotImplementedError

    @property
    def allowed_schemes(self) -> Tuple[Optional[str], ...]:
        raise NotImplementedError

    @classmethod
    def extract(cls, validated: ParseResult) -> str:
        raise NotImplementedError


# ========================================================================= #
# URI Types                                                                 #
# ========================================================================= #


# including `str` as a parent class means we can write: `assert UriType.URL == 'URL'`
# without `str` as a parent class, this does not evaluate to `True`.
# -- HOWEVER: we do not want this feature! It will just cause confusion
#             and can't be type checked!
class EnumUriType(Enum):
    """
    Types of URIs supported by the `parse_uri_and_type` function.
    """
    FILE = 'FILE'
    URL = 'URL'
    S3 = 'S3'
    SSH = 'SSH'


class UriValidatorUrl(UriValidator):
    uri_kind = 'url'
    uri_type = EnumUriType.URL
    allowed_schemes = ('http', 'https')

    # override these in subclasses
    validate_scheme:   UriFieldValidator = UriFieldValidator(mode=EnumValMode.REQUIRED, one_of=allowed_schemes)
    validate_userinfo: UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)
    validate_host:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.REQUIRED)
    validate_port:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_path:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_query:    UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)
    validate_fragment: UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL)

    @classmethod
    def extract(cls, validated: ParseResult) -> str:
        return validated.geturl()


class UriValidatorFile(UriValidator):
    uri_kind = 'file'
    uri_type = EnumUriType.FILE
    allowed_schemes = ('file', None)

    # override these in subclasses
    validate_scheme:   UriFieldValidator = UriFieldValidator(mode=EnumValMode.OPTIONAL, one_of=allowed_schemes)
    validate_userinfo: UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)
    validate_host:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)
    validate_port:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)
    validate_path:     UriFieldValidator = UriFieldValidator(mode=EnumValMode.REQUIRED)
    validate_query:    UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)
    validate_fragment: UriFieldValidator = UriFieldValidator(mode=EnumValMode.FORBIDDEN)

    @classmethod
    def extract(cls, validated: ParseResult) -> str:
        return validated.path


# ========================================================================= #
# URI vars                                                                  #
# ========================================================================= #


_SCHEME_VALIDATORS: Dict[Optional[str], UriValidator] = {
    scheme: validate_cls()
    for validate_cls in [UriValidatorUrl, UriValidatorFile]
    for scheme in validate_cls.allowed_schemes
}


# ========================================================================= #
# URI validation                                                            #
# ========================================================================= #


def uri_parse(uri: Union[str, Path, ParseResult], rfc3986_norm: bool = False) -> ParseResult:
    parsed = uri
    # convert to parse result
    # -- assume already normalized if already a ParseResult
    if not isinstance(parsed, ParseResult):
        with _rfc3986_patch_context__remove_dot_segments(disabled=rfc3986_norm):
            parsed: ParseResult = ParseResult.from_string(str(parsed), lazy_normalize=False)
    # done!
    return parsed


def uri_validate(uri: Union[str, Path], return_validator: bool = False) -> Union[ParseResult, Tuple[ParseResult, UriValidator]]:
    parsed = uri_parse(uri)
    # get the validator
    validator = _SCHEME_VALIDATORS.get(parsed.scheme, None)
    if validator is None:
        raise KeyError(f'invalid uri scheme: {repr(parsed.scheme)}, must be one of: {list(_SCHEME_VALIDATORS.keys())}, for uri: {repr(parsed.geturl())}')
    # validate the uri
    validated = validator.validate(parsed)
    # get results
    if return_validator:
        return validated, validator
    return validated


def uri_extract(
    uri: Union[str, Path],
    return_validated: bool = False,
    return_validator: bool = False,
) -> Union[str, Tuple[str, ParseResult], Tuple[str, UriValidator], Tuple[str, ParseResult, UriValidator]]:
    validated, validator = uri_validate(uri, return_validator=True)
    # validate the uri
    uri_norm = validator.extract(validated)
    # return the single result
    if not (return_validator or return_validated):
        return uri_norm
    # return all the results
    results = [uri_norm]
    if return_validated: results.append(validated)
    if return_validator: results.append(validator)
    return tuple(results)


# ========================================================================= #
# URI Class - Errors                                                        #
# ========================================================================= #


T = TypeVar('T')


class UriIsIncorrectTypeError(Exception):
    """
    This error is thrown if the uri is an incorrect type
    """


def only_if(prop: property) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(self: 'Uri', *args, **kwargs):
            if getattr(self, prop.fget.__name__):
                raise UriIsIncorrectTypeError(f'Check if: `{prop.fget.__name__}` is `True` before calling `{func.__name__}`, got uri: {repr(self.uri)}')
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# ========================================================================= #
# URI Class                                                                 #
# ========================================================================= #


class Uri(object):

    def __init__(self, uri: Union[str, Path, ParseResult, 'Uri']):
        # unwrap uri object
        if isinstance(uri, Uri):
            uri = uri._input_uri
            assert not isinstance(uri, Uri)
        # save the input
        self._input_uri: Union[str, Path, ParseResult] = uri
        # get validated uri
        validated, validator = uri_validate(uri, return_validator=True)
        self._validated: ParseResult = validated
        self._validator: UriValidator = validator

    # ~=~=~ URI ~=~=~ #

    @property
    def uri_extract(self) -> str:
        return self._validator.extract(self._validated)

    @property
    def uri_type(self) -> EnumUriType:
        return self._validator.uri_type

    @property
    def uri_parsed(self) -> ParseResult:
        return self._validated

    @property
    def uri_basename(self) -> str:
        return os.path.basename(self._validated.path)

    @property
    def uri(self) -> str:
        return self._validated.geturl()

    def __repr__(self):
        return f'{self.__class__.__name__}(uri={repr(self._input_uri)})'

    def __str__(self):
        return self.uri

    # ~=~=~ FILE ~=~=~ #

    @property
    def is_file(self) -> bool:
        return self.uri_type == EnumUriType.FILE

    @property
    @only_if(is_file)
    def file(self) -> str:
        return self.uri_extract

    @property
    @only_if(is_file)
    def file_abs(self) -> str:
        return os.path.abspath(self.uri_extract)

    @property
    @only_if(is_file)
    def file_is_abs(self) -> bool:
        return os.path.isabs(self.uri_extract)

    # ~=~=~ URL ~=~=~ #

    @property
    def is_url(self) -> bool:
        return self.uri_type == EnumUriType.URL

    @property
    @only_if(is_url)
    def url(self) -> str:
        return self.uri_extract

    @property
    @only_if(is_url)
    def url_is_http(self) -> bool:
        return self.uri_parsed.scheme == 'http'

    @property
    @only_if(is_url)
    def url_is_https(self) -> bool:
        return self.uri_parsed.scheme == 'https'

    # ~=~=~ S3 ~=~=~ #

    @property
    def is_s3(self) -> bool:
        return self.uri_type == EnumUriType.S3

    # TODO ...

    # ~=~=~ SSH ~=~=~ #

    @property
    def is_ssh(self) -> bool:
        return self.uri_type == EnumUriType.SSH

    # TODO ...

    # ~=~=~ COMMON ~=~=~ #

    # def download(self, dst: Union[str, Path, 'Uri']):
    #     raise NotImplementedError
    #
    # def copy(self, dst: Union[str, Path, 'Uri']):
    #     raise NotImplementedError
    #
    # def retrieve(self, dst: Union[str, Path, 'Uri']):
    #     raise NotImplementedError


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    # errors
    'UriMalformedException',
    'UriIsIncorrectTypeError',
    # enums
    'EnumValMode',
    'EnumUriType',
    # validation
    'UriFieldValidator',
    'UriValidator',
    'UriValidatorUrl',
    'UriValidatorFile',
    # functional
    'uri_parse',
    'uri_validate',
    'uri_extract',
    # oop
    'Uri',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
