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
from doorway._hash import hash_algo_get
from doorway._env_vars import EnvVar, EnvVarMissingError, EnvVarValidationError
from doorway._ctx import ctx_temp_attr
from doorway._ctx import ctx_temp_environ


# ========================================================================= #
# TEST UTILS                                                                #
# ========================================================================= #


@contextmanager
def skip_context(value, ctx):
    if value is not None:
        with ctx:
            yield
    else:
        yield


def context_temp_hash_mode_default(
    hash_mode: Optional[str], target=doorway._hash._VAR_HANDLER_HASH_MODE
):
    return skip_context(
        hash_mode, ctx_temp_attr(target, "_persisted_default", hash_mode)
    )


# ========================================================================= #
# TEST VAR HANDLER                                                          #
# ========================================================================= #


INVALID = "<INVALID>"


@pytest.mark.parametrize(
    ("usr_override", "cls_override", "environ", "usr_default", "cls_default"),
    itertools.product(
        ["a", INVALID, None],  # usr_override
        ["b", INVALID, None],  # cls_override
        ["c", INVALID, None],  # environ
        ["d", INVALID, None],  # usr_default
        ["e", INVALID, None],  # cls_default
    ),
)
def test_get_hash_mode(
    usr_override: str,
    cls_override: str,
    environ: str,
    usr_default: str,
    cls_default: str,
):
    # forcefully set the fallback, environ, and defaults
    with skip_context(environ, ctx_temp_environ(ASDF_FDSA=environ)):
        env_var = EnvVar.env_str(
            key="ASDF_FDSA",
            validator=EnvVar.validator_allowed(["a", "b", "c", "d", "e"]),
        )
        env_var.set_default_value(cls_default)
        env_var.set_override_value(cls_override)
        # now get
        values = [usr_override, cls_override, environ, usr_default, cls_default]
        first = next((v for v in values if v is not None), None)

        if first is None:
            with pytest.raises(EnvVarMissingError):
                env_var.get(default=usr_default, override=usr_override)
        elif first == INVALID:
            with pytest.raises(EnvVarValidationError):
                env_var.get(default=usr_default, override=usr_override)
        else:
            assert env_var.get(default=usr_default, override=usr_override) == first


def test_hash_mode_set_default():
    assert hash_mode_get() == "fast"
    # check that environ doesnt overwrite & that setting to null resets
    with ctx_temp_environ(DOORWAY_HASH_MODE="full"):
        assert hash_mode_get() == "full"
    assert hash_mode_get() == "fast"
    # check invalid
    with ctx_temp_environ(DOORWAY_HASH_MODE="INVALID"):
        with pytest.raises(EnvVarValidationError):
            hash_mode_get()


def test_hash_algo_set_default():
    assert hash_algo_get() == "md5"
    # check that environ doesnt overwrite & that setting to null resets
    with ctx_temp_environ(DOORWAY_HASH_ALGO="sha1"):
        assert hash_algo_get() == "sha1"
    assert hash_algo_get() == "md5"
    # check invalid
    with ctx_temp_environ(DOORWAY_HASH_ALGO="INVALID"):
        with pytest.raises(EnvVarValidationError):
            hash_algo_get()


