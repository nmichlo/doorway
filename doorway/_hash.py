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

import hashlib
import os
import warnings
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import NoReturn
from typing import Optional
from typing import Union
from doorway._utils import VarHandlerStr


# ========================================================================= #
# byte producers                                                            #
# ========================================================================= #


def _yield_file_bytes(file: str, chunk_size=16384):
    with open(file, 'rb') as f:
        while True:
            bytes = f.read(chunk_size)
            if not bytes:
                return
            yield bytes


def _yield_fast_hash_bytes(file: str, chunk_size=16384, num_chunks=3):
    assert num_chunks >= 2
    # return the size in bytes
    size = os.path.getsize(file)
    yield size.to_bytes(length=64//8, byteorder='big', signed=False)
    # return file bytes chunks
    if size < chunk_size * num_chunks:
        # we can't return chunks because the file is too small, return everything!
        yield from _yield_file_bytes(file, chunk_size=chunk_size)
    else:
        # includes evenly spaced start, middle and end chunks
        with open(file, 'rb') as f:
            for i in range(num_chunks):
                pos = (i * (size - chunk_size)) // (num_chunks - 1)
                f.seek(pos)
                yield f.read(chunk_size)


# ========================================================================= #
# hash algos                                                                #
# ========================================================================= #


Hash = str
Hashes = Union[str, Dict[str, str]]
HashMode = str
HashAlgo = str
HashPath = Union[str, Path]


# ========================================================================= #
# hash mode                                                                 #
# ========================================================================= #


_FILE_BYTE_PRODUCERS = {
    'full': _yield_file_bytes,
    'fast': _yield_fast_hash_bytes,
}


_VAR_HANDLER_HASH_MODE = VarHandlerStr(
    identifier='hash_mode',
    environ_key='DOORWAY_HASH_MODE',
    fallback_value='fast',
    allowed_values=tuple(_FILE_BYTE_PRODUCERS.keys()),
)


def hash_mode_set_default(hash_mode: Optional[HashMode]) -> NoReturn:
    return _VAR_HANDLER_HASH_MODE.set_default_value(value=hash_mode)


def hash_mode_get(hash_mode: Optional[HashMode] = None) -> HashMode:
    return _VAR_HANDLER_HASH_MODE.get_value(override=hash_mode)


_VAR_HANDLER_HASH_ALGO = VarHandlerStr(
    identifier='hash_algo',
    environ_key='DOORWAY_HASH_ALGO',
    fallback_value='md5',
    allowed_values=tuple(hashlib.algorithms_guaranteed),  # hashlib.algorithms_available?
)


def hash_algo_set_default(hash_algo: Optional[HashAlgo]) -> NoReturn:
    return _VAR_HANDLER_HASH_ALGO.set_default_value(value=hash_algo)


def hash_algo_get(hash_algo: Optional[HashAlgo] = None) -> HashAlgo:
    return _VAR_HANDLER_HASH_ALGO.get_value(override=hash_algo)


# ========================================================================= #
# file hashing                                                              #
# ========================================================================= #


def hash_bytes(bytes_str: bytes, hash_algo: Optional[HashAlgo] = None) -> str:
    # normalise the hash_algo
    hash_algo = hash_algo_get(hash_algo=hash_algo)
    # generate hash and convert to a string
    return hashlib.new(hash_algo, data=bytes_str).hexdigest()


def hash_bytes_iter(bytes_iter: Iterable[bytes], hash_algo: Optional[HashAlgo] = None) -> str:
    # normalise the hash_algo
    hash_algo = hash_algo_get(hash_algo=hash_algo)
    # generate hash and convert to a string
    hash = hashlib.new(hash_algo)
    for bytes in bytes_iter:
        hash.update(bytes)
    return hash.hexdigest()


def hash_str(str: str, hash_algo: Optional[HashAlgo] = None, encoding: str = 'utf-8') -> str:
    # encode string as bytes and then hash
    return hash_bytes(str.encode(encoding), hash_algo=hash_algo)


def hash_file(
    path: HashPath,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    hash_missing: bool = False,
) -> Hash:
    """
    :param path: the path to the file
    :param hash_mode: "full" uses all the bytes in the file to compute the hash, "fast" uses the start, middle, end bytes as well as the size of the file in the hash. Default is "fast".
    :param hash_algo: the kind of hash algorithm to use, see `hashlib` for details. Default is "md5"
    :param hash_missing: If enabled, then an error is not thrown if the file is missing, rather an empty hash is returned!
    :return: the hexdigest of the hash
    :raises FileNotFoundError
    """
    # normalise the hash_mode
    hash_mode = hash_mode_get(hash_mode=hash_mode)
    # check the file exists
    path = str(path)
    if os.path.exists(path):
        if not os.path.isfile(path):
            raise IsADirectoryError(f'the path exists but is not a file: {repr(path)}')
    else:
        if hash_missing:
            return ''
        raise FileNotFoundError(f'could not compute hash for missing file: {repr(path)}')
    # get file bytes iterator
    byte_producer = _FILE_BYTE_PRODUCERS[hash_mode]
    bytes_iter = byte_producer(path)
    # get file bytes iterator
    return hash_bytes_iter(bytes_iter, hash_algo=hash_algo)


# ========================================================================= #
# file hashing utils                                                        #
# ========================================================================= #


class HashError(Exception):
    """
    Raised if the hash of a file was invalid.
    """


def hash_norm(
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
) -> Hash:
    """
    file hashes depend on the mode.
    - Allow hashes to be dictionaries that map the hash_mode or hash_algo to the hash.
      This function returns the correct hash if it is a dictionary.

    priority of keys:
       1. `mode:algo`
       2. `mode`
       3. `algo`
    """
    if isinstance(hash, dict):
        hash_mode = hash_mode_get(hash_mode)
        hash_algo = hash_algo_get(hash_algo)
        multi_key = f'{hash_mode}:{hash_algo}'
        # 1. try get `mode:algo`
        if multi_key in hash:
            hash = hash[multi_key]
        elif hash_mode in hash:
            warnings.warn('obtaining the hash directly from the `hash_mode` is deprecated, please use the full key `hash_mode:hash_algo`')
            hash = hash[hash_mode]
        elif hash_algo in hash:
            warnings.warn('obtaining the hash directly from the `hash_algo` is deprecated, please use the full key `hash_mode:hash_algo`')
            hash = hash[hash_algo]
        else:
            raise KeyError(f'hash dictionary does not contain a valid key for either 1. {repr(multi_key)}, 2. {repr(hash_mode)}, or 3. {repr(hash_algo)}. Available hash keys are: {sorted(hash.keys())}')
    # check the result
    if not isinstance(hash, str):
        raise TypeError(f'normalized hash should be a str, got type: {type(hash)} for value: {repr(hash)}')
    # done!
    return hash


def hash_file_validate(
    path: HashPath,
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    hash_missing: bool = False,
) -> NoReturn:
    """
    :raises FileNotFoundError, HashError
    """
    # normalize the hash
    hash: str = hash_norm(hash=hash, hash_mode=hash_mode)
    # compute the hash
    fhash = hash_file(path=path, hash_algo=hash_algo, hash_mode=hash_mode, hash_missing=hash_missing)
    # check the hash
    if fhash != hash:
        # functions above also call this, we need to do it again for the error message
        hash_mode = hash_mode_get(hash_mode)
        hash_algo = hash_algo_get(hash_algo)
        # raise the error!
        raise HashError(f'computed {hash_mode} {hash_algo} hash: {repr(fhash)} does not match expected hash: {repr(hash)} for file: {repr(path)}')


def hash_file_is_valid(
    path: HashPath,
    hash: Hashes,
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    hash_missing: bool = False,
) -> bool:
    try:
        hash_file_validate(path=path, hash=hash, hash_algo=hash_algo, hash_mode=hash_mode, hash_missing=hash_missing)
    except HashError:
        return False
    return True


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    # types
    'Hash',
    'Hashes',
    'HashMode',
    'HashAlgo',
    'HashPath',
    # errors
    'HashError',
    # hash mode
    'hash_mode_set_default',
    'hash_mode_get',
    'hash_algo_set_default',
    'hash_algo_get',
    # normalise hash
    'hash_norm',
    # compute hash
    'hash_bytes',
    'hash_bytes_iter',
    'hash_str',
    'hash_file',
    'hash_file_validate',
    'hash_file_is_valid',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
