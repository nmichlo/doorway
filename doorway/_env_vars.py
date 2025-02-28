#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2025 Nathan Juraj Michlo
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
    "EnvVar",
    # errors
    "EnvVarError",
    "EnvVarValidationError",
    "EnvVarConversionError",
    "EnvVarMissingError",
)

import os
from typing import Callable, Iterable, Optional
from typing import Sequence
from typing import Generic
from typing import TypeVar


# ========================================================================= #
# Types                                                                     #
# ========================================================================= #


T = TypeVar("T")
EnvVarFnConverterHint = Callable[[str], T]
EnvVarFnValidatorHint = Callable[[T], T]


# ========================================================================= #
# Errors                                                                    #
# ========================================================================= #


class EnvVarError(ValueError):
    """Base exception for environment variable errors."""

    pass


class EnvVarMissingError(EnvVarError):
    """Raised when a value is missing."""

    pass


class EnvVarValidationError(EnvVarError):
    """Raised when a value fails validation."""

    pass


class EnvVarConversionError(EnvVarError):
    """Raised when converting an environment variable string fails."""

    pass


# ========================================================================= #
# Variable Manager                                                          #
# ========================================================================= #


class EnvVar(Generic[T]):
    """
    A flexible handler for environment variables of any type.

    priority:
      0. validated force (if set, passed in)
      1. validated override (if set, from constructor)
      2. validated + converted environment variable (if set, from os.environ)
      3. validated default value (if set, passed in)
      4. validated fallback value (if set, from constructor)
      5. raise error if the value is missing (None)
    """

    def __init__(
        self,
        key: str,
        *,
        default: Optional[T] = None,
        converter: Optional[EnvVarFnConverterHint[T]] = None,  # applied to env str
        validator: Optional[EnvVarFnValidatorHint[T]] = None,  # applied to all values
    ):
        self._key = key
        self._env_converter = converter or (lambda x: x)
        self._val_validator = validator or (lambda x: x)
        # do not apply validator until get, more inefficient, but easier to test
        self._persisted_default = default  # value not passed through convert, only val
        self._persisted_override = None  # value not passed through convert, only val

    @property
    def env_key(self) -> str:
        return self._key

    # set or / clear with `None`

    def set_default_value(self, value: Optional[T]) -> None:
        # do not apply validator until get, more inefficient, but easier to test
        self._persisted_default = value

    def set_override_value(self, value: Optional[T]) -> None:
        # do not apply validator until get, more inefficient, but easier to test
        self._persisted_override = value

    # get

    @property
    def value(self) -> T:
        return self.get()

    def __call__(
        self, *, default: Optional[T] = None, override: Optional[T] = None
    ) -> T:
        return self.get(default=default, override=override)

    def get(self, *, default: Optional[T] = None, override: Optional[T] = None) -> T:
        # convert / extract values

        if override is not None:
            source = "call_override"
            result = override
        elif self._persisted_override is not None:
            source = "persisted_override"
            result = self._persisted_override  # already validated in constructor
        elif self._key in os.environ:
            source = "env_value"
            try:
                result = self._env_converter(os.environ[self._key])
            except Exception as e:
                raise EnvVarConversionError(
                    f"error getting {repr(self._key)} from os.environ, conversion failed: {e}"
                ) from e
        elif default is not None:
            source = "call_default"
            result = default
        elif self._persisted_default is not None:
            source = "persisted_default"
            result = self._persisted_default  # already validated in constructor
        else:
            raise EnvVarMissingError(f"error getting {repr(self._key)} from any source")
        # handle missing values
        if result is None:
            raise EnvVarMissingError(
                f"error getting {repr(self._key)} from {repr(source)}"
            )
        # validate the result
        try:
            return self._val_validator(result)
        except Exception as e:
            raise EnvVarValidationError(
                f"error getting {repr(self._key)} from {repr(source)}, validation failed: {e}"
            ) from e

    # ===== static helpers ===== #

    @classmethod
    def as_converter(cls, fn: EnvVarFnConverterHint[T]) -> EnvVarFnConverterHint[T]:
        def _converter(value: str) -> T:
            try:
                return fn(value)
            except Exception as e:
                raise EnvVarConversionError(f"error converting {value} to {fn}: {e}")

        return _converter

    @classmethod
    def as_validator(cls, fn: EnvVarFnValidatorHint[T]) -> EnvVarFnValidatorHint[T]:
        def _validator(value: T) -> T:
            try:
                return fn(value)
            except Exception as e:
                raise EnvVarValidationError(
                    f"error validating {repr(value)} with {fn}: {e}"
                )

        return _validator

    @classmethod
    def validator_sequence(
        cls,
        *fns: EnvVarFnValidatorHint[T],
    ) -> EnvVarFnValidatorHint[T]:
        def _validator(value: T) -> T:
            for fn in fns:
                if fn is not None:
                    value = fn(value)
            return value

        return _validator

    @classmethod
    def validator_allowed(cls, allowed_values: Iterable[T]) -> EnvVarFnValidatorHint[T]:
        allowed_values = set(allowed_values)
        if not allowed_values:
            raise ValueError("allowed_values must not be empty")

        def _validator(value: T) -> T:
            if value not in allowed_values:
                raise EnvVarValidationError(
                    f"value {repr(value)} must be one of: {allowed_values}"
                )
            return value

        return _validator

    @classmethod
    def validator_min_max(
        cls, min_value: Optional[T], max_value: Optional[T]
    ) -> EnvVarFnValidatorHint[T]:
        def _validator(value: T) -> T:
            if min_value is not None and value < min_value:
                raise EnvVarValidationError(
                    f"value {repr(value)} must be greater than or equal to {min_value}"
                )
            if max_value is not None and value > max_value:
                raise EnvVarValidationError(
                    f"value {repr(value)} must be less than or equal to {max_value}"
                )
            return value

        return _validator

    # ===== factory methods ===== #

    @classmethod
    def env_str(
        cls,
        key: str,
        *,
        default: Optional[str] = None,
        validator: Optional[EnvVarFnValidatorHint[str]] = None,
    ) -> "EnvVar[str]":
        return cls(
            key=key,
            default=default,
            converter=cls.as_converter(str),
            validator=validator,
        )

    @classmethod
    def env_int(
        cls,
        key: str,
        *,
        default: Optional[int] = None,
        validator: Optional[EnvVarFnValidatorHint[int]] = None,
    ) -> "EnvVar[int]":
        return cls(
            key=key,
            default=default,
            converter=cls.as_converter(int),
            validator=validator,
        )

    @classmethod
    def env_float(
        cls,
        key: str,
        *,
        default: Optional[float] = None,
        validator: Optional[EnvVarFnValidatorHint[float]] = None,
    ) -> "EnvVar[float]":
        return cls(
            key=key,
            default=default,
            converter=cls.as_converter(float),
            validator=validator,
        )

    @classmethod
    def env_bool(
        cls,
        key: str,
        *,
        default: Optional[bool] = None,
        # extra settings
        convert_keys_true: Sequence[str] = ("y", "yes", "t", "true", "1"),
        convert_keys_false: Sequence[str] = ("n", "no", "f", "false", "0"),
        convert_lowercase: bool = True,
        # not really useful for bool, but keep for consistency
        validator: Optional[EnvVarFnValidatorHint[bool]] = None,
    ) -> "EnvVar[bool]":
        def convert_bool(value: str) -> bool:
            if convert_lowercase:
                value = value.lower()
            if value in convert_keys_true:
                return True
            elif value in convert_keys_false:
                return False
            else:
                raise EnvVarConversionError(
                    f"cannot convert environment variable `{key}={value}` into bool, must be one of: {sorted(list(convert_keys_true) + list(convert_keys_false))}"
                )

        return cls(
            key=key,
            default=default,
            converter=convert_bool,
            validator=validator,
        )


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
