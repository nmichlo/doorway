
<p align="center">
    <h1 align="center">🚪 Doorway</h1>
    <p align="center">
        <i>Essential data wrangling utilities.</i>
    </p>
</p>

<p align="center">
    <a href="https://choosealicense.com/licenses/mit/" target="_blank">
        <img alt="license" src="https://img.shields.io/github/license/nmichlo/doorway?style=flat-square&color=lightgrey"/>
    </a>
    <a href="https://pypi.org/project/doorway" target="_blank">
        <img alt="python versions" src="https://img.shields.io/pypi/pyversions/doorway?style=flat-square"/>
    </a>
    <a href="https://pypi.org/project/doorway" target="_blank">
        <img alt="pypi version" src="https://img.shields.io/pypi/v/doorway?style=flat-square&color=blue"/>
    </a>
    <a href="https://github.com/nmichlo/doorway/actions/workflows/python-test.yml">
        <img alt="tests status" src="https://img.shields.io/github/actions/workflow/status/nmichlo/doorway/python-test.yml?label=tests&style=flat-square"/>
    </a>
    <a href="https://codecov.io/gh/nmichlo/doorway/">
        <img alt="code coverage" src="https://img.shields.io/codecov/c/gh/nmichlo/doorway?token=86IZK3J038&style=flat-square"/>
    </a>
</p>

<p align="center">
    <p align="center">
        <a href="https://github.com/nmichlo/doorway/issues/new/choose">Contributions</a> are welcome!
    </p>
</p>

----------------------

## Table Of Contents

