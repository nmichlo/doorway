
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

import os
import sys
import contextlib
from typing import Any
from typing import Dict


# ========================================================================= #
# context managers -- io streams                                            #
# ========================================================================= #


@contextlib.contextmanager
def ctx_no_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout = old_stdout


@contextlib.contextmanager
def ctx_no_stderr():
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stderr = old_stderr


# ========================================================================= #
# context managers -- attr                                                  #
# ========================================================================= #


_DELETE = object()


@contextlib.contextmanager
def ctx_temp_attr(obj, name, value):
    # if we should delete this or just reset it
    prev_val = getattr(obj, name, _DELETE)
    # overwrite the value
    setattr(obj, name, value)
    # yield the context
    try:
        yield obj
    finally:
        # restore the original attr
        if prev_val is _DELETE:
            delattr(obj, name)
        else:
            setattr(obj, name, prev_val)


# ========================================================================= #
# context managers -- working dir, args, env                                #
# ========================================================================= #


@contextlib.contextmanager
def ctx_temp_wd(new_wd):
    old_wd = os.getcwd()
    os.chdir(new_wd)
    try:
        yield
    finally:
        os.chdir(old_wd)


@contextlib.contextmanager
def ctx_temp_sys_args(new_argv):
    old_argv = sys.argv
    sys.argv = new_argv
    try:
        yield
    finally:
        sys.argv = old_argv


@contextlib.contextmanager
def ctx_temp_environ(environment: Dict[str, Any] = None, **env_kwargs):
    # combine the kwargs and the environment dict
    if environment is None:
        environment = {}
    if env_kwargs:
        assert environment.keys().isdisjoint(env_kwargs.keys())
        environment.update(env_kwargs)
    # save the old environment
    old_env = {}
    for k in environment:
        if k in os.environ:
            old_env[k] = os.environ[k]
    # update the environment
    os.environ.update(environment)
    # run the context
    try:
        yield
    finally:
        # restore the original environment
        for k in environment:
            if k in old_env:
                os.environ[k] = old_env[k]
            else:
                del os.environ[k]


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
