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
    "c",
    # ===== atomic ===== #
    "AtomicPath",
    "AtomicOpen",
    # ===== context ===== #
    "ctx_no_stdout",
    "ctx_no_stderr",
    "ctx_temp_attr",
    "ctx_temp_wd",
    "ctx_temp_sys_args",
    "ctx_temp_environ",
    "ctx_do_undo",
    # ===== env_vars ===== #
    "EnvVar",
    # errors
    "EnvVarError",
    "EnvVarMissingError",
    "EnvVarValidationError",
    "EnvVarConversionError",
    # ===== fmt ===== #
    "fmt_use_colors_get",
    "fmt_bytes_to_human",
    # ===== hash ===== #
    # types
    "Hash",
    "Hashes",
    "HashMode",
    "HashAlgo",
    "HashPath",
    # errors
    "HashError",
    # hash mode
    "hash_mode_get",
    "hash_algo_get",
    # normalise hash
    "hash_norm",
    # compute hash
    "hash_bytes",
    "hash_bytes_iter",
    "hash_str",
    "hash_file",
    "hash_file_validate",
    "hash_file_is_valid",
    # ===== inout ===== #
    "io_download",
    # ===== modify_path ===== #
    "basename_split_ext",
    "basename_modify",
    "path_basename_modify",
    # ===== shard ===== #
    "shard_hash",
    "shard_idx",
    "sharded",
    "sharded_and_grouped",
    # ===== stale ===== #
    "stalefile_is_stale",
    "stalefile_generate",
    "stalefile_decorator",
    "Stalefile",
]

# colors
import doorway._colors as c

# other
from doorway._atomic import (
    AtomicPath,
    AtomicOpen,
)
from doorway._ctx import (
    ctx_no_stdout,
    ctx_no_stderr,
    ctx_temp_attr,
    ctx_temp_wd,
    ctx_temp_sys_args,
    ctx_temp_environ,
    ctx_do_undo,
)
from doorway._env_vars import (
    EnvVar,
    EnvVarError,
    EnvVarValidationError,
    EnvVarMissingError,
    EnvVarConversionError,
)
from doorway._fmt import (
    fmt_use_colors_get,
    fmt_bytes_to_human,
)
from doorway._hash import (
    Hash,
    Hashes,
    HashMode,
    HashAlgo,
    HashPath,
    HashError,
    hash_mode_get,
    hash_algo_get,
    hash_norm,
    hash_bytes,
    hash_bytes_iter,
    hash_str,
    hash_file,
    hash_file_validate,
    hash_file_is_valid,
)
from doorway._inout import (
    io_download,
)
from doorway._modify_path import (
    basename_split_ext,
    basename_modify,
    path_basename_modify,
)
from doorway._shard import (
    shard_hash,
    shard_idx,
    sharded,
    sharded_and_grouped,
)
from doorway._stale import (
    stalefile_is_stale,
    stalefile_generate,
    stalefile_decorator,
    Stalefile,
)
