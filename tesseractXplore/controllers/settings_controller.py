import subprocess
from locale import getdefaultlocale
from logging import getLogger
from os import makedirs, environ, path
from os.path import isfile, join
from pathlib import Path
from shutil import copyfile, copytree
from sys import platform as _platform

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivymd.app import MDApp
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast

from tesseractXplore.app import alert, get_app
from tesseractXplore.constants import TESSDATA_DIR, FONTS_DIR, DEFAULT_FONTS_DIR
from tesseractXplore.settings import (
    read_settings,
    write_settings,
    reset_defaults,
)
from tesseractXplore.stdout_cache import clear_stdout_cache, get_stdout_cache_size
from tesseractXplore.tesseract import install_tesseract_dialog
from tesseractXplore.thumbnails import delete_thumbnails, get_thumbnail_cache_size
from tesseractXplore.font import get_font_list

logger = getLogger().getChild(__name__)


# TODO: Track whether state changed since last write; if not, don't write on close
class SettingsController:
    """ Controller class to manage Settings screen, and reading from and writing to settings file """

    def __init__(self, settings_screen):
        self.screen = settings_screen
        self.settings_dict = read_settings()

        # Set tessdatapath
        if self.set_tesspaths() and Path(self.settings_dict['tesseract']['tessdatadir_system']).exists():
            self.screen.install_tesseract_btn.disabled = True
        else:
            toast("Please install Tesseract to use the offline version!")

        # Install tesseract
        self.install_tesseract_dialog = install_tesseract_dialog

        # Set default locale if it's unset
        if self.account['locale'] is None:
            self.account['locale'] = getdefaultlocale()[0]

        # self.screen.preferred_place_id_label.bind(
        #    on_release=lambda *x: webbrowser.open(PLACES_BASE_URL)
        # )
        self.screen.dark_mode_chk.bind(active=MDApp.get_running_app().set_theme_mode)
        self.screen.dark_mode_button.bind(on_release=self.change_colormode)
        self.screen.dark_mode_icon.bind(on_release=self.change_colormode)

        self.set_tessdir()

        # Bind buttons (with no persisted value)
        self.screen.reset_default_button.bind(on_release=self.clear_settings)
        self.screen.reset_default_icon.bind(on_release=self.clear_settings)

        # Control widget ids should match the options in the settings file (with suffixes)
        self.controls = {
            id.replace('_chk', '').replace('_input', ''): getattr(settings_screen, id)
            for id in settings_screen
        }
        self.update_control_widgets()

        # Bind buttons
        self.screen.cache_size_output.bind(on_release=self.update_cache_sizes)
        self.screen.clear_stdout_cache_button.bind(on_release=self.clear_stdout_cache)
        self.screen.clear_stdout_cache_icon.bind(on_release=self.clear_stdout_cache)
        self.screen.clear_thumbnail_cache_button.bind(on_release=self.clear_thumbnail_cache)
        self.screen.clear_thumbnail_cache_icon.bind(on_release=self.clear_thumbnail_cache)

        if not Path(FONTS_DIR).exists():
            copytree(DEFAULT_FONTS_DIR, FONTS_DIR)
        self.screen.fontname.values = get_font_list()
        self.screen.tessdatadir_user_sel_chk.bind(on_release=self.set_tessdir)
        self.screen.tessdatadir_userspecific_sel_chk.bind(on_release=self.set_tessdir)
        self.screen.tessdatadir_system_sel_chk.bind(on_release=self.set_tessdir)

        Clock.schedule_once(self.update_cache_sizes, 5)

    def change_colormode(self, *args):
        self.screen.dark_mode_chk.active = not self.screen.dark_mode_chk.active
        get_app().get_running_app().set_theme_mode(is_active=self.screen.dark_mode_chk.active)

    def create_dropdown(self, caller, item, callback):
        menu = MDDropdownMenu(caller=caller,
                              items=item,
                              width_mult=20)
        menu.bind(on_release=callback)
        return menu

    def set_tessdir_btn(self, instance, *args):
        self.set_tessdir()

    def set_tessdir(self, *args):
        for instance in [self.screen.tessdatadir_user_sel_chk, self.screen.tessdatadir_userspecific_sel_chk, self.screen.tessdatadir_system_sel_chk]:
            if instance.state == 'down':
                if instance.text == 'Userwide folder (default)':
                    self.screen['tessdatadir'].set_text(self.screen['tessdatadir'], self.settings_dict['tesseract']['tessdatadir_user'])
                elif instance.text == 'Systemwide folder':
                    self.screen['tessdatadir'].set_text(self.screen['tessdatadir'], self.settings_dict['tesseract']['tessdatadir_system'])
                else:
                    self.screen['tessdatadir'].set_text(self.screen['tessdatadir'], self.settings_dict['tesseract']['tessdatadir_userspecific'])

    def set_tesspaths(self):
        if self.settings_dict['tesseract']['tesspath'] == '':
            if _platform in ["win32","win64"]:
                tessfolder = 'Tesseract-OCR\\tesseract.exe'
                if path.exists(path.join(environ['ProgramFiles(x86)'],tessfolder)):
                    self.settings_dict['tesseract']['tesspath'] = path.join(environ['ProgramFiles(x86)'],tessfolder)
                elif path.exists(path.join(environ['ProgramFiles'],tessfolder)):
                    self.settings_dict['tesseract']['tesspath'] = path.join(environ['ProgramFiles'], tessfolder)
                else:
                    logger.warning("Please set the path to tesseract.exe manually in the settings window")
                    return False
        if self.settings_dict['tesseract']['tessdatadir_system'] == '':
            try:
                if self.settings_dict['tesseract']['tesspath'] != '':
                    # TODO: It seems that the stderr text here is corrupted needs to be checked again
                    tessdatapath = Path(subprocess.run([self.settings_dict['tesseract']['tesspath'], "-l", " ", "xxx", "xxx"], stderr=subprocess.PIPE).stderr.decode('utf-8').splitlines()[0].split("file ",1)[1].rsplit(" ",1)[0])
                    if tessdatapath.exists():
                        self.settings_dict['tesseract']['tessdatadir_system'] = str(tessdatapath)
                    else:
                        tessdatapath = Path(Path(self.settings_dict['tesseract']['tesspath']).drive).joinpath(tessdatapath).joinpath('tessdata')
                        if tessdatapath.exists():
                            self.settings_dict['tesseract']['tessdatadir_system'] = str(tessdatapath)
                else:
                    tessdatapath = Path(subprocess.run(["tesseract", "-l", " ", "xxx", "xxx"], stderr=subprocess.PIPE).stderr.decode('utf-8').splitlines()[0].split("file ")[1].rsplit(" ",1)[0])
                    self.settings_dict['tesseract']['tessdatadir_system'] = str(tessdatapath)
            except:
                logger.warning("Could not find tesseract installation")
                return False
        if self.settings_dict['tesseract']['tessdatadir_user'] == '':
            self.settings_dict['tesseract']['tessdatadir_user'] = TESSDATA_DIR
            self.settings_dict['tesseract']['tessdatadir'] = TESSDATA_DIR
            makedirs(TESSDATA_DIR, exist_ok=True)
        self.copy_models(self.settings_dict['tesseract']['tessdatadir_system'], TESSDATA_DIR, ['osd', 'eng'])
        self.copy_folder([join(self.settings_dict['tesseract']['tessdatadir_system'],'configs'),
                          join(self.settings_dict['tesseract']['tessdatadir_system'],'tessconfigs')],
                          TESSDATA_DIR)
        return True

    def copy_folder(self, folder_dir_list, to_dir, overwrite=False):
        try:
            to_dir = Path(to_dir)
            if to_dir.exists:
                for folder_dir in folder_dir_list:
                    folder_dir = Path(folder_dir)
                    if folder_dir.exists() and (overwrite == True or not to_dir.joinpath(folder_dir.name).exists()):
                        copytree(folder_dir, to_dir.joinpath(folder_dir.name), dirs_exist_ok=True)
        except:
            logger.info(f"Could not copy {folder_dir_list} to {to_dir}")

    def copy_models(self, from_dir, to_dir, modellist):
        for std_model in modellist:
            if isfile(join(from_dir, f"{std_model}.traineddata")) and \
                    not isfile(join(to_dir, f"{std_model}.traineddata")):
                try:
                    copyfile(join(from_dir, f"{std_model}.traineddata"),
                         join(to_dir, f"{std_model}.traineddata"))
                except:
                    logger.info(f"Could not copy {std_model} from {from_dir} to {to_dir}")
        return


    def clear_thumbnail_cache(self, *args):
        logger.info('Settings: Clearing thumbnail cache')
        delete_thumbnails()
        self.update_cache_sizes()
        alert('Cache has been cleared')

    def clear_stdout_cache(self, *args):
        logger.info('Settings: Clearing stdout cache')
        clear_stdout_cache()
        self.update_cache_sizes()
        alert('Cache has been cleared')

    def update_cache_sizes(self, *args):
        """Populate 'Cache Size' sections with calculated totals"""
        out = self.screen.cache_size_output

        num_stdout, stdout_total_size = get_stdout_cache_size()
        out.text = f'Stdout cache size: {num_stdout} files totaling {stdout_total_size}'
        num_thumbs, thumbnail_total_size = get_thumbnail_cache_size()
        out.secondary_text = (
            f'Thumbnail cache size: {num_thumbs} files totaling {thumbnail_total_size}'
        )

    def add_control_widget(self, widget: Widget, setting_name: str, section: str):
        """ Add a control widget from another screen, so its state will be stored with app settings """
        self.controls[setting_name] = widget
        value = self.settings_dict.get(section, {}).get(setting_name)
        self.set_control_value(setting_name, value)
        # Initialize section and setting if either have never been set before
        self.settings_dict.setdefault(section, {})
        self.settings_dict[section].setdefault(setting_name, value)

    def update_control_widgets(self):
        """ Update state of settings controls in UI with values from settings file """
        logger.info(f'Loading settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name, value in section.items():
                self.set_control_value(setting_name, value)

    def save_settings(self):
        """ Save the current state of the control widgets to settings file """
        logger.info(f'Saving settings: {self.settings_dict}')
        for k, section in self.settings_dict.items():
            for setting_name in section.keys():
                value = self.get_control_value(setting_name)
                if value is not None:
                    section[setting_name] = value

        write_settings(self.settings_dict)

    def get_control_value(self, setting_name):
        """ Get the value of the control widget corresponding to a setting """
        control_widget, property, setting_type = self.get_control_widget(setting_name)
        ret = getattr(control_widget, property) if control_widget else None
        if ret is not None and control_widget == "filetypes": ret = ret.split(',')
        return ret

    def set_control_value(self, setting_name, value):
        """ Set the value of the control widget corresponding to a setting """
        control_widget, property, setting_type = self.get_control_widget(setting_name)
        if isinstance(value, list) and setting_type is str:
            value = ",".join(value)
        if control_widget:
            setattr(control_widget, property, setting_type(value))

    def get_control_widget(self, setting_name):
        """  Find the widget corresponding to a setting and detect its type (bool, str, int) """
        # The setting (from file) may not have a corresponding widget on the Settings screen
        if setting_name not in self.controls:
            return None, None, None
        control_widget = self.controls[setting_name]
        if hasattr(control_widget, 'active'):
            return control_widget, 'active', bool
        elif hasattr(control_widget, 'state') and not isinstance(control_widget, MDDropDownItem) and not \
            isinstance(control_widget, Spinner):
            return control_widget, 'state', str
        elif hasattr(control_widget, 'text'):
            return control_widget, 'text', str
        if hasattr(control_widget, 'path'):
            return control_widget, 'path', str
        else:
            logger.warning(f'Could not detect type for {control_widget}')

    def clear_settings(self, *args):
        reset_defaults()
        self.update_control_widgets()
        alert('Settings have been reset to defaults')

    @property
    def locale(self):
        return self.account.get('locale')

    @property
    def username(self):
        return self.account.get('username')

    @property
    def password(self):
        return self.account.get('password')

    @property
    def account(self):
        return self.settings_dict['account']

    @property
    def display(self):
        return self.settings_dict['display']

    @property
    def tesseract(self):
        return self.settings_dict['tesseract']

    @property
    def viewer(self):
        return self.settings_dict['viewer']

    @property
    def pdfviewer(self):
        return self.viewer['pdfviewer']
