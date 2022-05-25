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

import itertools
import tempfile
from contextlib import contextmanager
from contextlib import nullcontext
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import pytest

import doorway._hash
from doorway._hash import hash_mode_get
from doorway._hash import hash_mode_set_default
from doorway._hash import hash_algo_get
from doorway._hash import hash_algo_set_default
from doorway._utils import VarHandlerStr
from tests.util import temp_attr
from tests.util import temp_environ


# ========================================================================= #
# TEST UTILS                                                                #
# ========================================================================= #


@contextmanager
def context_temp_hash_mode_fallback(hash_mode: Optional[str]):
    with nullcontext() if (not hash_mode) else temp_attr(doorway._hash._VAR_HANDLER_HASH_MODE, '_value_fallback', hash_mode):
        yield

@contextmanager
def context_temp_hash_mode_environ(hash_mode: Optional[str]):
    with nullcontext() if (not hash_mode) else temp_environ(DOORWAY_HASH_MODE=hash_mode):
        yield

@contextmanager
def context_temp_hash_algo_environ(hash_algo: Optional[str]):
    with nullcontext() if (not hash_algo) else temp_environ(DOORWAY_HASH_ALGO=hash_algo):
        yield

@contextmanager
def context_temp_hash_mode_default(hash_mode: Optional[str]):
    with nullcontext() if (not hash_mode) else temp_attr(doorway._hash._VAR_HANDLER_HASH_MODE, '_value_default', hash_mode):
        yield


# ========================================================================= #
# TEST VAR HANDLER                                                          #
# ========================================================================= #


INVALID = 'INVL'


def _get_params():
    params = itertools.product(
        ['full', 'fast', INVALID, None],
        ['full', 'fast', INVALID, None],
        ['full', 'fast', INVALID, None],
        ['full', 'fast', INVALID],
    )
    for row in params:
        row = list(row)
        target, source = next((t, s) for t, s in zip(row, ['manual', 'default', 'environment', 'fallback']) if t)
        yield *reversed(row), target, source


@pytest.mark.parametrize(
    ('fallback', 'environ', 'default', 'manual', 'target', 'source'),
    _get_params(),
)
def test_get_hash_mode(fallback: str, environ: str, default: str, manual: str, target: str, source: str):
    # check initial
    assert hash_mode_get() == 'fast'
    # forcefully set the fallback, environ, and defaults
    with context_temp_hash_mode_fallback(fallback):
        with context_temp_hash_mode_environ(environ):
            with context_temp_hash_mode_default(default):
                # handle the different cases
                if target != INVALID:
                    assert hash_mode_get(manual) == target
                    assert hash_mode_get('full') == 'full'
                    assert hash_mode_get('fast') == 'fast'
                    with pytest.raises(KeyError, match=f"invalid hash_mode: '{INVALID}', obtained from source: manual"):
                        hash_mode_get(INVALID)
                    assert hash_mode_get(manual) == target
                else:
                    with pytest.raises(KeyError, match=f"invalid hash_mode: '{INVALID}', obtained from source: {source}"):
                        hash_mode_get(INVALID if (source == 'manual') else None)
    # check restored
    assert hash_mode_get() == 'fast'


def test_hash_mode_set_default():
    assert hash_mode_get() == 'fast'
    hash_mode_set_default('full')
    assert hash_mode_get() == 'full'
    hash_mode_set_default('fast')
    assert hash_mode_get() == 'fast'
    # check that environ doesnt overwrite & that setting to null resets
    with context_temp_hash_mode_environ('full'):
        assert hash_mode_get() == 'fast'
        hash_mode_set_default(None)
        assert hash_mode_get() == 'full'
    assert hash_mode_get() == 'fast'
    # check invalid
    with pytest.raises(KeyError, match="invalid hash_mode: \'INVALID\', obtained from source: set_default_value, must be one of the allowed_values: \['fast', 'full'\]"):
        hash_mode_set_default('INVALID')


def test_hash_algo_set_default():
    assert hash_algo_get() == 'md5'
    hash_algo_set_default('sha1')
    assert hash_algo_get() == 'sha1'
    hash_algo_set_default('md5')
    assert hash_algo_get() == 'md5'
    # check that environ doesnt overwrite & that setting to null resets
    with context_temp_hash_algo_environ('sha1'):
        assert hash_algo_get() == 'md5'
        hash_algo_set_default(None)
        assert hash_algo_get() == 'sha1'
    assert hash_algo_get() == 'md5'
    # check invalid
    with pytest.raises(KeyError, match="invalid hash_algo: 'INVALID', obtained from source: set_default_value, must be one of the allowed_values:"):
        hash_algo_set_default('INVALID')


