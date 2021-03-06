""" Utilities for intelligently combining thumbnail images into a Kivy Atlas """
from logging import getLogger
from math import ceil
from time import sleep

from PIL import Image

from tesseractXplore.constants import (
    ATLAS_MAX_SIZE,
    THUMBNAILS_DIR,
    THUMBNAIL_SIZE_DEFAULT,
)
from tesseractXplore.image_glob import get_images_from_paths
from tesseractXplore.models import Model
from tesseractXplore.thumbnails import generate_thumbnail_from_url, get_thumbnail_if_exists

IMAGE_DOWNLOAD_DELAY = 1

logger = getLogger().getChild(__name__)


# TODO: Atlas not impelemented atm

def get_resource_path_if_exists(atlas_category, id):
    """ If the specified ID exists in the atlas, return the full path """
    atlas_path = ATLAS_CATEGORIES.get(atlas_category)
    atlas = get_atlas(atlas_path)
    if id in atlas.textures:
        logger.debug(f'Found {id} in atlas')
        return f'{atlas_path}/{id}'
    return None


def get_atlas(atlas_path):
    """ Get atlas from the Kivy cache if present, otherwise initialize it """
    from kivy.atlas import Atlas
    from kivy.cache import Cache

    atlas = Cache.get('kv.atlas', atlas_path.replace('atlas://', ''))
    if not atlas:
        logger.info(f'Initializing atlas "{atlas_path}"')
        atlas = Atlas(f'{atlas_path}.atlas')
        Cache.append('kv.atlas', atlas_path, atlas)
    return atlas


def build_local_photo_atlas(dir=THUMBNAILS_DIR):
    build_atlas(dir, *THUMBNAIL_SIZE_DEFAULT, 'local_photos', max_size=ATLAS_MAX_SIZE * 2)


def build_atlas(image_paths, src_x, src_y, atlas_name, padding=2, **limit_kwarg):
    """ Build a Kivy  Kivy :py:class:`~kivy.atlas.Atlas`

    Args:
        image_paths (list): Paths to images and/or image directories
        src_x: Max width of source images
        src_y: Max height of source images
        atlas_name: Name of atlas file to create
        \\*\\*limit_kwarg: At most one limit to provide to :py:func:`.get_atlas_dimensions`
    """
    from kivy.atlas import Atlas

    # Allow smallest dimension to be as low as half the max. This this works because each thumbnail
    # size category is over twice the size of the next smallest one
    min_x = ceil(src_x / 2)
    min_y = ceil(src_y / 2)
    logger.info(f'Searching for images of dimensions ({min_x}-{src_x}) x ({min_y}-{src_y})...')
    image_paths = list(filter_images_by_size(image_paths, src_x, src_y, min_x, min_y))
    logger.info(f'{len(image_paths)} images found')

    atlas_size = get_atlas_dimensions(
        len(image_paths), src_x, src_y, padding=padding, **limit_kwarg
    )
    logger.info(f'Calculated atlas size: {atlas_size}')
    if atlas_size != (0, 0):
        Atlas.create(atlas_name, image_paths, atlas_size, padding=padding)


def filter_images_by_size(image_paths, max_x, max_y, min_x, min_y):
    """ Get all images from the specified paths that are within specified dimensions.
    See also :py:func:`.get_images_from_paths`

    Args:
        image_paths (list): Paths to images and/or image directories
        max_x (int): Return only images this width or smaller
        max_y (int): Return only images this height or smaller
        min_x (int): Return only images this width or larger
        min_y (int): Return only images this height or larger

    Returns:
        list: Filtered list of image file paths
    """
    for image_path in get_images_from_paths(image_paths):
        img = Image.open(image_path)
        img_x, img_y = img.size
        img.close()
        if min_x <= img_x <= max_x and min_y < img_y <= max_y:
            yield image_path


def get_atlas_dimensions(n_images, x, y, padding=2, max_size=None, max_bins=None, max_per_bin=None):
    """ Get the ideal dimensions of a Kivy :py:class:`~kivy.atlas.Atlas` in which to store images
    of mostly uniform size.
    'Ideal' in this case means the smallest rectangle, with minimal wasted space, with closest to
    square x and y dimensions, and within specified limit of dimensions, # of bins, or
    # of images per bin. Only one of these limit parameters (``max_*``) may be provided.

    Args:
        n_images (str): Number of images to combine
        x (int): Horizontal dimension of images
        y (int): Vertical dimension of images
        padding (int): Amount of padding per image, in pixels
        max_size (int): Maximum dimension (x or y) of combined atlas image; beyond that multiple
            atlas images will be created
        max_bins (int): The maximum number of atlas images to produce
        max_per_bin (int): Maximum number of images per bin

    Returns:
        ``int, int``: Ideal atlas dimensions
    """
    if len(list(filter(None, [max_size, max_bins, max_per_bin]))) > 1:
        raise ValueError('Only one max limit may be provided')
    if n_images == 0:
        return 0, 0

    # Apply limit (if any) round up to nearest even int; a small amount of wasted space is okay
    if max_bins:
        n_images = ceil(n_images / max_bins)
    if max_per_bin:
        n_images = min(n_images, max_per_bin)
    if n_images % 2 == 1:
        n_images += 1

    # Get total atlas dimensions that will fit all the thumbnails
    x += padding
    y += padding
    factors = _largest_factor_pair(n_images)
    factor_x = _max_factor(x, factors[0], max_size)
    factor_y = _max_factor(y, factors[1], max_size)
    return x * factor_x, y * factor_y


def _max_factor(n, factor, max_size):
    """ Return the largest factor within the provided max;
    e.g., the most images of size n thet can fit in max_size
    """
    if max_size is None or n * factor <= max_size:
        return factor
    return max_size // n


def _largest_factor_pair(n):
    """ Get the largest pair of factors for the given number """
    for i in reversed(range(1, int(n ** 0.5) + 1)):
        if n % i == 0:
            return i, int(n / i)
    return n, 1


def preload_iconic_taxa_thumbnails():
    """ Pre-download model thumbnails for iconic taxa and descendants down to 2 ranks below """
    for id, name in list(PRELOAD_TAXA.items()):
        min_rank = 'family'
        if name == 'mammalia':
            min_rank = 'genus'
        if name in ['chromista', 'animalia']:
            min_rank = 'class'
        logger.info(f'Processing iconic model: {name} down to {min_rank} level')
        preload_thumnails(Model(id=id), min_rank=min_rank)


def preload_thumnails(model, min_rank='family', depth=0):
    logger.info(f'Processing: {model.rank} {model.name} at depth {depth}')
    thumnail_exists = model.photo_url and get_thumbnail_if_exists(model.photo_url)

    # Only preload images that can be redistributed under Creative Commons
    if model.has_cc_photo and not thumnail_exists:
        generate_thumbnail_from_url(model.photo_url, 'large')
        generate_thumbnail_from_url(model.thumbnail_url, 'small')
        sleep(IMAGE_DOWNLOAD_DELAY)

    if model.rank not in [min_rank, 'species', 'subspecies']:
        n_children = len(model.child_taxa)
        for i, child in enumerate(model.child_taxa):
            # Skip child if it's already loaded in another category
            if child.id not in PRELOAD_TAXA:
                logger.info(f'Child {i}/{n_children}')
                preload_thumnails(child, min_rank, depth=depth + 1)


if __name__ == '__main__':
    # preload_iconic_taxa_thumbnails()
    build_local_photo_atlas()