- [Overview](#overview)
- [Features](#features)

----------------------

## Overview

Doorway is a common library for interacting with files and data wranging, with zero deps over the common utils.

Get started with `doorway` by installing it with $`pip install doorway` or cloning this repository.

Experimental features need `pip install "doorway[extras]"`

## Features

Doorway includes the following features:
- [x] Partial "fast" hashing of files
- [x] Stale file detection
- [x] Atomic file writing and overwriting via a separate temporary file that is moved into place
- [x] Path name modification
- [x] Context managers
- [x] Environment Vars & Validation
- [x] String Colors
- [x] String Formatting
- [x] Downloading with a progress bar
- [x] Deterministic dataset partitioning using

As well as experimental:
- [ ] Arbitrary URI interop and handling
- [x] Proxy downloader -- multithreading, auto-retry, auto proxy retrieval and rotation.


### Atomic IO

Write or overwrite a file without worrying about it being half-written or corrupted,
and left in a bad state.

```python
from doorway import AtomicOpen, AtomicPath

# write to a temporary file, then move it into place once the context closes
with AtomicOpen("my/file.txt", "w") as f:
    f.write("Hello, World!")

# generate a temporary path and raise an exception if the file does not exist when the context closes
with AtomicPath("my/file.txt") as path:
    with open(path, "w") as f:  # `doorway.AtomicPath` + open ~= `doorway.AtomicOpen`
        f.write("Hello, World!")
```

### Fast Hashing

```python
from doorway import hash_file

# normal hashing
hast_full = hash_file("my/large.file", hash_mode="full", hash_algo="md5")
# fast hashing, uses start, middle and end bytes
hash_fast = hash_file("my/large.file", hash_mode="fast", hash_algo="md5")

# `doorway.hash_bytes`, `doorway.hash_str`, `doorway.hash_file_is_valid` are also available
```

### Stale Files

```python
from doorway import stalefile_generate, stalefile_is_stale

# generate a file if it is stale (doesn't exist or the hash is different)
stalefile_generate(
    make_file_fn=lambda path: open(path, "w").close(),
    path="my/file.txt",
    hash="some-long-hash-fffffffffffffffffffffffffff",
)

# check if a file is stale (doesn't exist or the hash is different)
exists = stalefile_is_stale(
    path="my/file.txt",
    hash="some-long-hash-fffffffffffffffffffffffffff",
)
```

### Path Modification

```python
from doorway import path_basename_modify

# `basename` is the full last part of the path e.g. "file.1.2.txt"
# `name` is the basename without the `extension` e.g. "file.1.2" or "file" (depending on the `name_contains_sep` parameter)
path = "my/path/to/file.1.2.txt"

p0 = path_basename_modify(
    path,
    ext="csv",
    name_prefix="a_",
    name_suffix="_b",
    name_contains_sep=True,
)
p1 = path_basename_modify(
    path,
    ext="csv",
    name_prefix="a_",
    name_suffix="_b",
    name_contains_sep=False,
)

assert p0 == "my/path/to/a_file.1.2_b.csv"
assert p1 == "my/path/to/a_file_b.csv"

# see `doorway.basename_modify` for the non-path version of this
# see `doorway.basename_split_ext` for splitting the name from the extension
```

### File Downloading

Easy file downloading wrapping `AtomicIO` with a progress bar if `tqdm` is installed.

```python
from doorway import io_download

# download a file with a progress bar
io_download(
    src_url="https://example.com/file.txt",
    dst_path="my/file.txt",
    exists_mode="error", # options are: "error" (default), "overwrite", "skip"
    progress=True,  # (default)
)
```

### Context Managers

Context managers for various tasks.

```python
import os
from doorway import ctx_temp_environ

# temporarily set an environment variable
with ctx_temp_environ(TEMP_VAR="temp_value"):
    assert os.environ.get("TEMP_VAR", None) == "temp_value"
assert os.environ.get("TEMP_VAR", None) is None

# most of the other context managers are similar
# all gracefully handle exceptions and undo their changes
# - ctx_temp_wd:       temporarily update the working directory
# - ctx_temp_attr:     temporarily update an attribute on an object
# - ctx_temp_sys_args: temporarily update sys.argv
# - ctx_no_stdout:     temporarily suppress stdout
# - ctx_no_stderr:     temporarily suppress stderr
# - ctx_do_undo:       do something (run "do" fn), then undo it (run "undo" fn)
```

### Environment Variables

Parse environment variables and validate their values.

```python
from doorway import EnvVar, ctx_temp_environ

MY_VAR = EnvVar.env_int(
    "MY_VAR",
    default=42,
    validator=EnvVar.validator_min_max(0, 100),
)

# get the value of the environment variable (and validate)
with ctx_temp_environ(MY_VAR="7"):
    assert MY_VAR.get() == 7

# get a default value if set (and validate)
# - if no default was set, an exception is raised
assert MY_VAR.get() == 42

# override the default value for this call (and validate)
with ctx_temp_environ(MY_VAR="8"):
    assert MY_VAR.get(default=43) == 8
assert MY_VAR.get(default=43) == 43

# force a value (and validate)
with ctx_temp_environ(MY_VAR="9"):
    assert MY_VAR.get(override=99) == 99
assert MY_VAR.get(override=99) == 99
```

### ANSI Colors

```python
from doorway import c

print(f"{c.lRED}This is red {c.RST}This is reset to defaults")
```

### Human Readable Byte Conversion

```python
from doorway import fmt_bytes_to_human

assert fmt_bytes_to_human(1025**0, base=1024) == "1.000 B"
assert fmt_bytes_to_human(1025**0, base=1000) == "1.000 B"

assert fmt_bytes_to_human(1025**1, base=1024) == "1.001 KiB"
assert fmt_bytes_to_human(1025**1, base=1000) == "1.025 kB"  # lowercase is more correct for kB in this case

assert fmt_bytes_to_human(1025**2, base=1024) == "1.002 MiB"
assert fmt_bytes_to_human(1025**2, base=1000) == "1.051 MB"

assert fmt_bytes_to_human(1025**3, base=1024) == "1.003 GiB"
assert fmt_bytes_to_human(1025**3, base=1000) == "1.077 GB"

assert fmt_bytes_to_human(1025**4, base=1024) == "1.004 TiB"
assert fmt_bytes_to_human(1025**4, base=1000) == "1.104 TB"
```

### Deterministic Dataset Partitioning

Split datapoints deterministically but pseudo-randomly into buckets.

This is useful when you have datasets that are increasing or decreasing in size,
but you want to keep adding the same datapoints to the same splits/buckets/shards.
(A standard shuffle with seed CANNOT do this)

_The example below only has 9 datapoints, which doesn't show the full power
of this function, this is useful for much larger datasets when assignment
to buckets follows the expected statistical distribution._


```python
from doorway import sharded, sharded_weighted

# create 3 buckets and assign values to them pseudo-randomly
shards = sharded(
    values=[1, 2, 3, 4, 5, 6, 7, 8, 9],
    num_shards=3,
    shard_key=lambda x: str(x),
)
print(shards)  # [[2, 5, 6, 7], [1, 3], [4, 8, 9]]

# create 3 buckets with relative weights 9:1:1 and assign values to them pseudo-randomly
train, test, split = sharded_weighted(
    values=[1, 2, 3, 4, 5, 6, 7, 8, 9],
    shard_weights=[8, 3, 1],
    shard_key=str,
)
print(train, test, split)  # [2, 6, 9, 7, 8, 1, 3] [4, 5] []
```


### Proxy Downloader

```python
# EXPERIMENTAL, API may change -- `pip install doorway[extras]`
from doorway.x import ProxyDownloader, proxy_download


# collect a default list of proxies and cache them
# - see: `proxies_register_scraper` for registering custom proxies, or pass in a list of proxies directly to this
downloader = ProxyDownloader()

# download a single file with a randomly chosen proxy
path = downloader.download(
    "https://example.com/file.txt", # src
    "my/file.txt",  # dst
    exists_mode="error",  # options are: "error" (default), "overwrite", "skip"
)

# download multiple files in parallel while rotating proxies and retrying if any fail
failed = downloader.download_threaded(
    [
        ("https://example.com/file1.txt", "my/file1.txt"),
        ("https://example.com/file2.txt", "my/file2.txt"),
        ("https://example.com/file3.txt", "my/file3.txt"),
    ],
    exists_mode="error",  # options are: "error" (default), "overwrite", "skip"
    verbose=True, # (default is False)
    ignore_failures=True,  # (default is False)
)
```

#### Proxy Issues?

The scrape logic used to obtain the proxy list will  probably go out of date. You can override
the *default* scrape logic by registering a new scrape function.

```python3
from doorway.x import proxies_register_scraper

@proxies_register_scraper(name='my_proxy_source', is_default=True)
def custom_proxy_scraper(proxy_type):
    # you should respect this setting
    assert proxy_type in ('all', 'http', 'https')
    # proxies is a list of dictionaries, where each dictionary only has one entry:
    # - the key is the protocol
    # - the value is the matching full url
    return [
        {'HTTP': 'http://<my-http-proxy>.com'},
        {'HTTPS': 'https://<my-https-proxy>.com'},
    ]
```

### URI Handling

Interop between URIs from different locations, e.g. S3, Local, HTTP, etc.

```python
# TODO: W.I.P
```

----------------

## TODO

- [ ] More Docs
- [ ] More Examples
- [ ] More APIs
