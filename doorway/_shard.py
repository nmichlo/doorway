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


__all__ = [
    "shard_hash",
    "shard_idx",
    "sharded",
    "sharded_weighted",
]

import os
from collections.abc import Callable
from collections.abc import Iterable
from pathlib import Path
from typing import Literal
from typing import overload

from doorway._hash import Hash
from doorway._hash import HashAlgo
from doorway._hash import hash_str

# ========================================================================= #
# individual shards                                                         #
# ========================================================================= #


_SHARD_KEYS: dict[str, Callable[[str | Path], str | Path]] = {
    "basename": os.path.basename,
    "abspath": os.path.abspath,
    "input": lambda x: x,
}

type ShardKey[T] = str | Callable[[T], str] | None


def shard_hash[T](
    value: T,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
) -> Hash:
    # get the hash data function
    key: str | Path | T
    if shard_key is None:
        key = value
    elif isinstance(shard_key, str):
        fn = _SHARD_KEYS.get(shard_key, None)  # cannot be None here
        if fn is None:
            raise KeyError(
                f"if shard_key is a str, it must be one of: {list(_SHARD_KEYS.keys())}, got: {repr(shard_key)}"
            )
        assert isinstance(value, (str, Path)), (
            f"The value must be a str or Path to use the preset shard_key {repr(shard_key)}, instead got type: {type(value)}, with value: {repr(value)}"
        )
        key = fn(value)
    elif callable(shard_key):
        key = shard_key(value)
    else:
        raise ValueError(f"shard_key must be a str, callable or None, got: {repr(shard_key)}")
    # get the string
    assert isinstance(key, (str, Path)), (
        f"The value after shard_key is applied must be a str or Path, instead got type: {type(key)}, with value: {repr(key)}"
    )
    # compute the hash
    return hash_str(str(key), hash_algo=hash_algo)


def shard_idx[T](
    value: T,
    num_shards: int,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
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


_SHARD_RETURN_MODES = ("pairs", "indices", "values")

type _ShardsReturnHint[T] = (
    list[list[tuple[int, T]]]  # pairs
    | list[list[int]]  # indices
    | list[list[T]]  # values
)


@overload
def sharded[T](
    values: Iterable[T],
    num_shards: int,
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
    returns: Literal["pairs"],
) -> list[list[tuple[int, T]]]: ...
@overload
def sharded[T](
    values: Iterable[T],
    num_shards: int,
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
    returns: Literal["indices"],
) -> list[list[int]]: ...
@overload
def sharded[T](
    values: Iterable[T],
    num_shards: int,
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
    returns: Literal["values"] = "values",
) -> list[list[T]]: ...
def sharded[T](
    values: Iterable[T],
    num_shards: int,
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
    returns: Literal["pairs", "indices", "values"] = "values",
) -> _ShardsReturnHint[T]:
    """
    Shard files based on their hashes instead of random seeds

    Returns a list of `num_shards` buckets, each holding the items assigned to that shard.
    """
    if returns not in _SHARD_RETURN_MODES:
        raise KeyError(f"invalid shards returns: {repr(returns)}, must be one of: {_SHARD_RETURN_MODES}")
    # create new array of shards, and assign values to the correct shard
    if returns == "pairs":
        shards_pairs: list[list[tuple[int, T]]] = [[] for _ in range(num_shards)]
        for i, value in enumerate(values):
            idx = shard_idx(value, num_shards, shard_key=shard_key, hash_algo=hash_algo)
            shards_pairs[idx].append((i, value))
        return shards_pairs
    elif returns == "indices":
        shards_indices: list[list[int]] = [[] for _ in range(num_shards)]
        for i, value in enumerate(values):
            idx = shard_idx(value, num_shards, shard_key=shard_key, hash_algo=hash_algo)
            shards_indices[idx].append(i)
        return shards_indices
    else:
        shards_values: list[list[T]] = [[] for _ in range(num_shards)]
        for value in values:
            idx = shard_idx(value, num_shards, shard_key=shard_key, hash_algo=hash_algo)
            shards_values[idx].append(value)
        return shards_values


def _group_shards[X](shards: list[list[X]], shard_weights: list[int]) -> list[list[X]]:
    weighted_buckets: list[list[X]] = []
    i = 0
    for num_shards in shard_weights:
        weighted_buckets.append([item for shard in shards[i : i + num_shards] for item in shard])
        i += num_shards
    return weighted_buckets


def sharded_weighted[T](
    values: Iterable[T],
    shard_weights: Iterable[int],
    *,
    shard_key: ShardKey[T] = None,
    hash_algo: HashAlgo | None = None,
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
    num_shards = sum(shard_weights)
    # get all the shards, then group them together based on the weights
    if returns == "pairs":
        shards_pairs: list[list[tuple[int, T]]] = sharded(
            values=values, num_shards=num_shards, shard_key=shard_key, hash_algo=hash_algo, returns="pairs"
        )
        return _group_shards(shards_pairs, shard_weights)
    elif returns == "indices":
        shards_indices: list[list[int]] = sharded(
            values=values, num_shards=num_shards, shard_key=shard_key, hash_algo=hash_algo, returns="indices"
        )
        return _group_shards(shards_indices, shard_weights)
    else:
        shards_values: list[list[T]] = sharded(
            values=values, num_shards=num_shards, shard_key=shard_key, hash_algo=hash_algo, returns="values"
        )
        return _group_shards(shards_values, shard_weights)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
