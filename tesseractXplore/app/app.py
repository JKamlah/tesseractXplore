""" Main Kivy application """
import asyncio
import os
from logging import getLogger
from threading import Thread
from sys import platform as _platform

from tesseractXplore.settings import read_settings

# Set GL backend before any kivy modules are imported
os.environ['KIVY_GL_BACKEND'] = 'sdl2'
# Set Textprovider backend before any kivy modules are imported
settings = read_settings()
if settings['display']['pil_textprovider'] == 'down':
    os.environ['KIVY_TEXT'] = 'pil'
elif settings['display']['pygame_textprovider'] == 'down':
    os.environ['KIVY_TEXT'] = 'pygame'
elif settings['display']['pango_textprovider'] == 'down':
    os.environ['KIVY_TEXT'] = 'pango'

# TODO: Make it as setting
from kivy.clock import Clock

# Disable multitouch emulation before any other kivy modules are imported
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivymd.app import MDApp

from tesseractXplore.app import alert
from tesseractXplore.app.screens import HOME_SCREEN, Root, load_screens
from tesseractXplore.tessprofiles import read_tessprofiles
from tesseractXplore.constants import (
    INIT_WINDOW_POSITION,
    INIT_WINDOW_SIZE,
    MD_PRIMARY_PALETTE,
    MD_ACCENT_PALETTE,
    BACKSPACE,
    ENTER,
    F11, TRIGGER_DELAY,
)
from tesseractXplore.controllers import (
    ImageSelectionController,
    FulltextViewController,
    ImageEditorController,
    SettingsController,
    ModelListController,
    ModelSearchController,
    ModelSelectionController,
    ModelViewController,
    TessprofilesController,
    TesseractController,
    DiffStdoutController,
)
from tesseractXplore.widgets import ModelListItem

logger = getLogger().getChild(__name__)


class ControllerProxy:
    """ The individual controllers need to talk to each other sometimes.
    Any such interactions go through this class so they don't talk to each other directly.
    This also just serves as documentation for these interactions so I don't lose track of them.
    """
    image_selection_controller = ObjectProperty()
    fulltext_view_controller = ObjectProperty()
    image_edit_controller = ObjectProperty()
    model_search_controller = ObjectProperty()
    model_selection_controller = ObjectProperty()
    model_view_controller = ObjectProperty()
    modellist_controller = ObjectProperty()
    tessprofiles_controller = ObjectProperty()
    settings_controller = ObjectProperty()
    diffstdout_controller = ObjectProperty()

    def init_controllers(self, screens):
        # Init OS-specific errorcodes
        self._platform = _platform
        self.errorcodes = [1,127] if _platform in ["win32","win64"] else [127]

        # Read profile settings
        self.tessprofiles = read_tessprofiles()

        # Init controllers with references to nested screen objects
        self.settings_controller = SettingsController(screens['settings'].ids)
        self.tessdatadir = self.settings_controller.tesseract['tessdatadir']
        self.tesspath = self.settings_controller.tesseract['tesspath']
        self.image_selection_controller = ImageSelectionController(screens[HOME_SCREEN].ids)
        self.tesseract_controller = TesseractController(screens[HOME_SCREEN].ids)
        self.fulltext_view_controller = FulltextViewController(screens['fulltext'].ids)
        self.image_editor_controller = ImageEditorController(screens['imageeditor'].ids)
        self.model_selection_controller = ModelSelectionController(screens['model'].ids)
        self.model_view_controller = ModelViewController(screens['model'].ids)
        self.modellist_controller = ModelListController(screens['modellist'].ids)
        self.tessprofiles_controller = TessprofilesController(screens['tessprofiles'].ids)
        self.model_search_controller = ModelSearchController(screens['model'].ids)
        self.diffstdout_controller = DiffStdoutController(screens['diffstdout'].ids)
        # gt_search_controller = GTSearchController(screens['gt'].ids)

        # Proxy methods
        self.is_starred = self.model_selection_controller.is_starred
        self.add_star = self.model_selection_controller.add_star
        self.select_fulltext = self.fulltext_view_controller.select_fulltext
        self.select_image = self.image_editor_controller.select_image
        self.remove_star = self.model_selection_controller.remove_star
        self.select_model = self.model_view_controller.select_model
        self.select_model_from_photo = self.image_selection_controller.select_model_from_photo
        self.update_history = self.model_selection_controller.update_history
        self.add_control_widget = self.settings_controller.add_control_widget

        # Proxy properties
        self.locale = self.settings_controller.locale
        self.username = self.settings_controller.username
        self.password = self.settings_controller.password


        self.image_selection_controller.post_init()
        self.model_selection_controller.post_init()

    def get_model_list_item(self, *args, **kwargs):
        """ Get a new :py:class:`.ModelListItem with event binding """
        item = ModelListItem(*args, **kwargs)
        self.bind_to_select_model(item)
        return item

    def bind_to_select_model(self, item):
        # If ModelListItem's disable_button is set, don't set button action
        if not item.disable_button:
            item.bind(on_release=lambda x: self.model_view_controller.select_model(x.model))


