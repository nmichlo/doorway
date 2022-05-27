import os
from pathlib import Path
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from typing import TypeVar

from doorway._hash import Hash
from doorway._hash import HashAlgo
from doorway._hash import hash_str


# ========================================================================= #
# individual shards                                                         #
# ========================================================================= #


T = TypeVar('T')

_SHARD_KEYS = {
    'basename': os.path.basename,
    'abspath': os.path.abspath,
    'input': lambda x: x,
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
            raise KeyError(f'if shard_key is a str, it must be one of: {list(_SHARD_KEYS.keys())}, got: {repr(shard_key)}')
        value = fn(value)
    else:
        raise ValueError(f'shard_key must be a str, callable or None, got: {repr(shard_key)}')
    # get the string
    assert isinstance(value, (str, Path)), f'The value after shard_key is applied must be a str or Path, instead got type: {type(value)}, with value: {repr(value)}'
    # compute the hash
    return hash_str(str(value), hash_algo=hash_algo)


def shard_idx(
    value: T,
    num_shards: int,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
) -> int:
    assert isinstance(num_shards, int) and (num_shards > 0), f'num_shards must be an integer that is > 0, got: {repr(num_shards)}'
    # compute the hash for the value
    hash = shard_hash(value, shard_key=shard_key, hash_algo=hash_algo)
    # convert hashes to integers, and assign to correct split
    return int(hash, 16) % num_shards


# ========================================================================= #
# multiples shards                                                          #
# ========================================================================= #


_SHARD_RETURNS = {
    'pairs':   lambda i, value: (i, value),
    'indices': lambda i, value: i,
    'values':  lambda i, value: value,
}


def sharded(
    values: Iterable[T],
    num_shards: int,
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
    returns: str = 'values'
) -> list:
    """
    Shard files based on their hashes instead of random seeds
    """
    # shard functions
    if returns not in _SHARD_RETURNS:
        raise KeyError(f'invalid shards returns: {repr(returns)}, must be one of: {sorted(_SHARD_RETURNS.keys())}')
    value_getter = _SHARD_RETURNS[returns]
    # create new array of shards
    shards = [[] for _ in range(num_shards)]
    # assign paths to shards
    for i, value in enumerate(values):
        idx = shard_idx(value, num_shards, shard_key=shard_key, hash_algo=hash_algo)
        shards[idx].append(value_getter(i, value))
    # results
    return shards


def sharded_and_grouped(
    values: Iterable[T],
    group_sizes: Iterable[int],
    shard_key: ShardKey[T] = None,
    hash_algo: Optional[HashAlgo] = None,
    returns: str = 'values'
) -> list:
    """
    Shard files based on their hashes instead of random seeds
    -- This is useful if you need to split a dataset, but you expect changes to be made to it,
       eg. files will always randomly be assigned to the same shared
    """
    group_sizes = list(group_sizes)
    # checks
    assert all(isinstance(size, int) and (size >= 0) for size in group_sizes), f'values of group_sizes must be integers that are >= 0, got: {repr(group_sizes)}'
    # get all the shards
    shards = sharded(
        values=values,
        num_shards=sum(group_sizes),
        shard_key=shard_key,
        hash_algo=hash_algo,
        returns=returns,
    )
    # group all the shards together
    splits, i = [], 0
    for size in group_sizes:
        splits.append([path for shard in shards[i:i+size] for path in shard])
        i += size
    # done!
    return splits


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'shard_hash',
    'shard_idx',
    'sharded',
    'sharded_and_grouped',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
