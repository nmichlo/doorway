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
from doorway._atomic import AtomicOpen


LOG = logging.getLogger(__name__)


# ========================================================================= #
# files/dirs exist                                                          #
# ========================================================================= #


def io_download(
    src_url: str,
    dst_path: str,
    overwrite_existing: bool = False,
    chunk_size: int = 16384,
):
    # make sure we have the correct imports
    try:
        import requests
        from tqdm import tqdm
    except ImportError as e:
        raise ImportError(f'`requests` and `tqdm` need to be installed for `{io_download.__name__}`') from e

    # write the file
    with AtomicOpen(dst_path, 'wb' if overwrite_existing else 'xb') as fp:
        response = requests.get(src_url, stream=True)

        # get the file size from the request for the progress bar
        total_length = response.headers.get('content-length')
        if total_length is not None:
            total_length = int(total_length)

        # download with progress bar
        LOG.info(f'Downloading: {src_url} to: {dst_path}')
        with tqdm(total=total_length, desc=f'Downloading', unit='B', unit_scale=True, unit_divisor=1024) as progress:
            for data in response.iter_content(chunk_size=chunk_size):
                fp.write(data)
                progress.update(chunk_size)


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'io_download',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
