
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
import shutil
from pathlib import Path
from typing import BinaryIO
from typing import TextIO
from typing import Union

from doorway._modify_path import path_basename_modify


LOG = logging.getLogger(__name__)


# ========================================================================= #
# Atomic file saving                                                        #
# ========================================================================= #


_MODE_REPLACE = 'w'
_MODE_MISSING = 'x'
_MODE_TRY_COPY = 'a'
_MODE_EXISTING = 'r+'


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
            f.write('hello world!\n')
    ```
    """

    # +----------------+-----+-----+-----+-----+-----+-----+-----+-----+
    # | DESCRIPTION    |  r  |  r+ |  w  |  w+ |  a  |  a+ |  x  |  x+ |
    # |----------------+-----+-----+-----+-----+-----+-----+-----+-----|
    # | read           |  *  |  *  |     |  *  |     |  *  |     |  *  |
    # | write          |     |  *  |  *  |  *  |  *  |  *  |  *  |  *  |
    # |----------------+-----+-----+-----+-----+-----+-----+-----+-----|
    # | create         |     |     |  *  |  *  |  *  |  *  |  *  |  *  |
    # | truncate       |     |     |  *  |  *  |     |     |  O  |  O  |
    # |----------------+-----+-----+-----+-----+-----+-----+-----+-----|
    # | must exist     |  *  |  *  |     |     |     |     |     |     |
    # | overwrite      |     |     |  *  |  *  |     |     |     |     |
    # | append         |     |     |     |     |  *  |  *  |     |     |
    # | must not exist |     |     |     |     |     |     |  *  |  *  |
    # |----------------+-----+-----+-----+-----+-----+-----+-----+-----|
    # | seek to start  |  *  |  *  |  *  |  *  |     |     |  *  |  *  |
    # | seek to end    |     |     |     |     |  *  |  *  |     |     |
    # |----------------+-----+-----+-----+-----+-----+-----+-----+-----|
    # | O: special case, must not exist, so truncated by default       |
    # +----------------------------------------------------------------+

    # SUPPORTED MODES:
    # 'r' : overwrite, assert temp file created in context and then move to destination
    #     | like open(..., 'w'): write which truncates the file
    # 'x' : exclusive, assert temp file created in context but fail if dest. exists
    #     | like open(..., 'x'): exclusive create which fails if the file already exists
    # 'a' : append, copy data to temp file if it exists, then move back to destination
    #     | like open(..., 'a'): append which appends to end of file if it exists
    # 'r+': required, copy data to temp file, then move back to destination
    #     | like open(..., 'r+'): read which requires the file to exist

    # UNSUPPORTED MODES:
    # 'r': open for reading
    # 'U': universal newlines mode

    def __init__(
        self,
        file: Union[str, Path],
        mode: str = _MODE_MISSING,
        makedirs: bool = False,
    ):
        # check files
        if (not file) or Path(file).name in ('', '.', '..'):
            raise ValueError(f'file must not be empty: {repr(file)}')

        # check the mode
        if mode not in (_MODE_TRY_COPY, _MODE_REPLACE, _MODE_MISSING, _MODE_EXISTING):
            raise ValueError(
                f'invalid mode: {repr(mode)}, '
                f'must be one of: {_MODE_TRY_COPY}/{_MODE_REPLACE}/{_MODE_MISSING}/{_MODE_EXISTING} (try_copy/replace/missing/existing)'
            )

        # get the actual files
        from uuid import uuid4
        self._dst_path = Path(file).absolute()
        self._tmp_path = path_basename_modify(
            file=self._dst_path,
            basename_prefix=f'.temp.{uuid4()}.',
        )

        # check that the files are different, but that
        # their parent directories are the same
        if self._dst_path == self._tmp_path:
            raise ValueError(f'temporary and destination files are the same: {self._tmp_path} == {self._dst_path}')
        if self._dst_path.parent != self._tmp_path.parent:
            raise ValueError(f'temporary and destination directories are not same: {self._tmp_path.parent} != {self._dst_path.parent}')

        # other settings
        self._makedirs = makedirs
        self._mode = mode

    def __enter__(self) -> Path:
        # 1. check that the temporary file does not already exist
        #    this should be impossible
        if self._tmp_path.exists():
            raise RuntimeError(f'the temporary file already exists: {self._tmp_path}, this is a bug!')

        # 2. handle the different modes for when the destination file exists
        # - make sure the destination does not exist
        if self._mode == _MODE_MISSING:
            if self._dst_path.exists():
                raise FileExistsError(f'the destination file should not exist: {self._dst_path}')
        # - make sure the destination can be replaced
        elif self._mode == _MODE_REPLACE:
            if self._dst_path.exists():
                if not self._dst_path.is_file():
                    raise IsADirectoryError(f'the destination file exists but is not a file: {self._dst_path}')
        # - make sure the destination can be replaced and try copy it
        elif self._mode in (_MODE_REPLACE, _MODE_TRY_COPY, _MODE_EXISTING):
            if self._dst_path.exists():
                if not self._dst_path.is_file():
                    raise IsADirectoryError(f'the destination file exists but is not a file: {self._dst_path}')
                shutil.copy(self._dst_path, self._tmp_path)
        # - make sure the destination exists, can be replaced and copy it
        elif self._mode == _MODE_EXISTING:
            if not self._dst_path.exists():
                raise FileExistsError(f'the destination file should exist: {self._dst_path}')
            elif not self._dst_path.is_file():
                raise FileExistsError(f'the destination file exists but is not a file: {self._dst_path}')
            shutil.copy(self._dst_path, self._tmp_path)
        # - make sure the mode is valid
        else:
            raise NotImplementedError(f'invalid mode: {self._mode}, this is a bug!')

        # 3. create the missing parent directory if specified
        if self._makedirs:
            self._tmp_path.parent.mkdir(parents=True, exist_ok=True)

        # return the path to the temp file
        return self._tmp_path

    def __exit__(self, error_type, error, traceback):
        # 0. cleanup if there was an error, and exit early
        if error_type is not None:
            if self._tmp_path.exists():
                if self._tmp_path.is_dir():
                    raise RuntimeError(f'An error occured in {self.__class__.__name__}, but could not clean up the temporary file because it is a directory: {self._tmp_path}')
                self._tmp_path.unlink(missing_ok=True)
                LOG.error(f'An error occurred in {self.__class__.__name__}, deleted temporary file: {self._tmp_path}')
            else:
                LOG.error(f'An error occurred in {self.__class__.__name__}')
            return

        # 1. check that the temporary file was created in this context
        if not self._tmp_path.exists():
            raise FileNotFoundError(f'the temporary file was not created: {self._tmp_path}')
        if not self._tmp_path.is_file():
            raise RuntimeError(f'the temporary file is not a file: {self._tmp_path}')

        # 2. handle the different modes, we perform some checks again just to be safe
        # - make sure the destination does not exist
        if self._mode == _MODE_MISSING:
            if self._dst_path.exists():
                raise FileExistsError(f'the destination file should not exist: {self._dst_path}')
        # - no checks needed
        elif self._mode in (_MODE_REPLACE, _MODE_TRY_COPY, _MODE_EXISTING):
            pass
        # - make sure the mode is valid
        else:
            raise NotImplementedError(f'invalid mode: {self._mode}, this is a bug!')

        # 3. move the temp file to the destination file. `os.rename` is usually
        # guaranteed to be atomic on linux and also overwrites the destination path
        LOG.info(f'moving temporary file to final location: {self._tmp_path} -> {self._dst_path}')
        os.rename(self._tmp_path, self._dst_path)


class AtomicOpen(object):

    # SUPPORTED MODES:
    # 'r': open for reading (default)
    # 'a': open for writing, appending to the end of the file if it exists
    # 'w': open for writing, truncating the file first
    # 'x': open for exclusive creation, failing if the file already exists

    # SUPPORTED MODIFIERS:
    # 't': text mode (default)
    # '+': open a disk file for updating (reading and writing)
    # 'b': binary mode

    # UNSUPPORTED MODES:
    # 'U': universal newlines mode (deprecated)

    def __init__(
        self,
        file: Union[str, Path],
        mode: str = 'x',
        makedirs: bool = False,
    ):
        # obtain the basic mode from the actual mode
        if 'r' in mode:
            basic_mode = _MODE_EXISTING if ('+' in mode) else None
        elif 'x' in mode:
            basic_mode = _MODE_MISSING
        elif 'w' in mode:
            basic_mode = _MODE_REPLACE
        elif 'a' in mode:
            basic_mode = _MODE_TRY_COPY
        else:
            raise ValueError(f'invalid mode: {repr(mode)}, must contain: r/x/w/a')

        # set the class vars
        self._open_mode = mode
        self._file_io = None
        self._orig_path = file

        # handle the different basic modes
        if basic_mode is None:
            self._atomic_path = None
        else:
            self._atomic_path = AtomicPath(
                file=file,
                mode=basic_mode,
                makedirs=makedirs,
            )

    def __enter__(self) -> Union[TextIO, BinaryIO]:
        # - we should be in read-only mode
        if self._atomic_path is None:
            tmp_path = self._orig_path
            LOG.debug(f'opening original file: {tmp_path} with mode: {self._open_mode}')
        # - prepare like usual
        else:
            tmp_path = self._atomic_path.__enter__()
            LOG.debug(f'opening temporary file: {tmp_path} with mode: {self._open_mode}')

        # open and return the file
        self._file_io = open(tmp_path, self._open_mode)
        return self._file_io

    def __exit__(self, error_type, error, traceback):
        # close the temp file
        try:
            self._file_io.close()
        finally:
            self._file_io = None
        # cleanup like usual if we are not in read-only mode
        if self._atomic_path is not None:
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
