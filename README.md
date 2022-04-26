
<p align="center">
    <h1 align="center">🚪 Doorway</h1>
    <p align="center">
        <i>Essential file IO utilities</i>
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
    <a href="https://github.com/nmichlo/doorway/actions?query=workflow%3Atest">
        <img alt="tests status" src="https://img.shields.io/github/workflow/status/nmichlo/doorway/test?label=tests&style=flat-square"/>
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

Doorway is a common library for interacting with files.

Get started with `doorway` by installing it with $`pip install doorway` or cloning this repository.

## Features

Doorway includes the following features:
- Partial "fast" hashing of files
- Stale file detection
- Downloading with a progress bar
- Atomic file writing and overwriting via a seperate temporary file that is moved into place
- File renaming without affecting the extension
- File renaming to replace the extension