def test_hash_norm():
    assert doorway.hash_norm("???") == "???"
    assert (
        doorway.hash_norm({"fast:md5": "fast:md5", "fast": "fast", "md5": "md5"})
        == "fast:md5"
    )
    assert doorway.hash_norm({"fast:md5": "fast:md5", "fast": "fast"}) == "fast:md5"
    assert doorway.hash_norm({"fast:md5": "fast:md5", "md5": "md5"}) == "fast:md5"
    assert doorway.hash_norm({"fast:md5": "fast:md5"}) == "fast:md5"
    assert doorway.hash_norm({"fast": "fast", "md5": "md5"}) == "fast"
    assert doorway.hash_norm({"fast": "fast"}) == "fast"
    assert doorway.hash_norm({"md5": "md5"}) == "md5"
    with pytest.raises(
        KeyError,
        match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \\[\\]",
    ):
        assert doorway.hash_norm({})
    # check overrides 1.
    assert (
        doorway.hash_norm({"fast:md5": "fast:md5"}, hash_mode=None, hash_algo=None)
        == "fast:md5"
    )
    assert doorway.hash_norm({"fast": "fast"}, hash_mode=None, hash_algo=None) == "fast"
    assert doorway.hash_norm({"md5": "md5"}, hash_mode=None, hash_algo=None) == "md5"
    with pytest.raises(
        KeyError,
        match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \\['invalid'\\]",
    ):
        doorway.hash_norm({"invalid": "invalid"}, hash_mode=None, hash_algo=None)
    # check overrides 2.
    assert (
        doorway.hash_norm({"full:md5": "full:md5"}, hash_mode="full", hash_algo=None)
        == "full:md5"
    )
    assert (
        doorway.hash_norm({"full": "full"}, hash_mode="full", hash_algo=None) == "full"
    )
    assert doorway.hash_norm({"md5": "md5"}, hash_mode="full", hash_algo=None) == "md5"
    with pytest.raises(
        KeyError,
        match="hash dictionary does not contain a valid key for either 1. 'full:md5', 2. 'full', or 3. 'md5'. Available hash keys are: \\['invalid'\\]",
    ):
        doorway.hash_norm({"invalid": "invalid"}, hash_mode="full", hash_algo=None)
    # check overrides 3.
    assert (
        doorway.hash_norm({"fast:sha1": "fast:sha1"}, hash_mode=None, hash_algo="sha1")
        == "fast:sha1"
    )
    assert (
        doorway.hash_norm({"fast": "fast"}, hash_mode=None, hash_algo="sha1") == "fast"
    )
    assert (
        doorway.hash_norm({"sha1": "sha1"}, hash_mode=None, hash_algo="sha1") == "sha1"
    )
    with pytest.raises(
        KeyError,
        match="hash dictionary does not contain a valid key for either 1. 'fast:sha1', 2. 'fast', or 3. 'sha1'. Available hash keys are: \\['invalid'\\]",
    ):
        doorway.hash_norm({"invalid": "invalid"}, hash_mode=None, hash_algo="sha1")
    # check overrides 4.
    assert (
        doorway.hash_norm(
            {"full:sha1": "full:sha1"}, hash_mode="full", hash_algo="sha1"
        )
        == "full:sha1"
    )
    assert (
        doorway.hash_norm({"full": "full"}, hash_mode="full", hash_algo="sha1")
        == "full"
    )
    assert (
        doorway.hash_norm({"sha1": "sha1"}, hash_mode="full", hash_algo="sha1")
        == "sha1"
    )
    with pytest.raises(
        KeyError,
        match="hash dictionary does not contain a valid key for either 1. 'full:sha1', 2. 'full', or 3. 'sha1'. Available hash keys are: \\['invalid'\\]",
    ):
        doorway.hash_norm({"invalid": "invalid"}, hash_mode="full", hash_algo="sha1")


def test_hash_norm_invalid():
    with pytest.raises(
        TypeError,
        match="normalized hash should be a str, got type: <class 'NoneType'> for value: None",
    ):
        assert doorway.hash_norm(None)
    with pytest.raises(
        TypeError,
        match="normalized hash should be a str, got type: <class 'int'> for value: 1",
    ):
        assert doorway.hash_norm(1)
    with pytest.raises(
        TypeError,
        match="normalized hash should be a str, got type: <class 'NoneType'> for value: None",
    ):
        assert doorway.hash_norm({"fast:md5": None})
    with pytest.raises(
        TypeError,
        match="normalized hash should be a str, got type: <class 'int'> for value: 1",
    ):
        assert doorway.hash_norm({"fast:md5": 1})


# ========================================================================= #
# TEST HASHING - HELPER                                                     #
# ========================================================================= #


def _make_sequential_file(file, length: int = 100_000):
    context = open(file, "w") if isinstance(file, (str, Path)) else nullcontext(file)
    # insert lines into the file
    with context as fp:
        for i in range(length):
            fp.write(f"{i}\n")
    fp.seek(0)
    return fp


# ========================================================================= #
# TEST HASHING                                                              #
# ========================================================================= #


def test_hash_file_dir():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(
            IsADirectoryError, match="the path exists but is not a file:"
        ):
            doorway.hash_file(d, hash_algo="md5", hash_mode="fast", hash_missing=False)
    with pytest.raises(
        FileNotFoundError, match="could not compute hash for missing file:"
    ):
        doorway.hash_file(d, hash_algo="md5", hash_mode="fast", hash_missing=False)


