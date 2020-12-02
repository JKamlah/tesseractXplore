""" Tools to get keyword tags (e.g., for XMP metadata) from iNaturalist observations """
from datetime import timedelta
from logging import getLogger
from os import makedirs
from os.path import dirname, getsize
from typing import Dict, List, Optional, Tuple

from tesseractXplore.constants import (
    CACHE_BACKEND,
    CACHE_PATH,
    IntTuple,
    StrTuple,
)
from tesseractXplore.validation import format_file_size


def get_stdout_cache_size() -> str:
    """Get the current size of the HTTP request cache, in human-readable format"""
    return format_file_size(getsize(f'{CACHE_PATH}.{CACHE_BACKEND}'))

def clear_stdout_cache() -> str:
    """Get the current size of the HTTP request cache, in human-readable format"""
    return format_file_size(getsize(f'{CACHE_PATH}.{CACHE_BACKEND}'))