#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .mounts_project import MountsProject, volcanoes
from pkg_resources import get_distribution

__version__ = get_distribution("magma-mounts").version
__author__ = "Martanto"
__author_email__ = "martanto@live.COM"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2024, Martanto"
__url__ = "https://github.com/magma-indonesia/extract-mounts"

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "MountsProject",
    "volcanoes",
]