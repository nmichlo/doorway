import os
from pathlib import Path
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from doorway._hash import HashAlgo
from doorway._hash import HashMode
from doorway._hash import hash_file
from doorway._hash import hash_str


# ========================================================================= #
# shard files                                                               #
# ========================================================================= #



def shard_hash(
    file_path: Union[str, Path],
    hash_data: str = 'name',
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
):
    assert isinstance(file_path, (str, Path)), f'file_path must be a str or Path, got type: {type(file_path)} with value: {repr(file_path)}'
    file_path = str(file_path)
    # compute the hash
    if hash_data == 'name':
        return hash_str(os.path.basename(file_path), hash_algo=hash_algo)
    elif hash_data == 'abspath':
        return hash_str(os.path.abspath(file_path), hash_algo=hash_algo)
    elif hash_data == 'path':
        return hash_str(file_path, hash_algo=hash_algo)
    elif hash_data == 'disk':
        return hash_file(file_path, hash_mode=hash_mode, hash_algo=hash_algo, hash_missing=False)
    else:
        raise KeyError(f'invalid hash_data: {repr(hash_data)}')


def shard_idx(
    file_path: Union[str, Path],
    num_shards: int,
    hash_data: str = 'name',
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    seed: Optional[int] = None,
):
    # checks & defaults
    if seed is None:
        seed = 0
    assert isinstance(seed, int), f'the seed must be an integer or None, got: {repr(seed)}'
    assert isinstance(num_shards, int) and (num_shards > 0), f'num_shards must be an integer that is > 0, got: {repr(num_shards)}'
    # compute the hash for the file
    hash = shard_hash(file_path, hash_data=hash_data, hash_mode=hash_mode, hash_algo=hash_algo)
    # convert hashes to integers, and assign to correct split
    # -- the seed does not affect randomness, rather it just acts as a hash offset
    idx = (int(hash, 16) + seed) % num_shards
    # add the path to the correct shard
    return idx


def shards_deterministic(
    file_paths: Sequence[Union[str, Path]],
    num_shards: int,
    hash_data: str = 'name',
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    seed: Optional[int] = None,
) -> List[List[str]]:
    """
    Shard files based on their hashes instead of random seeds
    """
    # create new array of shards
    shards = [[] for _ in range(num_shards)]
    # assign paths to shards
    for file_path in file_paths:
        idx = shard_idx(file_path, num_shards, hash_data=hash_data, hash_mode=hash_mode, hash_algo=hash_algo, seed=seed)
        shards[idx].append(file_path)
    return shards


def shards_deterministic_grouped(
    file_paths: Sequence[str],
    group_sizes: Sequence[int],
    hash_data: str = 'name',
    hash_mode: Optional[HashMode] = None,
    hash_algo: Optional[HashAlgo] = None,
    seed: Optional[int] = None,
) -> List[List[str]]:
    """
    Shard files based on their hashes instead of random seeds
    -- This is useful if you need to split a dataset, but you expect changes to be made to it,
       eg. files will always randomly be assigned to the same shared
    """

    # checks
    assert all(isinstance(size, int) and (size >= 0) for size in group_sizes), f'values of group_sizes must be integers that are >= 0, got: {repr(group_sizes)}'
    # get all the shards
    shards = shards_deterministic(
        file_paths=file_paths,
        num_shards=sum(group_sizes),
        hash_data=hash_data,
        hash_mode=hash_mode,
        hash_algo=hash_algo,
        seed=seed,
    )
    # group all the shards together
    splits, i = [], 0
    for size in group_sizes:
        splits.append([path for shard in shards[i:i+size] for path in shard])
    # done!
    return splits


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'shard_hash',
    'shard_idx',
    'shards_deterministic',
    'shards_deterministic_grouped',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
