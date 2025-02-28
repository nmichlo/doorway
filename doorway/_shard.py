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


__all__ = [
    "shard_hash",
    "shard_idx",
    "sharded",
    "sharded_weighted",
]

import os
from pathlib import Path
from typing import Callable, List, Literal, Tuple
from typing import Iterable
from typing import Optional
from typing import Union
from typing import TypeVar

from doorway._hash import Hash
from doorway._hash import HashAlgo
from doorway._hash import hash_str


# ========================================================================= #
# individual shards                                                         #
# ========================================================================= #


T = TypeVar("T")

_SHARD_KEYS = {
    "basename": os.path.basename,
    "abspath": os.path.abspath,
    "input": lambda x: x,
}

ShardKey = Optional[Union[str, Callable[[T], str]]]


def shard_hash(
    value: T,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
) -> Hash:
    # get the hash data function
    if shard_key is None:
        pass
    elif callable(shard_key):
        value = shard_key(value)
    elif isinstance(shard_key, str):
        fn = _SHARD_KEYS.get(shard_key, None)  # cannot be None here
        if fn is None:
            raise KeyError(
                f"if shard_key is a str, it must be one of: {list(_SHARD_KEYS.keys())}, got: {repr(shard_key)}"
            )
        value = fn(value)
    else:
        raise ValueError(
            f"shard_key must be a str, callable or None, got: {repr(shard_key)}"
        )
    # get the string
    assert isinstance(value, (str, Path)), (
        f"The value after shard_key is applied must be a str or Path, instead got type: {type(value)}, with value: {repr(value)}"
    )
    # compute the hash
    return hash_str(str(value), hash_algo=hash_algo)


def shard_idx(
    value: T,
    num_shards: int,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
) -> int:
    assert isinstance(num_shards, int) and (num_shards > 0), (
        f"num_shards must be an integer that is > 0, got: {repr(num_shards)}"
    )
    # compute the hash for the value
    hash = shard_hash(value, shard_key=shard_key, hash_algo=hash_algo)
    # convert hashes to integers, and assign to correct split
    return int(hash, 16) % num_shards


# ========================================================================= #
# multiples shards                                                          #
# ========================================================================= #


_SHARD_RETURNS = {
    "pairs": lambda i, value: (i, value),
    "indices": lambda i, value: i,
    "values": lambda i, value: value,
}

_ShardsReturnHint = Union[
    List[Tuple[int, T]],  # pairs
    List[int],  # indices
    List[T],  # values
]


def sharded(
    values: Iterable[T],
    num_shards: int,
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
    returns: Literal["pairs", "indices", "values"] = "values",
) -> _ShardsReturnHint[T]:
    """
    Shard files based on their hashes instead of random seeds
    """
    # shard functions
    if returns not in _SHARD_RETURNS:
        raise KeyError(
            f"invalid shards returns: {repr(returns)}, must be one of: {sorted(_SHARD_RETURNS.keys())}"
        )
    value_getter = _SHARD_RETURNS[returns]
    # create new array of shards
    shards = [[] for _ in range(num_shards)]
    # assign paths to shards
    for i, value in enumerate(values):
        idx = shard_idx(value, num_shards, shard_key=shard_key, hash_algo=hash_algo)
        shards[idx].append(value_getter(i, value))
    # results
    return shards


def sharded_weighted(
    values: Iterable[T],
    shard_weights: Iterable[int],
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
    returns: Literal["pairs", "indices", "values"] = "values",
) -> _ShardsReturnHint[T]:
    """
    Shard files based on their hashes instead of random seeds, and group them based on weights
    -- This is useful if you need to split a dataset, but you expect changes to be made to it,
       eg. files will always randomly be assigned to the same shared
    """
    shard_weights = list(shard_weights)
    # checks
    assert all(isinstance(size, int) and (size >= 0) for size in shard_weights), (
        f"values of group_sizes must be integers that are >= 0, got: {repr(shard_weights)}"
    )
    # get all the shards
    shards = sharded(
        values=values,
        num_shards=sum(shard_weights),
        shard_key=shard_key,
        hash_algo=hash_algo,
        returns=returns,
    )
    # group all the shards together
    weighted_buckets, i = [], 0
    for num_shards in shard_weights:
        weighted_buckets.append(
            [item for shard in shards[i : i + num_shards] for item in shard]
        )
        i += num_shards
    # done!
    return weighted_buckets


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
