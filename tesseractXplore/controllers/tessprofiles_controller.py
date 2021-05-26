from functools import partial
from logging import getLogger

from kivy.properties import StringProperty
from kivymd.uix.list import OneLineListItem, TwoLineAvatarIconListItem, IconRightWidget, IconLeftWidget, MDList

from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller
from tesseractXplore.tessprofiles import write_tessprofiles
from tesseractXplore.widgets import LeftCheckbox



logger = getLogger().getChild(__name__)


class CustomOneLineListItem(OneLineListItem):
    icon = StringProperty()


class TessprofilesController(Controller):
    """ Controller class to manage tessprofiles screen """

    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.layout = MDList()

    def get_current_profile(self):
        return get_app().tessprofiles_online if get_app().is_online() else get_app().tessprofiles

    def set_profiles(self, text="", search=False):
        """ Lists all tesseract profiles """

        def add_profile(profile, profileparam, profileparamstr):
            item = TwoLineAvatarIconListItem(
                text=profile,
                secondary_text="Settings: " + profileparamstr,
                on_release=partial(self.load_profile, profileparam),
            )
            item.add_widget(IconRightWidget(icon="trash-can", on_release=partial(self.remove_profile, profile)))
            if 'default' in profileparam and profileparam['default'] == False:
                item.add_widget(IconLeftWidget(icon="star-outline", on_release=partial(self.set_to_default, profile)))
            else:
                item.add_widget(IconLeftWidget(icon="star", on_release=partial(self.unset_default, profile)))
            self.layout.add_widget(item)

        self.layout.clear_widgets()
        self.screen.tessprofilelist.clear_widgets()
        for profilename, profileparam in self.get_current_profile().items():
            profileparamstr = ", ".join([f"{k}:{v}" for k, v in profileparam.items()])
            if search:
                if self.screen.exact_match_chk.active:
                    if text == profilename[:len(text)]:
                        add_profile(profilename, profileparam, profileparamstr)
                else:
                    textparts = text.split(" ")
                    if sum([True if textpart.lower() in profilename.lower() + " " + profileparamstr.lower() else False
                            for textpart in textparts]) == len(textparts):
                        add_profile(profilename, profileparam, profileparamstr)
            else:
                add_profile(profilename, profileparam, profileparamstr)
        self.screen.tessprofilelist.add_widget(self.layout)

    def load_profile(self, profileparam, *args):
        """ Apply all settings of the choosen profile to the main window"""
        if get_app().is_online():
            get_app().tesseract_online_controller.load_tessprofile(profileparam)
        else:
            get_app().tesseract_controller.load_tessprofile(profileparam)
        get_app().switch_screen(get_app().home_screen())

    def set_to_default(self, sel_profile, *args):
        """ Set selected profile as default profile"""
        for profile, profileparam in self.get_current_profile().items():
            if profile == sel_profile:
                profileparam['default'] = True
            else:
                profileparam['default'] = False
        write_tessprofiles(self.get_current_profile(), online=get_app().is_online())
        self.set_profiles(text=self.screen.search_field.text)

    def unset_default(self, sel_profile, *args):
        """ Unset default profile"""
        self.get_current_profile()[sel_profile]['default'] = False
        write_tessprofiles(self.get_current_profile())
        self.set_profiles(text=self.screen.search_field.text)

    def remove_profile(self, profile, *args):
        """ Deletes a profile from the tessprofileslist """
        logger.info(f'TESSPROFILE: Delete {profile}')
        del self.get_current_profile()[profile]
        write_tessprofiles(self.get_current_profile())
        self.set_profiles(text=self.screen.search_field.text)
