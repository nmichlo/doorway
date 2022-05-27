import os
from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

from doorway._hash import HashAlgo
from doorway._hash import hash_str


# ========================================================================= #
# individual shards                                                         #
# ========================================================================= #


_SHARD_KEYS = {
    'basename': os.path.basename,
    'abspath': os.path.abspath,
    'input': lambda x: x,
    None: lambda x: x,
}

ShardKey = Union[str, None, Callable[[str], str]]


def shard_hash(
    file_path: Union[str, Path],
    shard_key: ShardKey = 'basename',
    hash_algo: Optional[HashAlgo] = None,
):
    assert isinstance(file_path, (str, Path)), f'file_path must be a str or Path, got type: {type(file_path)} with value: {repr(file_path)}'
    file_path = str(file_path)
    # get the hash data function
    if shard_key in _SHARD_KEYS:
        shard_key = _SHARD_KEYS[shard_key]
    elif not callable(shard_key):
        raise ValueError(f'shard_key must be callable or one of: {list(_SHARD_KEYS.keys())}, got: {repr(shard_key)}')
    # compute the hash
    return hash_str(shard_key(file_path), hash_algo=hash_algo)


def shard_idx(
    file_path: Union[str, Path],
    num_shards: int,
    shard_key: ShardKey = 'basename',
    hash_algo: Optional[HashAlgo] = None,
):
    assert isinstance(num_shards, int) and (num_shards > 0), f'num_shards must be an integer that is > 0, got: {repr(num_shards)}'
    # compute the hash for the file
    hash = shard_hash(file_path, shard_key=shard_key, hash_algo=hash_algo)
    # convert hashes to integers, and assign to correct split
    idx = int(hash, 16) % num_shards
    return idx


# ========================================================================= #
# multiples shards                                                          #
# ========================================================================= #


_SHARD_RETURNS = {
    'pairs': lambda i, file_path: (i, file_path),
    'indices': lambda i, file_path: i,
    'values': lambda i, file_path: file_path,
}


def sharded(
    file_paths: Sequence[Union[str, Path]],
    num_shards: int,
    shard_key: ShardKey = 'basename',
    hash_algo: Optional[HashAlgo] = None,
    returns: str = 'values'
) -> Union[List[List[int]], List[List[str]], List[List[Tuple[int, str]]]]:
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
    for i, file_path in enumerate(file_paths):
        idx = shard_idx(file_path, num_shards, shard_key=shard_key, hash_algo=hash_algo)
        shards[idx].append(value_getter(i, file_path))
    # results
    return shards


def sharded_and_grouped(
    file_paths: Sequence[str],
    group_sizes: Sequence[int],
    shard_key: ShardKey = 'basename',
    hash_algo: Optional[HashAlgo] = None,
    returns: str = 'values'
) -> Union[List[List[int]], List[List[str]], List[List[Tuple[int, str]]]]:
    """
    Shard files based on their hashes instead of random seeds
    -- This is useful if you need to split a dataset, but you expect changes to be made to it,
       eg. files will always randomly be assigned to the same shared
    """

    # checks
    assert all(isinstance(size, int) and (size >= 0) for size in group_sizes), f'values of group_sizes must be integers that are >= 0, got: {repr(group_sizes)}'
    # get all the shards
    shards = sharded(
        file_paths=file_paths,
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
