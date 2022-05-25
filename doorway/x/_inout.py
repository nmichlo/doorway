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
import os

from doorway.x._atomic import AtomicSaveFile


LOG = logging.getLogger(__name__)


# ========================================================================= #
# files/dirs exist                                                          #
# ========================================================================= #


def io_download(url: str, save_path: str, overwrite_existing: bool = False, chunk_size: int = 16384):
    import requests
    from tqdm import tqdm
    # write the file
    with AtomicSaveFile(file=save_path, open_mode='wb', overwrite=overwrite_existing) as (_, file):
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')
        # cast to integer if content-length exists on response
        if total_length is not None:
            total_length = int(total_length)
        # download with progress bar
        LOG.info(f'Downloading: {url} to: {save_path}')
        with tqdm(total=total_length, desc=f'Downloading', unit='B', unit_scale=True, unit_divisor=1024) as progress:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                progress.update(chunk_size)


def io_copy(src: str, dst: str, overwrite_existing: bool = False):
    # copy the file
    if os.path.abspath(src) == os.path.abspath(dst):
        raise FileExistsError(f'input and output paths for copy are the same, skipping: {repr(dst)}')
    else:
        import shutil
        with AtomicSaveFile(file=dst, overwrite=overwrite_existing) as path:
            shutil.copyfile(src, path)


# def io_retrieve(src_uri: str, dst_path: str, overwrite_existing: bool = False):
#     uri, is_url = parse_uri_and_type(src_uri)
#     if is_url:
#         io_download(url=uri, save_path=dst_path, overwrite_existing=overwrite_existing)
#     else:
#         io_copy(src=uri, dst=dst_path, overwrite_existing=overwrite_existing)



# ========================================================================= #
# export                                                                    #
# ========================================================================= #


# def ensure_dir_exists(*join_paths: str, is_file=False, absolute=False):
#     import os
#     # join path
#     path = os.path.join(*join_paths)
#     # to abs path
#     if absolute:
#         path = os.path.abspath(path)
#     # remove file
#     dirs = os.path.dirname(path) if is_file else path
#     # create missing directory
#     if os.path.exists(dirs):
#         if not os.path.isdir(dirs):
#             raise IOError(f'path is not a directory: {dirs}')
#     else:
#         os.makedirs(dirs, exist_ok=True)
#         log.info(f'created missing directories: {dirs}')
#     # return directory
#     return path


# def ensure_parent_dir_exists(*join_paths: str):
#     return ensure_dir_exists(*join_paths, is_file=True, absolute=True)


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'io_download',
    'io_copy',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
