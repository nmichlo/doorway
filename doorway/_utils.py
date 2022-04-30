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
import os
from typing import NoReturn
from typing import Optional
from typing import Sequence


# ========================================================================= #
# Variable Manager                                                          #
# ========================================================================= #


class VarHandler(object):

    def __init__(
        self,
        identifier: str,
        environ_key: str,
        fallback_value: str,
        allowed_values: Sequence[str],
    ):
        self._environ_key = environ_key
        self._value_fallback = fallback_value
        self._value_default = None
        self._allowed_values = set(allowed_values)
        self._identifier = identifier
        # assertions
        assert self._allowed_values
        assert self._value_fallback in self._allowed_values
        assert str.isidentifier(self._environ_key)
        assert str.isidentifier(self._identifier)

    @property
    def allowed_values(self) -> list:
        return sorted(self._allowed_values)

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def environ_key(self) -> str:
        return self._environ_key

    @property
    def fallback_value(self) -> str:
        return self._value_fallback

    def set_default_value(self, value: Optional[str] = None) -> NoReturn:
        # make sure the hash_algo is valid
        if value is not None:
            if value not in self._allowed_values:
                raise KeyError(f'invalid {self.identifier}: {repr(value)}, must be one of: {self.allowed_values}')
        # update the default mode
        self._value_default = value

    def del_default_value(self) -> NoReturn:
        self._value_default = None

    def get_value(self, override: Optional[str] = None) -> str:
        """
        priority:
          1. manual specification
          2. default mode (set_default_value)
          3. environment variable
          4. fallback mode ("fast")
        """
        if override is not None:
            source = 'manual'
            value = override
        elif self._value_default is not None:
            source = 'default'
            value = self._value_default
        elif self._environ_key in os.environ:
            source = 'environment'
            value = os.environ[self._environ_key]
        else:
            source = 'fallback'
            value = self._value_fallback
        # make sure the hash mode is valid
        if value not in self._allowed_values:
            raise KeyError(f'invalid {self.identifier}: {repr(value)}, obtained from source: {source}, must be one of: {self._allowed_values}')
        # done
        return value


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
