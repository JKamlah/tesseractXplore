""" Screen classes used by the app """
from logging import getLogger
from os.path import join
from typing import Dict, Any

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.screen import MDScreen

from tesseractXplore.constants import KV_SRC_DIR

HOME_SCREEN = 'tesseract_xplore'
HOME_SCREEN_ONLINE = 'tesseract_xplore_online'

# TODO: Load kv files in corresponding widget modules instead?
SCREEN_COMPONENTS = [
    'widgets',
    'main',
    # 'autocomplete',
    'menus',
    'model_search',
    'model_selection',
]

logger = getLogger().getChild(__name__)


class Root(BoxLayout):
    pass

class ImageSelectionScreen(MDScreen):
    pass

class ImageSelectionOnlineScreen(MDScreen):
    pass

class SettingsScreen(MDScreen):
    pass

class FulltextViewScreen(MDScreen):
    pass

class ModelListScreen(MDScreen):
    pass

class TessprofilesScreen(MDScreen):
    pass

class ImageEditorScreen(MDScreen):
    pass

class JobsScreen(MDScreen):
    pass

class ModelScreen(MDScreen):
    pass

class DiffStdoutScreen(MDScreen):
    pass

class GTScreen(MDScreen):
    pass


SCREENS = {
    HOME_SCREEN: ImageSelectionScreen,
    HOME_SCREEN_ONLINE: ImageSelectionOnlineScreen,
    'settings': SettingsScreen,
    'fulltext': FulltextViewScreen,
    'imageeditor': ImageEditorScreen,
    'jobs': JobsScreen,
    'model': ModelScreen,
    'modellist': ModelListScreen,
    'tessprofiles': TessprofilesScreen,
    'groundtruth': GTScreen,
    'diffstdout': DiffStdoutScreen,
}


def load_screens() -> Dict[str, Any]:
    """ Initialize screen components and screens, and store references to them """
    for component_name in SCREEN_COMPONENTS:
        load_kv(component_name)

    screens = {}
    for screen_name, screen_cls in SCREENS.items():
        load_kv(screen_name)
        screens[screen_name] = screen_cls()
    return screens


def load_kv(name: str):
    """ Load an individual kv file by name """
    path = join(KV_SRC_DIR, f'{name}.kv')
    Builder.load_file(path)
    logger.debug(f'Init: Loaded {path}')