def test_hash_norm():
    assert doorway.hash_norm('???') == '???'
    assert doorway.hash_norm({'fast:md5': 'fast:md5', 'fast': 'fast', 'md5': 'md5'}) == 'fast:md5'
    assert doorway.hash_norm({'fast:md5': 'fast:md5', 'fast': 'fast'              }) == 'fast:md5'
    assert doorway.hash_norm({'fast:md5': 'fast:md5',                 'md5': 'md5'}) == 'fast:md5'
    assert doorway.hash_norm({'fast:md5': 'fast:md5'                              }) == 'fast:md5'
    assert doorway.hash_norm({                        'fast': 'fast', 'md5': 'md5'}) == 'fast'
    assert doorway.hash_norm({                        'fast': 'fast'              }) == 'fast'
    assert doorway.hash_norm({                                        'md5': 'md5'}) == 'md5'
    with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \[\]"):
        assert doorway.hash_norm({})
    # check overrides 1.
    assert doorway.hash_norm({'fast:md5': 'fast:md5'}, hash_mode=None, hash_algo=None) == 'fast:md5'
    assert doorway.hash_norm({'fast':     'fast'},     hash_mode=None, hash_algo=None) == 'fast'
    assert doorway.hash_norm({'md5':      'md5'},      hash_mode=None, hash_algo=None) == 'md5'
    with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \['invalid'\]"):
        doorway.hash_norm({'invalid': 'invalid'},              hash_mode=None, hash_algo=None)
    # check overrides 2.
    assert doorway.hash_norm({'full:md5': 'full:md5'}, hash_mode='full', hash_algo=None) == 'full:md5'
    assert doorway.hash_norm({'full':     'full'},     hash_mode='full', hash_algo=None) == 'full'
    assert doorway.hash_norm({'md5':      'md5'},      hash_mode='full', hash_algo=None) == 'md5'
    with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'full:md5', 2. 'full', or 3. 'md5'. Available hash keys are: \['invalid'\]"):
        doorway.hash_norm({'invalid': 'invalid'},              hash_mode='full', hash_algo=None)
    # check overrides 3.
    assert doorway.hash_norm({'fast:sha1': 'fast:sha1'}, hash_mode=None, hash_algo='sha1') == 'fast:sha1'
    assert doorway.hash_norm({'fast':      'fast'},      hash_mode=None, hash_algo='sha1') == 'fast'
    assert doorway.hash_norm({'sha1':      'sha1'},      hash_mode=None, hash_algo='sha1') == 'sha1'
    with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'fast:sha1', 2. 'fast', or 3. 'sha1'. Available hash keys are: \['invalid'\]"):
        doorway.hash_norm({'invalid': 'invalid'},                hash_mode=None, hash_algo='sha1')
    # check overrides 4.
    assert doorway.hash_norm({'full:sha1': 'full:sha1'}, hash_mode='full', hash_algo='sha1') == 'full:sha1'
    assert doorway.hash_norm({'full':      'full'},      hash_mode='full', hash_algo='sha1') == 'full'
    assert doorway.hash_norm({'sha1':      'sha1'},      hash_mode='full', hash_algo='sha1') == 'sha1'
    with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'full:sha1', 2. 'full', or 3. 'sha1'. Available hash keys are: \['invalid'\]"):
        doorway.hash_norm({'invalid': 'invalid'},                hash_mode='full', hash_algo='sha1')


def test_hash_norm_invalid():
    with pytest.raises(TypeError, match="normalized hash should be a str, got type: <class 'NoneType'> for value: None"):
        assert doorway.hash_norm(None)
    with pytest.raises(TypeError, match="normalized hash should be a str, got type: <class 'int'> for value: 1"):
        assert doorway.hash_norm(1)
    with pytest.raises(TypeError, match="normalized hash should be a str, got type: <class 'NoneType'> for value: None"):
        assert doorway.hash_norm({'fast:md5': None})
    with pytest.raises(TypeError, match="normalized hash should be a str, got type: <class 'int'> for value: 1"):
        assert doorway.hash_norm({'fast:md5': 1})

# ========================================================================= #
# TEST HASHING - HELPER                                                     #
# ========================================================================= #


