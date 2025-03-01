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
    "io_download",
]

import logging
import os
import warnings
from typing import Literal


from doorway._atomic import AtomicOpen


LOG = logging.getLogger(__name__)


# ========================================================================= #
# files/dirs exist                                                          #
# ========================================================================= #


def io_download(
    src_url: str,
    dst_path: str,
    *,
    exists_mode: Literal["skip", "overwrite", "error"] = "error",
    chunk_size: int = 16384,
    progress: bool = True,
):
    # make sure we have the correct imports
    try:
        import requests
    except ImportError:
        raise ImportError(
            "The `requests` package is required for downloading files.\n"
            "You can install it via: `pip install requests`."
        )

    try:
        from tqdm import tqdm
    except ImportError:
        warnings.warn(
            "The `tqdm` package is not installed, progress bar will not be shown.\n"
        )
        tqdm = None
        progress = False

    # skip existing
    if exists_mode == "skip":
        if os.path.exists(dst_path):
            LOG.info(f"Skipping: {dst_path}")
            return
        overwrite = False
    elif exists_mode == "overwrite":
        overwrite = True
    elif exists_mode == "error":
        overwrite = False
    else:
        raise ValueError(f"invalid `exists_mode`: {exists_mode}")

    # write the file
    with AtomicOpen(dst_path, "wb" if overwrite else "xb") as fp:
        response = requests.get(src_url, stream=True)

        # get the file size from the request for the progress bar
        total_length = response.headers.get("content-length")
        if total_length is not None:
            total_length = int(total_length)

        # download with progress bar
        LOG.info(f"Downloading: {src_url} to: {dst_path}")

        if progress and tqdm is not None:
            with tqdm(
                total=total_length,
                desc="Downloading",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress:
                for data in response.iter_content(chunk_size=chunk_size):
                    fp.write(data)
                    progress.update(chunk_size)
        else:
            for data in response.iter_content(chunk_size=chunk_size):
                fp.write(data)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
