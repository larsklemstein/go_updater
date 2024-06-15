# Description

Update your locally installed Go on Linux.


# Implementation

First we check for the latest stable Go linux version.

Then we cecks if the given path exists with an installed Go. If is already match that version,
there's nothing to do. Otherwise we will fetch that version, delete(!) the existing installation
and extract the updated archive, replacing the same old path.

If there's initially no installed Go at the given path, we will just install it there.


# License

[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
