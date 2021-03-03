from os.path import dirname, join
from typing import Optional, Tuple

from appdirs import user_data_dir

from tesseractXplore import __version__

# Resource directories
PKG_DIR = dirname(dirname(__file__))
ASSETS_DIR = join(PKG_DIR, 'assets', '')
METADATA_DIR = join(ASSETS_DIR, 'metadata', '')
KV_SRC_DIR = join(PKG_DIR, 'kv')
ICONS_DIR = join(ASSETS_DIR, 'icons')
DATA_DIR = join(user_data_dir(), 'TesseractXplore')

# TODO: These may be useful as user-configurable settings
TRIGGER_DELAY = 0.1
AUTOCOMPLETE_DELAY = 0.5
AUTOCOMPLETE_MIN_CHARS = 3
IMAGE_FILETYPES = ['*ppm', '*.jpg', '*.jpeg', '*.png', '*.gif', '*.tif', '*.tiff']

# PDF utils (for windows user)
PDF_DIR = join(DATA_DIR, 'pdf')

# Thumnbnail & cache settings
EXIF_ORIENTATION_ID = '0x0112'
THUMBNAILS_DIR = join(DATA_DIR, 'thumbnails')
THUMBNAIL_DEFAULT_FORMAT = 'png'
THUMBNAIL_SIZE_SM = (75, 75)
THUMBNAIL_SIZE_DEFAULT = (400, 400)
THUMBNAIL_SIZE_LG = (600, 600)
THUMBNAIL_SIZES = {
    'small': THUMBNAIL_SIZE_SM,
    'medium': THUMBNAIL_SIZE_DEFAULT,
    'large': THUMBNAIL_SIZE_LG,
}
CC_LICENSES = ['CC0', 'CC-BY', 'CC_BY_NC']

# Atlas settings
# TODO: Not used atm
ATLAS_MAX_SIZE = 4096
ATLAS_BASE = 'atlas://../../assets/atlas'  # Path is relative to Kivy app.py
ATLAS_PATH = join(ASSETS_DIR, 'atlas', 'model_icons.atlas')
ATLAS_TAXON_ICONS = f'{ATLAS_BASE}/model_icons'
ATLAS_TAXON_PHOTOS = f'{ATLAS_BASE}/model_photos'
ATLAS_LOCAL_PHOTOS = f'{ATLAS_BASE}/local_photos'
ATLAS_APP_ICONS = f'{ATLAS_BASE}/app_icons'
ALL_ATLASES = [ATLAS_APP_ICONS, ATLAS_TAXON_ICONS, ATLAS_TAXON_PHOTOS, ATLAS_LOCAL_PHOTOS]

# Cache settings
CACHE_DIR = join(DATA_DIR, 'stdout')
# CACHE_BACKEND = 'sqlite'

# Config files
CONFIG_PATH = join(DATA_DIR, 'settings.yml')
DEFAULT_CONFIG_PATH = join(METADATA_DIR, 'default_settings.yml')
TESSPROFILE_PATH = join(DATA_DIR, 'tessprofiles.json')

# Fonts
DEFAULT_FONTS_DIR = join(ASSETS_DIR, 'fonts', '')
FONTS_DIR = join(DATA_DIR, 'fonts')

# Tessdata
TESSDATA_DIR = join(DATA_DIR, 'tessdata')

# Model file
MODEL_PATH = join(DATA_DIR, 'metadata_modellist.yml')
MODELINFO_PATH = join(DATA_DIR, 'modelinfo.json')
DEFAULT_MODEL_PATH = join(METADATA_DIR, 'default_metadata_modellist.yml')

# URLs / API settings
USER_AGENT = f'tesseract-xplore/{__version__};'.lower()

# Theme/window settings
INIT_WINDOW_POSITION = ('custom', 100, 100)
INIT_WINDOW_SIZE = (1500, 900)
MD_PRIMARY_PALETTE = 'Teal'
MD_ACCENT_PALETTE = 'Cyan'
MAX_LABEL_CHARS = 80

# Key codes; reference: https://gist.github.com/Enteleform/a2e4daf9c302518bf31fcc2b35da4661
BACKSPACE = 8
ENTER = 13
F11 = 292

# Type aliases
IntTuple = Tuple[Optional[int], Optional[int]]
StrTuple = Tuple[Optional[str], Optional[str]]
