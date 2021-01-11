""" Tools to get keyword tags (e.g., for XMP metadata) from iNaturalist observations """
from datetime import timedelta
from logging import getLogger
from os import makedirs
from os.path import dirname, getsize, exists
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Optional, Tuple
from hashlib import md5
from logging import getLogger
from io import BytesIO, IOBase
from os import makedirs, scandir
from os.path import dirname, isfile, join, normpath, getsize, splitext
from PIL import Image
import json

from tesseractXplore.constants import (
    CACHE_DIR,
    IntTuple,
    StrTuple,
)
from tesseractXplore.validation import format_file_size

logger = getLogger().getChild(__name__)

def write_stdout_cache(image,id,text,params=None):
    if params is not None: params = [""]
    stdout_cache =  read_stdout_cache(image)
    stdout_path = Path(get_stdout_path(image))
    stdout_cache[id] = {'fulltext': text, 'parameter': " ".join(params), 'imagename':image.name}
    logger.info(f'Writing {str(image.absolute())} to stdout cache')
    with open(stdout_path, 'w') as f:
        json.dump(stdout_cache, f, indent=4)

def read_stdout_cache(image):
    stdout_path = Path(get_stdout_path(image))
    if not stdout_path.exists():
        stdout_cache = {}
    else:
        with open(stdout_path) as f:
            stdout_cache = json.load(f)
    return stdout_cache


def get_stdout_cache_size()  -> Tuple[int, str]:
    """Get the current size of the HTTP request cache, in human-readable format"""
    makedirs(CACHE_DIR, exist_ok=True)
    files = [f for f in scandir(CACHE_DIR) if isfile(f)]
    file_size = sum(getsize(f) for f in files)
    return len(files), format_file_size(file_size)

def get_image_hash(image: str) -> str:
    """ Get a unique string based on the source to use as a filename or atlas resource ID """
    return md5(Image.open(image).tobytes()).hexdigest()

def clear_stdout_cache() -> str:
    """Delete call cached thumbnails"""
    rmtree(CACHE_DIR)
    makedirs(CACHE_DIR)

def get_stdout_path(image: str) -> str:
    """
    Determine the thumbnail filename based on a hash of the original file path

    Args:
        source: File path or URI for image source
    """
    makedirs(CACHE_DIR, exist_ok=True)
    stdout_hash = get_image_hash(image)
    return join(CACHE_DIR, f'{stdout_hash}.json')

