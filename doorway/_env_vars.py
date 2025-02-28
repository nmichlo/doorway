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

__all__ = (
    "EnvVarHandlerBase",
    "EnvVarHandlerStr",
    "EnvVarHandlerBool",
    "EnvVarHandlerInt",
    # errors
    "EnvVarError",
    "EnvVarValidationError",
    "EnvVarConversionError",
)

import abc
import os
from typing import List, Optional
from typing import Sequence
from typing import Generic
from typing import TypeVar


# ========================================================================= #
# Errors                                                                    #
# ========================================================================= #


class EnvVarError(ValueError):
    pass


class EnvVarValidationError(EnvVarError):
    pass


class EnvVarConversionError(EnvVarError):
    pass


# ========================================================================= #
# Variable Manager                                                          #
# ========================================================================= #


T = TypeVar("T")


class EnvVarHandlerBase(Generic[T], abc.ABC):
    """
    Base class for managing variables that can be set via environment variables.
    """

    def __init__(
        self,
        environ_key: str,
        fallback_value: T,
        *,
        identifier: Optional[str] = None,
    ):
        if identifier is None:
            identifier = environ_key.lower()
        self._identifier = identifier
        self._environ_key = environ_key
        assert str.isidentifier(self._environ_key)
        assert str.isidentifier(self._identifier)
        # default
        self._value_default = None
        # values
        self._value_fallback = fallback_value
        self._validate_value(self._value_fallback, source="fallback_value")

    # OVERRIDEABLE

    @abc.abstractmethod
    def _validate_value(self, value: T, source: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _normalize_environ_value(self, value: str) -> T:
        raise NotImplementedError

    # COMMON - PROPS

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def environ_key(self) -> str:
        return self._environ_key

    @property
    def fallback_value(self) -> T:
        return self._value_fallback

    # COMMON - FUNCS

    def set_default_value(self, value: Optional[T] = None) -> None:
        # make sure the hash_algo is valid
        if value is not None:
            self._validate_value(value, source="set_default_value")
        # update the default mode
        self._value_default = value

    def del_default_value(self) -> None:
        self._value_default = None

    def get_value(self, override: Optional[T] = None) -> T:
        """
        priority:
          1. manual specification
          2. default mode (set_default_value)
          3. environment variable
          4. fallback mode ("fast")
        """
        if override is not None:
            source, value = ("manual", override)
        elif self._value_default is not None:
            source, value = ("default", self._value_default)
        elif self._environ_key in os.environ:
            source, value = (
                "environment",
                self._normalize_environ_value(os.environ[self._environ_key]),
            )
        else:
            source, value = ("fallback", self._value_fallback)
        # make sure the hash mode is valid
        self._validate_value(value=value, source=source)
        # done
        return value


# ========================================================================= #
# String Variable Manager                                                   #
# ========================================================================= #


class EnvVarHandlerStr(EnvVarHandlerBase[str]):
    def __init__(
        self,
        environ_key: str,
        fallback_value: str,
        *,
        allowed_values: Optional[Sequence[str]] = None,
        identifier: Optional[str] = None,
    ):
        # values
        self._allowed_values = set(allowed_values)
        # checks
        if len(self.allowed_values) <= 0:
            raise ValueError(
                f"allowed_values must not be an empty sequence, got: {repr(self._allowed_values)}"
            )
        if not all(isinstance(v, str) for v in self._allowed_values):
            raise ValueError(
                f"all entries in the allowed_values must be strings, got: {repr(self._allowed_values)}"
            )
        if fallback_value not in self._allowed_values:
            raise ValueError(
                f"the fallback_value: {repr(fallback_value)} is not one of the allowed_values: {repr(self._allowed_values)}"
            )
        # initialize
        super().__init__(
            environ_key=environ_key,
            fallback_value=fallback_value,
            identifier=identifier,
        )

    # CUSTOM

    @property
    def allowed_values(self) -> Optional[List[str]]:
        if self._allowed_values is None:
            return None
        return sorted(self._allowed_values)

    # OVERRIDDEN

    def _validate_value(self, value: str, source: Optional[str] = None) -> None:
        if not isinstance(value, str):
            raise EnvVarValidationError(
                f"invalid {self.identifier}: {repr(value)}, obtained from source: {source}, must be of type {str}, got type: {type(value)}"
            )
        if self._allowed_values is not None:
            if value not in self._allowed_values:
                raise EnvVarValidationError(
                    f"invalid {self.identifier}: {repr(value)}, obtained from source: {source}, must be one of the allowed_values: {self.allowed_values}"
                )

    def _normalize_environ_value(self, value: str) -> str:
        return value


# ========================================================================= #
# Bool Variable Manager                                                     #
# ========================================================================= #


class EnvVarHandlerBool(EnvVarHandlerBase[bool]):
    def __init__(
        self,
        environ_key: str,
        fallback_value: bool,
        *,
        environ_keys_true: Sequence[str] = ("y", "yes", "t", "true", "1"),
        environ_keys_false: Sequence[str] = ("n", "no", "f", "false", "0"),
        environ_to_lower_case: bool = True,
        identifier: Optional[str] = None,
    ):
        # values
        self._environ_keys_true = set(environ_keys_true)
        self._environ_keys_false = set(environ_keys_false)
        self._environ_to_lower_case = environ_to_lower_case
        # checks
        assert self._environ_keys_true and all(
            isinstance(v, str) for v in self._environ_keys_true
        )
        assert self._environ_keys_false and all(
            isinstance(v, str) for v in self._environ_keys_false
        )
        assert isinstance(environ_to_lower_case, bool)
        # init
        super().__init__(
            environ_key=environ_key,
            fallback_value=fallback_value,
            identifier=identifier,
        )

    def _validate_value(self, value: bool, source: str) -> None:
        if not isinstance(value, bool):
            raise EnvVarValidationError(
                f"invalid {self.identifier}: {repr(value)}, obtained from source: {source}, must be of type {bool}, got type: {type(value)}"
            )

    def _normalize_environ_value(self, value: str) -> bool:
        if self._environ_to_lower_case:
            value = value.lower()
        if value in self._environ_keys_true:
            return True
        elif value in self._environ_keys_false:
            return False
        else:
            raise EnvVarConversionError(
                f"cannot normalize environment variable `{self.environ_key}={repr(value)}` into {self.identifier}, must be one of: {sorted(self._environ_keys_true | self._environ_keys_false)}"
            )


# ========================================================================= #
# Int Variable Manager                                                      #
# ========================================================================= #


class EnvVarHandlerInt(EnvVarHandlerBase[int]):
    def __init__(
        self,
        environ_key: str,
        fallback_value: int,
        *,
        identifier: Optional[str] = None,
    ):
        super().__init__(
            environ_key=environ_key,
            fallback_value=fallback_value,
            identifier=identifier,
        )

    def _validate_value(self, value: int, source: str) -> None:
        if not isinstance(value, int):
            raise EnvVarValidationError(
                f"invalid {self.identifier}: {repr(value)}, obtained from source: {source}, must be of type {int}, got type: {type(value)}"
            )

    def _normalize_environ_value(self, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise EnvVarConversionError(
                f"cannot normalize environment variable `{self.environ_key}={repr(value)}` into {self.identifier}, must be an integer"
            )


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