def _make_sequential_file(file, length: int = 100_000):
    context = open(file, 'w') if isinstance(file, (str, Path)) else nullcontext(file)
    # insert lines into the file
    with context as fp:
        for i in range(length):
            fp.write(f'{i}\n')
    fp.seek(0)
    return fp


# ========================================================================= #
# TEST HASHING                                                              #
# ========================================================================= #


def test_hash_file_dir():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(IsADirectoryError, match='the path exists but is not a file:'):
            doorway.hash_file(d, hash_algo='md5', hash_mode='fast', hash_missing=False)
    with pytest.raises(FileNotFoundError, match='could not compute hash for missing file:'):
        doorway.hash_file(d, hash_algo='md5', hash_mode='fast', hash_missing=False)


def test_hash_file():
    with NamedTemporaryFile('w') as fp:
        fp = _make_sequential_file(fp, 1_000_000)
        # hash the file, checking default vars
        assert doorway.hash_file(fp.name)                                                      == 'f71b9a144c7a67c43999103f34c5a0ef'
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode=None, hash_missing=False) == 'f71b9a144c7a67c43999103f34c5a0ef'
        with context_temp_hash_mode_default('full'):
            assert doorway.hash_file(fp.name)                                                  == '762251ff53a76f10ada68131f8e3d4c1'
        # hash the file checking explicit modes
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='fast', hash_missing=False) == 'f71b9a144c7a67c43999103f34c5a0ef'
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='full', hash_missing=False) == '762251ff53a76f10ada68131f8e3d4c1'
        # hash the file checking explicit types -- might be an idea to swap to sha256 by default instead?
        assert doorway.hash_file(fp.name, hash_algo='sha1',   hash_mode='fast', hash_missing=False) == 'c1ae8652e374a052493c1d7faae28f41c139c87c'
        assert doorway.hash_file(fp.name, hash_algo='sha1',   hash_mode='full', hash_missing=False) == '5e174204d2aae9c9adf7e11b2184f36a56730230'
        assert doorway.hash_file(fp.name, hash_algo='sha256', hash_mode='fast', hash_missing=False) == 'b0cab88abcf70e9cf2fac9db6eccf0141c818ded4888880936169b7f88b37fa6'
        assert doorway.hash_file(fp.name, hash_algo='sha256', hash_mode='full', hash_missing=False) == '7b8f269ab1f1ba01ea1cb69d69eb2abdd98b88311ce896f1083cc9e66112988b'
        assert doorway.hash_file(fp.name, hash_algo='sha512', hash_mode='fast', hash_missing=False) == 'c3e92e686f010bed0b9fcf404e87fea6fb049bae6bb2b2a12c0d45c0b686caa39c91f2e6d792731d70393f07757e2ce1753be175dae287fa991b5c23e2d7ae69'
        assert doorway.hash_file(fp.name, hash_algo='sha512', hash_mode='full', hash_missing=False) == 'b1ad0bfbe6a5560623fc66926ec63a3c11856f505bdbdd713a608d18bbb32b1aaa7260d91558cdf1cb8bd5bc3e539c51b25badd8bf3229f2a9906dbdcb29c7d5'
    # test missing files
    with pytest.raises(FileNotFoundError, match='could not compute hash for missing file'):
        doorway.hash_file(fp.name)
    with pytest.raises(FileNotFoundError, match='could not compute hash for missing file'):
        doorway.hash_file(fp.name, hash_algo='md5', hash_mode='fast', hash_missing=False)
    assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='fast', hash_missing=True) == ''



def test_hash_file_small():
    # check tiny file
    with NamedTemporaryFile('w') as fp:
        fp = _make_sequential_file(fp, 100)
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='fast', hash_missing=False) == '40f6ddb8db1f93ad1f5502e2e0321f2f'
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='full', hash_missing=False) == '9a10f4f09341c2db76a16b44f841c551'
    # check mini file
    with NamedTemporaryFile('w') as fp:
        fp = _make_sequential_file(fp, 1000)
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='fast', hash_missing=False) == 'c8902cdef4e5ad7c0b59784ebe454aa9'
        assert doorway.hash_file(fp.name, hash_algo='md5', hash_mode='full', hash_missing=False) == 'b6f42041b389b22d1fb65ec3f1307ccd'