def test_hash_file():
    with NamedTemporaryFile("w") as fp:
        fp = _make_sequential_file(fp, 1_000_000)
        # hash the file, checking default vars
        assert doorway.hash_file(fp.name) == "f71b9a144c7a67c43999103f34c5a0ef"
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode=None, hash_missing=False
            )
            == "f71b9a144c7a67c43999103f34c5a0ef"
        )
        with context_temp_hash_mode_default("full"):
            assert doorway.hash_file(fp.name) == "762251ff53a76f10ada68131f8e3d4c1"
        # hash the file checking explicit modes
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="fast", hash_missing=False
            )
            == "f71b9a144c7a67c43999103f34c5a0ef"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="full", hash_missing=False
            )
            == "762251ff53a76f10ada68131f8e3d4c1"
        )
        # hash the file checking explicit types -- might be an idea to swap to sha256 by default instead?
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha1", hash_mode="fast", hash_missing=False
            )
            == "c1ae8652e374a052493c1d7faae28f41c139c87c"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha1", hash_mode="full", hash_missing=False
            )
            == "5e174204d2aae9c9adf7e11b2184f36a56730230"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha256", hash_mode="fast", hash_missing=False
            )
            == "b0cab88abcf70e9cf2fac9db6eccf0141c818ded4888880936169b7f88b37fa6"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha256", hash_mode="full", hash_missing=False
            )
            == "7b8f269ab1f1ba01ea1cb69d69eb2abdd98b88311ce896f1083cc9e66112988b"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha512", hash_mode="fast", hash_missing=False
            )
            == "c3e92e686f010bed0b9fcf404e87fea6fb049bae6bb2b2a12c0d45c0b686caa39c91f2e6d792731d70393f07757e2ce1753be175dae287fa991b5c23e2d7ae69"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="sha512", hash_mode="full", hash_missing=False
            )
            == "b1ad0bfbe6a5560623fc66926ec63a3c11856f505bdbdd713a608d18bbb32b1aaa7260d91558cdf1cb8bd5bc3e539c51b25badd8bf3229f2a9906dbdcb29c7d5"
        )
    # test missing files
    with pytest.raises(
        FileNotFoundError, match="could not compute hash for missing file"
    ):
        doorway.hash_file(fp.name)
    with pytest.raises(
        FileNotFoundError, match="could not compute hash for missing file"
    ):
        doorway.hash_file(
            fp.name, hash_algo="md5", hash_mode="fast", hash_missing=False
        )
    assert (
        doorway.hash_file(fp.name, hash_algo="md5", hash_mode="fast", hash_missing=True)
        == ""
    )


def test_hash_file_small():
    # check tiny file
    with NamedTemporaryFile("w") as fp:
        fp = _make_sequential_file(fp, 100)
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="fast", hash_missing=False
            )
            == "40f6ddb8db1f93ad1f5502e2e0321f2f"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="full", hash_missing=False
            )
            == "9a10f4f09341c2db76a16b44f841c551"
        )
    # check mini file
    with NamedTemporaryFile("w") as fp:
        fp = _make_sequential_file(fp, 1000)
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="fast", hash_missing=False
            )
            == "c8902cdef4e5ad7c0b59784ebe454aa9"
        )
        assert (
            doorway.hash_file(
                fp.name, hash_algo="md5", hash_mode="full", hash_missing=False
            )
            == "b6f42041b389b22d1fb65ec3f1307ccd"
        )


