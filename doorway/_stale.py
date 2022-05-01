#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2021 Nathan Juraj Michlo
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
from functools import wraps
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Union

from doorway._hash import HashPath
from doorway._hash import Hashes
from doorway._hash import HashAlgo
from doorway._hash import HashMode
from doorway._hash import hash_file
from doorway._hash import hash_norm
from doorway._hash import hash_file_validate


LOG = logging.getLogger(__name__)


# ========================================================================= #
# Functional Stalefile                                                      #
# ========================================================================= #


def stalefile_is_stale(
    path: HashPath,
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
):
    # compute the hash for a file
    fhash = hash_file(path=path, hash_mode=hash_mode, hash_algo=hash_algo, hash_missing=True)
    # check if the file is stale or not
    if not fhash:
        LOG.info(f'file is stale because it does not exist: {repr(path)}')
        return True
    # obtain the target hash
    hash = hash_norm(hash=hash, hash_mode=hash_mode, hash_algo=hash_algo)
    # check if the file is stale or not
    if fhash != hash:
        LOG.warning(f'file is stale because the computed {hash_mode}:{hash_algo} hash: {fhash} does not match the target hash: {hash} for file: {repr(path)}')
        return True
    # the file is fresh
    LOG.debug(f'file is fresh: {repr(path)}')
    return False


def stalefile_generate(
    make_file_fn: Callable[[HashPath], NoReturn],
    path: HashPath,
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
) -> HashPath:
    is_stale = stalefile_is_stale(path=path, hash=hash, hash_mode=hash_mode, hash_algo=hash_algo)
    # if the file is stale:
    # - 1. produce is using the wrapped function
    # - 2. validate the produced file and throw errors if it is wrong!
    if is_stale:
        LOG.debug(f'calling wrapped function: {make_file_fn} because the file is stale: {repr(path)}')
        make_file_fn(path)
        hash_file_validate(path, hash=hash, hash_mode=hash_mode, hash_algo=hash_algo, hash_missing=True)
    # if the file is fresh
    # - 1. don't actually do anything, skip calling the producer!
    else:
        LOG.debug(f'skipped wrapped function: {make_file_fn} because the file is fresh: {repr(path)}')
    # return the path that contains the valid file!
    return path


def stalefile_decorator(
    path: str,
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    make_file_fn: Optional[Callable[[HashPath], NoReturn]] = None,
) -> Union[
        Callable[[Callable[[HashPath], NoReturn]], Callable[[], HashPath]],
        Callable[[], HashPath],
]:
    # the wrapped function should take in a path and produce a file at that location.
    # a. if the file already exists, this function is not called!
    # b. if the file does not exist, the function is called to generate the file, which is then validated!
    def decorator(make_file_fn: Callable[[HashPath], NoReturn]) -> Callable[[], HashPath]:
        @wraps(make_file_fn)
        def make_file_if_stale() -> HashPath:
            return stalefile_generate(
                make_file_fn=make_file_fn,
                path=path,
                hash=hash,
                hash_mode=hash_mode,
                hash_algo=hash_algo,
            )
        return make_file_if_stale
    # wrap directly if function is specified
    if make_file_fn is not None:
        return decorator(make_file_fn)
    return decorator


# ========================================================================= #
# Stalefile Class                                                           #
# ========================================================================= #



class Stalefile(object):
    """
    decorator that only runs the wrapped function if a
    file does not exist, or its hash does not match.
    """

    def __init__(
        self,
        path: str,
        hash: Hashes,
        hash_mode: Optional[HashMode] = None,
        hash_algo: Optional[HashAlgo] = None,
    ):
        self._path = path
        self._hash = hash
        self._hash_mode = hash_mode
        self._hash_algo = hash_algo

    def generate(self, make_file_fn: Callable[[HashPath], NoReturn]) -> HashPath:
        return stalefile_generate(
            make_file_fn=make_file_fn,
            path=self._path,
            hash=self._hash,
            hash_mode=self._hash_mode,
            hash_algo=self._hash_algo,
        )

    def decorator(self, make_file_fn: Optional[Callable[[HashPath], NoReturn]] = None) -> Callable[[], HashPath]:
        # the wrapped function should take in a path and produce a file at that location.
        # a. if the file already exists, this function is not called!
        # b. if the file does not exist, the function is called to generate the file, which is then validated!
        return stalefile_decorator(
            path=self._path,
            hash=self._hash,
            hash_mode=self._hash_mode,
            hash_algo=self._hash_algo,
            make_file_fn=make_file_fn,
        )

    def is_stale(self):
        return stalefile_is_stale(
            path=self._path,
            hash=self._hash,
            hash_mode=self._hash_mode,
            hash_algo=self._hash_algo,
        )

    def __bool__(self):
        return self.is_stale()


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'stalefile_is_stale',
    'stalefile_generate',
    'stalefile_decorator',
    'Stalefile',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
