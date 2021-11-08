""" Classes to extend image container functionality for caching, metadata, etc. """
from io import BytesIO
from os.path import basename
import time
from logging import getLogger
from pathlib import Path

from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.image import AsyncImage
from kivymd.uix.imagelist import SmartTile, SmartTileWithLabel

from tesseractXplore.app.cache import cache_async_thumbnail
from tesseractXplore.models import get_icon_path
from tesseractXplore.thumbnails import get_thumbnail_if_exists, get_format, get_thumbnail

logger = getLogger().getChild(__name__)

DESELECTED_COLOR = (0, 0, 0, 0)
SELECTED_COLOR = (0.2, 0.6, 0.6, .4)


class CachedAsyncImage(AsyncImage):
    """ AsyncImage which, once loaded, caches the image for future use """
    def __init__(self, thumbnail_size: str='large', **kwargs):
        """
        Args:
            size : Size of thumbnail to cache
        """
        self.thumbnail_size = thumbnail_size
        self.thumbnail_path = None
        super().__init__(**kwargs)

    def _load_source(self, *args):
        """ Before downloading remote image, first check for existing thumbnail """
        # Differentiating between None and '' here to handle on_load being triggered multiple times
        if self.thumbnail_path is None:
            self.thumbnail_path = get_thumbnail_if_exists(self.source) or ''
            if self.thumbnail_path:
                logger.debug(f'Found {self.source} in cache: {self.thumbnail_path}')
                self.source = self.thumbnail_path
        super()._load_source(*args)

    def on_load(self, *args):
        """ After loading, cache the downloaded image for future use, if not previously done """
        if not get_thumbnail_if_exists(self.source):
            cache_async_thumbnail(self, size=self.thumbnail_size)

    def get_image_bytes(self):
        if not (self._coreimage.image and self._coreimage.image.texture):
            logger.warning(f'Texture for {self.source} not loaded')
            return None

        # thumbnail_path = get_thumbnail_path(self.source)
        ext = get_format(self.source)
        logger.debug(f'Getting image data downloaded from {self.source}; format {ext}')

        # Load inner 'texture' bytes into a file-like object that PIL can read
        image_bytes = BytesIO()
        self._coreimage.image.texture.save(image_bytes, fmt=ext)
        return image_bytes, ext


class IconicTaxaIcon(SmartTile):
    """ Icon for an iconic model """
    is_selected = BooleanProperty()

    def __init__(self, model_id, **kwargs):
        super().__init__(source=get_icon_path(model_id), allow_stretch=False, **kwargs)
        self.is_selected = False
        self.box_color = DESELECTED_COLOR
        self.model_id = model_id
        self.bind(on_release=self.toggle_selection)

    def toggle_selection(self, *args):
        """ Toggle between selected and deselected when clicked. The SmartTile overlay can be
        conveniently repurposed as a background, since the icon is so small the overlay covers it
        """
        if self.is_selected:
            self.box_color = DESELECTED_COLOR
            self.is_selected = False
        else:
            self.box_color = SELECTED_COLOR
            self.is_selected = True


class ImageMetaTile(SmartTileWithLabel):
    """ Class that contains an image thumbnail to display plus its associated metadata """

    def __init__(self, source, **kwargs):
        super().__init__(source=get_thumbnail(source), text=Path(source).name, **kwargs)
        self.original_source = source

    def on_metadata(self, *args):
        """ Triggered whenever metadata changes """
        self.text = self.text
        self.set_box_color()

    def set_box_color(self):
        """ Set the color of the image overlay box based on its metadata """
        def set_alpha(rgba, alpha):
            return rgba[:3] + [alpha]
        self.box_color = (0, 0, 0, 0.5)