def test_hash_file_validate():
    hashs_md5 = {
        'fast':  'f71b9a144c7a67c43999103f34c5a0ef',
        'full':  '762251ff53a76f10ada68131f8e3d4c1',
    }
    hashs_sha1 = {
        'fast':  'c1ae8652e374a052493c1d7faae28f41c139c87c',
        'full':  '5e174204d2aae9c9adf7e11b2184f36a56730230',
    }
    # get hashes
    with NamedTemporaryFile('w') as fp:
        fp = _make_sequential_file(fp, 1_000_000)
        # check validation of file
        doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'])
        doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'], hash_algo='md5', hash_mode='fast', hash_missing=False)
        # check hash dictionaries
        doorway.hash_file_validate(fp.name, hash=hashs_md5,         hash_algo='md5', hash_mode='fast', hash_missing=False)
        doorway.hash_file_validate(fp.name, hash=hashs_md5,         hash_algo='md5', hash_mode='full', hash_missing=False)
        # sha1
        doorway.hash_file_validate(fp.name, hash=hashs_sha1,        hash_algo='sha1', hash_mode='fast', hash_missing=False)
        doorway.hash_file_validate(fp.name, hash=hashs_sha1,        hash_algo='sha1', hash_mode='full', hash_missing=False)
        # check changing hash mode
        with context_temp_hash_mode_default('full'):
            doorway.hash_file_validate(fp.name, hash=hashs_md5['full'])
            with pytest.raises(doorway.HashError, match="computed full md5 hash: '762251ff53a76f10ada68131f8e3d4c1' does not match expected hash: 'f71b9a144c7a67c43999103f34c5a0ef' for file:"):
                doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'])
        # check changing hash mode
        with context_temp_hash_mode_default('fast'):
            doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'])
            with pytest.raises(doorway.HashError, match="computed fast md5 hash: 'f71b9a144c7a67c43999103f34c5a0ef' does not match expected hash: '762251ff53a76f10ada68131f8e3d4c1' for file:"):
                doorway.hash_file_validate(fp.name, hash=hashs_md5['full'])
        # check invalid hash
        with pytest.raises(doorway.HashError, match="computed fast md5 hash: 'f71b9a144c7a67c43999103f34c5a0ef' does not match expected hash: '<invalid>' for file:"):
            doorway.hash_file_validate(fp.name, hash='<invalid>', hash_algo='md5')
        # check missing hash
        with pytest.raises(KeyError, match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \[\]"):
            doorway.hash_file_validate(fp.name, hash={}, hash_algo='md5')
        # check is valid
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5,         hash_missing=False) == True
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['fast'], hash_missing=False) == True
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['full'], hash_missing=False) == False
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5,         hash_missing=True)  == True
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['fast'], hash_missing=True)  == True
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['full'], hash_missing=True)  == False
    # missing file
    with pytest.raises(FileNotFoundError, match="could not compute hash for missing file:"):
        doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'], hash_missing=False)
    with pytest.raises(doorway.HashError, match="computed fast md5 hash: '' does not match expected hash: 'f71b9a144c7a67c43999103f34c5a0ef' for file:"):
        doorway.hash_file_validate(fp.name, hash=hashs_md5['fast'], hash_missing=True)
    # missing file
    with pytest.raises(FileNotFoundError, match="could not compute hash for missing file:"):
        doorway.hash_file_is_valid(fp.name, hash=hashs_md5, hash_missing=False)
    assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5,         hash_missing=True) == False
    assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['fast'], hash_missing=True) == False
    assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5['full'], hash_missing=True) == False


# ========================================================================= #
# Variable Handler                                                          #
# ========================================================================= #


def test_variable_handler():
    handler = VarHandlerStr(
        identifier='var_handler',
        environ_key='VAR_HANDLER',
        fallback_value='1',
        allowed_values=('2', '1', '3'),
    )
    assert handler.environ_key == 'VAR_HANDLER'
    assert handler.fallback_value == '1'
    assert handler.allowed_values == ['1', '2', '3']
    # environ values
    assert handler.get_value() == '1'
    with temp_environ(VAR_HANDLER='3'):
        assert handler.get_value() == '3'
    assert handler.get_value() == '1'
    # checks
    handler.set_default_value('2')
    assert handler.get_value() == '2'
    handler.set_default_value(None)
    assert handler.get_value() == '1'
    handler.set_default_value('2')
    assert handler.get_value() == '2'
    handler.del_default_value()
    assert handler.get_value() == '1'


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