def test_hash_file_validate():
    hashs_md5 = {
        "fast": "f71b9a144c7a67c43999103f34c5a0ef",
        "full": "762251ff53a76f10ada68131f8e3d4c1",
    }
    hashs_sha1 = {
        "fast": "c1ae8652e374a052493c1d7faae28f41c139c87c",
        "full": "5e174204d2aae9c9adf7e11b2184f36a56730230",
    }
    # get hashes
    with NamedTemporaryFile("w") as fp:
        fp = _make_sequential_file(fp, 1_000_000)
        # check validation of file
        doorway.hash_file_validate(fp.name, hash=hashs_md5["fast"])
        doorway.hash_file_validate(
            fp.name,
            hash=hashs_md5["fast"],
            hash_algo="md5",
            hash_mode="fast",
            hash_missing=False,
        )
        # check hash dictionaries
        doorway.hash_file_validate(
            fp.name,
            hash=hashs_md5,
            hash_algo="md5",
            hash_mode="fast",
            hash_missing=False,
        )
        doorway.hash_file_validate(
            fp.name,
            hash=hashs_md5,
            hash_algo="md5",
            hash_mode="full",
            hash_missing=False,
        )
        # sha1
        doorway.hash_file_validate(
            fp.name,
            hash=hashs_sha1,
            hash_algo="sha1",
            hash_mode="fast",
            hash_missing=False,
        )
        doorway.hash_file_validate(
            fp.name,
            hash=hashs_sha1,
            hash_algo="sha1",
            hash_mode="full",
            hash_missing=False,
        )
        # check changing hash mode
        with context_temp_hash_mode_default("full"):
            doorway.hash_file_validate(fp.name, hash=hashs_md5["full"])
            with pytest.raises(
                doorway.HashError,
                match="computed full md5 hash: '762251ff53a76f10ada68131f8e3d4c1' does not match expected hash: 'f71b9a144c7a67c43999103f34c5a0ef' for file:",
            ):
                doorway.hash_file_validate(fp.name, hash=hashs_md5["fast"])
        # check changing hash mode
        with context_temp_hash_mode_default("fast"):
            doorway.hash_file_validate(fp.name, hash=hashs_md5["fast"])
            with pytest.raises(
                doorway.HashError,
                match="computed fast md5 hash: 'f71b9a144c7a67c43999103f34c5a0ef' does not match expected hash: '762251ff53a76f10ada68131f8e3d4c1' for file:",
            ):
                doorway.hash_file_validate(fp.name, hash=hashs_md5["full"])
        # check invalid hash
        with pytest.raises(
            doorway.HashError,
            match="computed fast md5 hash: 'f71b9a144c7a67c43999103f34c5a0ef' does not match expected hash: '<invalid>' for file:",
        ):
            doorway.hash_file_validate(fp.name, hash="<invalid>", hash_algo="md5")
        # check missing hash
        with pytest.raises(
            KeyError,
            match="hash dictionary does not contain a valid key for either 1. 'fast:md5', 2. 'fast', or 3. 'md5'. Available hash keys are: \[\]",
        ):
            doorway.hash_file_validate(fp.name, hash={}, hash_algo="md5")
        # check is valid
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5, hash_missing=False)
        assert doorway.hash_file_is_valid(
            fp.name, hash=hashs_md5["fast"], hash_missing=False
        )
        assert not doorway.hash_file_is_valid(
            fp.name, hash=hashs_md5["full"], hash_missing=False
        )
        assert doorway.hash_file_is_valid(fp.name, hash=hashs_md5, hash_missing=True)
        assert doorway.hash_file_is_valid(
            fp.name, hash=hashs_md5["fast"], hash_missing=True
        )
        assert not doorway.hash_file_is_valid(
            fp.name, hash=hashs_md5["full"], hash_missing=True
        )
    # missing file
    with pytest.raises(
        FileNotFoundError, match="could not compute hash for missing file:"
    ):
        doorway.hash_file_validate(fp.name, hash=hashs_md5["fast"], hash_missing=False)
    with pytest.raises(
        doorway.HashError,
        match="computed fast md5 hash: '' does not match expected hash: 'f71b9a144c7a67c43999103f34c5a0ef' for file:",
    ):
        doorway.hash_file_validate(fp.name, hash=hashs_md5["fast"], hash_missing=True)
    # missing file
    with pytest.raises(
        FileNotFoundError, match="could not compute hash for missing file:"
    ):
        doorway.hash_file_is_valid(fp.name, hash=hashs_md5, hash_missing=False)
    assert not doorway.hash_file_is_valid(fp.name, hash=hashs_md5, hash_missing=True)
    assert not doorway.hash_file_is_valid(
        fp.name, hash=hashs_md5["fast"], hash_missing=True
    )
    assert not doorway.hash_file_is_valid(
        fp.name, hash=hashs_md5["full"], hash_missing=True
    )


# ========================================================================= #
# Variable Handler                                                          #
# ========================================================================= #


def test_variable_handler():
    handler = EnvVar.env_str(
        key="VAR_HANDLER",
        default="1",
        validator=EnvVar.validator_allowed(["1", "2", "3"]),
    )
    assert handler.env_key == "VAR_HANDLER"
    # environ values
    assert handler.get() == "1"
    with ctx_temp_environ(VAR_HANDLER="3"):
        assert handler.get() == "3"
    assert handler.get() == "1"

    # checks
    handler.set_default_value("2")
    assert handler.get() == "2"
    handler.set_default_value("2")
    assert handler.get() == "2"

    handler.set_default_value(None)
    with pytest.raises(EnvVarMissingError):
        handler.get()


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