class TesseractXplore(MDApp, ControllerProxy):
    """ Manages window, theme, main screen and navigation state; other application logic is
    handled by Controller
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_loop = None
        self.root = None
        self.nav_drawer = None
        self.screen_manager = None
        self.toolbar = None
        # Buffer + delayed trigger For collecting multiple files dropped at once
        self.dropped_files = []
        self.drop_trigger = Clock.create_trigger(self.process_dropped_files, TRIGGER_DELAY)

    def build(self):
        # Set color palette
        self.theme_cls.primary_palette = MD_PRIMARY_PALETTE
        self.theme_cls.accent_palette = MD_ACCENT_PALETTE

        # Create an event loop to be used by background loaders
        self.bg_loop = asyncio.new_event_loop()
        # Need this to get killed when app closes
        tmain = Thread(target=self.bg_loop.run_forever)
        tmain.setDaemon(True)
        tmain.start()

        # Init screens and store references to them
        screens = load_screens()
        self.root = Root()
        ControllerProxy.init_controllers(self, screens)

        # Init screen manager and nav elements
        self.nav_drawer = self.root.ids.nav_drawer
        self.screen_manager = self.root.ids.screen_manager
        self.toolbar = self.root.ids.toolbar

        for screen_name, screen in screens.items():
            self.screen_manager.add_widget(screen)
        self.set_theme_mode()
        self.home()

        # self.switch_screen('model')

        # Set Window and theme settings
        position, left, top = INIT_WINDOW_POSITION
        Window.position = position
        Window.left = left
        Window.top = top
        Window.size = INIT_WINDOW_SIZE
        Window.bind(on_keyboard=self.on_keyboard)
        Window.bind(on_request_close=self.on_request_close)

        # On_dropfile sends a single file at a time; this collects files dropped at the same time
        Window.bind(on_dropfile=lambda _, path: self.dropped_files.append(path))
        Window.bind(on_dropfile=self.drop_trigger)

        # Preload atlases so they're immediately available in Kivy cache
        # TODO: Currently not necessary, but will be in future version
        # Image(source=f'{ATLAS_APP_ICONS}/')
        # Image(source=f'{ATLAS_TAXON_ICONS}/')
        return self.root

    def process_dropped_files(self, *args):
        self.image_selection_controller.add_images(self.dropped_files)
        self.dropped_files = []

    def home(self, *args):
        self.switch_screen(HOME_SCREEN)

    def open_nav(self, *args):
        self.nav_drawer.set_state('open')

    def close_nav(self, *args):
        self.nav_drawer.set_state('close')

    def switch_screen(self, screen_name: str):
        # If we're leaving a screen with stored state, save it first
        # TODO: Also save stored taxa, but needs optimization first (async, only store if changed)
        if self.screen_manager.current in ['settings']:
            self.settings_controller.save_settings()
        if screen_name == "model":
            self.model_view_controller.screen.tessdatadir.text = self.tessdatadir
        self.screen_manager.current = screen_name
        self.update_toolbar(screen_name)
        self.close_nav()

    def on_request_close(self, *args):
        """ Save any unsaved settings before exiting """
        self.settings_controller.save_settings()
        self.stop()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """ Handle keyboard shortcuts """
        if (modifier, key) == (['ctrl'], BACKSPACE):
            self.home()
        elif (modifier, key) == (['ctrl'], ENTER):
            self.current_screen_action()
        elif (set(modifier), codepoint) == ({'ctrl', 'shift'}, 'x'):
            self.current_screen_clear()
        elif (modifier, codepoint) == (['ctrl'], 'o'):
            self.image_selection_controller.open_native_file_chooser()
        elif (set(modifier), codepoint) == ({'ctrl', 'shift'}, 'o'):
            self.image_selection_controller.open_native_file_chooser(dirs=True)
        elif (modifier, codepoint) == (['ctrl'], 'q'):
            self.on_request_close()
        elif (modifier, codepoint) == (['ctrl'], 's'):
            self.switch_screen('settings')
        elif (modifier, codepoint) == (['ctrl'], 't'):
            self.switch_screen('model')
        elif (modifier, codepoint) == (['ctrl'], 'v'):
            self.current_screen_paste()
        elif self.screen_manager.current == HOME_SCREEN:
            if (modifier, codepoint) == (['ctrl'], '+'):
                self.image_selection_controller.zoomin(None, None)
            elif (modifier, codepoint) == (['ctrl'], '-'):
                self.image_selection_controller.zoomout(None, None)
        elif key == F11:
            self.toggle_fullscreen()

    # TODO: current_screen_*() may be better organized as controller methods (inherited/overridden as needed)
    def current_screen_action(self):
        """ Run the current screen's main action """
        if self.screen_manager.current == HOME_SCREEN:
            self.tesseract_controller.recognize(None)
        elif self.screen_manager.current == 'model':
            self.model_search_controller.search()

    def current_screen_clear(self):
        """ Clear the settings on the current screen, if applicable """
        if self.screen_manager.current == HOME_SCREEN:
            self.image_selection_controller.clear()
        elif self.screen_manager.current == 'model':
            self.model_search_controller.reset_all_search_inputs()

    # TODO: Threw this together quickly, this could be cleaned up a lot
    def current_screen_paste(self):
        value = Clipboard.paste()
        model_id, gt_id = 0, 0
        if model_id:
            self.select_model(id=model_id)
            alert(f'Model {model_id} selected')
        if gt_id:
            # self.select_gt(id=gt_id)
            alert(f'GT {gt_id} selected')

        if self.screen_manager.current == HOME_SCREEN:
            if gt_id:
                self.image_selection_controller.screen.gt_id_input.text = str(gt_id)
                self.image_selection_controller.screen.model_id_input.text = ''
            elif model_id:
                self.image_selection_controller.screen.gt_id_input.text = ''
                self.image_selection_controller.screen.model_id_input.text = str(model_id)

    def update_toolbar(self, screen_name: str):
        """ Modify toolbar in-place so it can be shared by all screens """
        self.toolbar.title = screen_name.title().replace('_', ' ')
        if screen_name == HOME_SCREEN:
            self.toolbar.left_action_items = [['menu', self.open_nav]]
        else:
            self.toolbar.left_action_items = [["arrow-left", self.home]]
        self.toolbar.right_action_items = [
            ['border-none-variant', self.toggle_border],
            ['fullscreen', self.toggle_fullscreen],
            ['dots-vertical', self.open_settings],
        ]

    def set_theme_mode(self, switch=None, is_active: bool = None):
        """ Set light or dark themes, based on either toggle switch or settings """
        if is_active is None:
            is_active = self.settings_controller.display['dark_mode']
        self.theme_cls.theme_style = 'Dark' if is_active else 'Light'

    def toggle_border(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        # Window fullscreen doesn't work with two displays
        if self.toolbar.right_action_items[0][0] == 'border-all-variant':
            Window.borderless = 0
            icon = 'border-none-variant'
        else:
            Window.borderless = 1
            icon = 'border-all-variant'
        self.toolbar.right_action_items[0] = [icon, self.toggle_border]

    def toggle_fullscreen(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        # Window fullscreen doesn't work with two displays
        if self.toolbar.right_action_items[1][0] == 'fullscreen-exit':
            Window.restore()
            icon = 'fullscreen'
        else:
            Window.maximize()
            icon = 'fullscreen-exit'
        self.toolbar.right_action_items[1] = [icon, self.toggle_fullscreen]


def main():
    TesseractXplore().run()

if __name__ == '__main__':
    main()
