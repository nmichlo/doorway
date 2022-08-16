
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
from pathlib import Path
from typing import BinaryIO
from typing import Optional
from typing import TextIO
from typing import Union

from doorway.x._modify_path import modify_file_name


LOG = logging.getLogger(__name__)


# ========================================================================= #
# Atomic file saving                                                        #
# ========================================================================= #


class AtomicPath(object):
    """
    Within the context, data must be written to a temporary file.
    Once data has been successfully written, the temporary file
    is moved to the location of the destination file.

    The temporary path is set to the same directory as the
    destination path.

    ```
    with AtomicPath('file.txt') as tmp_path:
        with open(tmp_file, 'w') as f:
            f.write("hello world!\n")
    ```
    """

    def __init__(
        self,
        file: Union[str, Path],
        overwrite: bool = False,
        makedirs: bool = False,
        tmp_prefix: Optional[str] = '.temp.',
        tmp_suffix: Optional[str] = None,
    ):
        from uuid import uuid4

        # check files
        if not file or not Path(file).name:
            raise ValueError(f'file must not be empty: {repr(file)}')

        # get files
        self._dst_path = Path(file).absolute()
        self._tmp_path = modify_file_name(self._dst_path, prefix=f'{tmp_prefix}{uuid4()}', suffix=tmp_suffix)

        # check that the files are different, but that
        # their parent directories are the same
        if self._dst_path == self._tmp_path:
            raise ValueError(f'temporary and destination files are the same: {self._tmp_path} == {self._dst_path}')
        if self._dst_path.parent != self._tmp_path.parent:
            raise ValueError(f'temporary and destination directories are not same: {self._tmp_path.parent} != {self._dst_path.parent}')

        # other settings
        self._makedirs = makedirs
        self._overwrite = overwrite

    def __enter__(self) -> Union[Path, TextIO, BinaryIO]:
        # check that the temporary file does not already exist
        if self._tmp_path.exists():
            raise RuntimeError(f'the temporary file already exists: {self._tmp_path}, this should never happen.')
        # check that the destination file does not already exist
        if self._dst_path.exists():
            if not self._overwrite:
                raise FileExistsError(f'the destination file already exists: {self._dst_path}, set `overwrite=True` to ignore this error.')
            if not self._dst_path.is_file():
                raise RuntimeError(f'the destination file exists but is not a file: {self._dst_path}')

        # create the missing parent directory if specified
        # and check that this directory actually exists
        if self._makedirs:
            self._tmp_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._tmp_path.parent.is_dir():
            raise NotADirectoryError(f'the parent directory of the temporary file does not exist: {self._tmp_path.parent}, set `makedirs=True` to ignore this error.')

        # handle the different modes
        return self._tmp_path

    def __exit__(self, error_type, error, traceback):
        # cleanup if there was an error, and exit early
        # NOTE: this assumes the user respected creating a file,
        #       a directory won't be removed.
        if error_type is not None:
            if self._tmp_path.exists():
                self._tmp_path.unlink(missing_ok=True)
                LOG.error(f'An error occurred in {self.__class__.__name__}, deleted temporary file: {self._tmp_path}')
            else:
                LOG.error(f'An error occurred in {self.__class__.__name__}')
            return

        # the temp file must have been created at this point
        if not self._tmp_path.exists():
            raise FileNotFoundError(f'the temporary file was not created: {self._tmp_path}')
        if not self._tmp_path.is_file():
            raise RuntimeError(f'the temporary file is not a file: {self._tmp_path}')

        # delete the destination file if it exists and overwrite is enabled:
        # NOTE: this assumes the user respected creating a file,
        #       a directory won't be removed.
        if self._overwrite:
            if self._dst_path.exists():
                LOG.warning(f'overwriting file: {self._dst_path}')
                self._dst_path.unlink(missing_ok=True)

        # create the missing output directories if needed
        if self._makedirs:
            self._dst_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._dst_path.parent.is_dir():
            raise NotADirectoryError(f'the parent directory of the destination file does not exist: {self._dst_path.parent}, set `makedirs=True` to ignore this error.')

        # move the temp file to the destination file
        LOG.info(f'moved temporary file to final location: {self._tmp_path} -> {self._dst_path}')
        os.rename(self._tmp_path, self._dst_path)


class AtomicOpen(object):

    # UNSUPPORTED MODES:
    # 'r': open for reading (default)
    # 'a': open for writing, appending to the end of the file if it exists
    # 'U': universal newlines mode (deprecated)

    # SUPPORTED MODES:
    # 'w': open for writing, truncating the file first
    # 'x': open for exclusive creation, failing if the file already exists

    # SUPPORTED MODIFIERS:
    # 't': text mode (default)
    # '+': open a disk file for updating (reading and writing)
    # 'b': binary mode

    def __init__(
        self,
        file: Union[str, Path],
        mode: str = 'x',
        makedirs: bool = False,
        tmp_prefix: Optional[str] = '.temp.',
        tmp_suffix: Optional[str] = None,
    ):
        # set the overwrite mode based on `x` or `w`
        if "x" in mode:
            overwrite, copy_orig = False, False
        elif "w" in mode:
            overwrite, copy_orig = True, False
        elif "a" in mode:
            overwrite, copy_orig = True, True
            raise NotImplementedError('mode "a" is unsupported')
        elif "r" in mode:
            overwrite, copy_orig = False, True
            raise NotImplementedError('mode "r" is unsupported')
        else:
            raise ValueError(f'the mode: {repr(mode)} is invalid')

        # standard path context manager
        self._atomic_path = AtomicPath(
            file=file,
            overwrite=overwrite,
            makedirs=makedirs,
            tmp_prefix=tmp_prefix,
            tmp_suffix=tmp_suffix,
        )

        # resources
        self._open_mode = mode
        self._resource = None

    def __enter__(self):
        # prepare like usual
        tmp_path = self._atomic_path.__enter__()
        # actually create and open the file
        LOG.debug(f'opening temporary file: {tmp_path} with mode: {self._open_mode}')
        self._resource = open(tmp_path, self._open_mode)
        return self._resource

    def __exit__(self, error_type, error, traceback):
        # close the temp file
        try:
            self._resource.close()
        finally:
            self._resource = None
        # cleanup like usual
        self._atomic_path.__exit__(error_type, error, traceback)


# ========================================================================= #
# export                                                                    #
# ========================================================================= #


__all__ = (
    'AtomicPath',
    'AtomicOpen',
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
