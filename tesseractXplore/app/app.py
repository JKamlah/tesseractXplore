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
from tesseractXplore.app.screens import HOME_SCREEN, HOME_SCREEN_ONLINE, Root, load_screens
from tesseractXplore.tessprofiles import read_tessprofiles
from tesseractXplore.modelinfos import Modelinformations
from tesseractXplore.app import get_app
from tesseractXplore.constants import (
    INIT_WINDOW_POSITION,
    INIT_WINDOW_SIZE,
    MD_PRIMARY_PALETTE,
    MD_PRIMARY_PALETTE_ONLINE,
    MD_ACCENT_PALETTE,
    MD_ACCENT_PALETTE_ONLINE,
    BACKSPACE, ENTER, F2, F5, F6, F7, F8, F9, F10, F11, F12,
    TRIGGER_DELAY,
)
from tesseractXplore.controllers import (
    ImageSelectionController,
    ImageSelectionOnlineController,
    FulltextViewController,
    ImageEditorController,
    JobsController,
    SettingsController,
    ModelListController,
    ModelSearchController,
    ModelSelectionController,
    ModelViewController,
    TessprofilesController,
    TesseractController,
    TesseractOnlineController,
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
    image_selection_online_controller = ObjectProperty()
    fulltext_view_controller = ObjectProperty()
    image_edit_controller = ObjectProperty()
    model_search_controller = ObjectProperty()
    model_selection_controller = ObjectProperty()
    model_view_controller = ObjectProperty()
    modellist_controller = ObjectProperty()
    tessprofiles_controller = ObjectProperty()
    tesseract_controller = ObjectProperty()
    tesseract_online_controller = ObjectProperty()
    jobs_controller = ObjectProperty()
    settings_controller = ObjectProperty()
    diffstdout_controller = ObjectProperty()

    def init_controllers(self, screens):
        # Basic app information
        self._window = Window

        # Processthreads
        self.active_threads = {}

        # Init OS-specific errorcodes
        self._platform = _platform
        self.errorcodes = [1,127] if _platform in ["win32","win64"] else [127]

        # Read profile settings
        self.tessprofiles = read_tessprofiles()
        self.tessprofiles_online = read_tessprofiles(online=True)
        self.modelinformations = Modelinformations()

        # Init controllers with references to nested screen objects
        self.settings_controller = SettingsController(screens['settings'].ids)
        self.image_selection_controller = ImageSelectionController(screens[HOME_SCREEN].ids)
        self.tesseract_controller = TesseractController(screens[HOME_SCREEN].ids)
        self.image_selection_online_controller = ImageSelectionOnlineController(screens[HOME_SCREEN_ONLINE].ids)
        self.tesseract_online_controller = TesseractOnlineController(screens[HOME_SCREEN_ONLINE].ids)
        self.jobs_controller = JobsController(screens['jobs'].ids)
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
        self.token = None

        self.image_selection_controller.post_init()
        self.image_selection_online_controller.post_init()
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
        self.home_screen = HOME_SCREEN
        self.nav_drawer = None
        self.screen_manager = None
        self.toolbar = None
        # Buffer + delayed trigger For collecting multiple files dropped at once
        self.dropped_files = []
        self.drop_trigger = Clock.create_trigger(self.process_dropped_files, TRIGGER_DELAY)

        # Profile
        # import cProfile
        # self.profile = cProfile.Profile()
        # self.profile.enable()

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
        self.init_toolbar(HOME_SCREEN)

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

        # Start checking active threads for processmanager
        Clock.schedule_interval(self.check_threads, .05)

        return self.root

    def check_threads(self, dt):
        import threading
        active_threads = get_app().active_threads.copy()
        for active_thread, pm in active_threads.items():
            if active_thread not in threading.enumerate():
                del get_app().active_threads[active_thread]
                pm.parent.remove_widget(pm)

    def process_dropped_files(self, *args):
        self.image_selection_controller.add_images(self.dropped_files)
        self.dropped_files = []

    def home(self, *args):
        self.switch_screen(self.home_screen)

    def is_online(self):
        return True if self.home_screen == HOME_SCREEN_ONLINE else False

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
            self.model_view_controller.screen.tessdatadir.set_text(self.model_view_controller.screen.tessdatadir,
                                                                   self.settings_controller.tesseract['tessdatadir'])
        self.screen_manager.current = screen_name
        self.update_toolbar(screen_name)
        self.close_nav()

    def on_request_close(self, *args):
        """ Save any unsaved settings before exiting """
        self.settings_controller.save_settings()
        self.stop()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """ Handle keyboard shortcuts """
        if 'ctrl' in modifier:
            if 'shift' in modifier:
                if codepoint == 'x':
                    self.current_screen_clear()
            else:
                if key == ENTER:
                    self.current_screen_action()
                elif codepoint == 'q':
                    self.on_request_close()
                elif codepoint == 's':
                    self.settings_controller.save_settings()
                elif self.screen_manager.current == HOME_SCREEN:
                    if codepoint == '+':
                        self.image_selection_controller.zoomin(None, None)
                    elif codepoint == '-':
                        self.image_selection_controller.zoomout(None, None)
                    elif codepoint == 'o':
                        self.image_selection_controller.open_folder()
        elif key == F2:
            self.switch_screen('settings')
        elif key == F5:
            self.home()
        elif key == F6:
            self.switch_screen('modellist')
        elif key == F7:
            self.switch_screen('model')
        elif key == F9:
            self.toggle_online_offline()
        elif key == F10:
            self.toggle_border()
        elif key == F11:
            self.toggle_fullscreen()
        elif key == F12:
            self.settings_controller.change_colormode()
            self.settings_controller.save_settings()


    # TODO: current_screen_*() may be better organized as controller methods (inherited/overridden as needed)
    def current_screen_action(self):
        """ Run the current screen's main action """
        if self.screen_manager.current == self.home_screen:
            self.tesseract_controller.recognize(None)
        elif self.screen_manager.current == 'model':
            self.model_search_controller.search()

    def current_screen_clear(self):
        """ Clear the settings on the current screen, if applicable """
        if self.screen_manager.current == self.home_screen:
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

        if self.screen_manager.current == self.home_screen:
            if gt_id:
                self.image_selection_controller.screen.gt_id_input.text = str(gt_id)
                self.image_selection_controller.screen.model_id_input.text = ''
            elif model_id:
                self.image_selection_controller.screen.gt_id_input.text = ''
                self.image_selection_controller.screen.model_id_input.text = str(model_id)

    def update_toolbar(self, screen_name: str):
        """ Modify toolbar in-place so it can be shared by all screens """
        self.toolbar.title = screen_name.title().replace('_', ' ')
        if screen_name in [HOME_SCREEN, HOME_SCREEN_ONLINE]:
            self.toolbar.left_action_items = [['menu', self.open_nav]]
        else:
            self.toolbar.left_action_items = [["arrow-left", self.home]]

    def init_toolbar(self, screen_name:str):
        self.toolbar.right_action_items = [
            ['cloud-off-outline', self.toggle_online_offline, 'Switch to TesseracXploreOnline'],
            ['border-none-variant', self.toggle_border, 'Borderless'],
            ['fullscreen', self.toggle_fullscreen, 'Fullscreen'],
            ['dots-vertical', self.open_settings, 'Open app settings'],
        ]

    def set_theme_mode(self, switch=None, is_active: bool = None):
        """ Set light or dark themes, based on either toggle switch or settings """
        if is_active is None:
            is_active = self.settings_controller.display['dark_mode']
        self.theme_cls.theme_style = 'Dark' if is_active else 'Light'

    def toggle_online_offline(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        # Window fullscreen doesn't work with two displays
        if self.toolbar.right_action_items[0][0] == 'cloud-off-outline':
            self.theme_cls.primary_palette = MD_PRIMARY_PALETTE_ONLINE
            self.theme_cls.accent_palette = MD_ACCENT_PALETTE_ONLINE
            self.switch_screen(HOME_SCREEN_ONLINE)
            self.home_screen = HOME_SCREEN_ONLINE
            icon = 'cloud-outline'
            tooltip_text = 'Switch to TesseracXplore'
        else:
            self.theme_cls.primary_palette = MD_PRIMARY_PALETTE
            self.theme_cls.accent_palette = MD_ACCENT_PALETTE
            self.switch_screen(HOME_SCREEN)
            self.home_screen = HOME_SCREEN
            icon = 'cloud-off-outline'
            tooltip_text = 'Switch to TesseracXploreOnline'
        self.toolbar.right_action_items[0] = [icon, self.toggle_online_offline, tooltip_text]

    def toggle_border(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        # Window fullscreen doesn't work with two displays
        if self.toolbar.right_action_items[1][0] == 'border-all-variant':
            Window.borderless = 0
            icon = 'border-none-variant'
            tooltip_text = 'Borderless'
        else:
            Window.borderless = 1
            icon = 'border-all-variant'
            tooltip_text = 'Window'
        self.toolbar.right_action_items[1] = [icon, self.toggle_border, tooltip_text]

    def toggle_fullscreen(self, *args):
        """ Enable or disable fullscreen, and change icon"""
        # Window fullscreen doesn't work with two displays
        if self.toolbar.right_action_items[2][0] == 'fullscreen-exit':
            Window.restore()
            icon = 'fullscreen'
            tooltip_text = 'Fullscreen'
        else:
            Window.maximize()
            icon = 'fullscreen-exit'
            tooltip_text = 'Normalscreen'
        self.toolbar.right_action_items[2] = [icon, self.toggle_fullscreen, tooltip_text]

    def stop_app(self):
        # self.profile.disable()
        # self.profile.dump_stats('TesseractXplore.profile')
        # self.profile.print_stats(sort='cumulative')
        get_app().stop()


def main():
    TesseractXplore().run()


if __name__ == '__main__':
    main()
