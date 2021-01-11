from logging import getLogger
from kivymd.uix.list import OneLineListItem, TwoLineAvatarIconListItem, IconRightWidget, MDList
from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller
from kivy.properties import StringProperty
from functools import partial

from tesseractXplore.tessprofiles import write_tessprofiles

logger = getLogger().getChild(__name__)

class CustomOneLineListItem(OneLineListItem):
    icon = StringProperty()

class TessprofilesController(Controller):
    """ Controller class to manage tessprofiles screen """
    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.layout = MDList()

    def set_profiles(self, text="", search=False):
        """ Lists all tesseract profiles """
        def add_profile(profile, profileparam, profileparamstr):
            item = TwoLineAvatarIconListItem(
                    text= profile,
                    secondary_text= "Settings: " + profileparamstr,
                    on_release= partial(self.load_profile, profileparam),
            )
            item.add_widget(IconRightWidget(icon= "trash-can",on_release=partial(self.remove_profile,profile)))
            self.layout.add_widget(item)

        self.layout.clear_widgets()
        self.screen.tessprofilelist.clear_widgets()
        for profilename, profileparam in get_app().tessprofiles.items():
            profileparamstr = ", ".join([f"{k}:{v}" for k, v in profileparam.items()])
            if search:
                if self.screen.exact_match_chk.active:
                    if text == profilename[:len(text)]:
                        add_profile(profilename, profileparam, profileparamstr)
                else:
                    textparts = text.split(" ")
                    if sum([True if textpart.lower() in profilename.lower()+" "+profileparamstr.lower() else False for textpart in textparts]) == len(textparts):
                        add_profile(profilename, profileparam, profileparamstr)
            else:
                add_profile(profilename, profileparam, profileparamstr)
        self.screen.tessprofilelist.add_widget(self.layout)

    def load_profile(self, profileparam, *args):
        """ Apply all settings of the choosen profile to the main window"""
        get_app().tesseract_controller.load_tessprofile(profileparam)
        get_app().switch_screen('tesseract_xplore')

    def remove_profile(self, profile, *args):
        """ Deletes a profile from the tessprofileslist """
        logger.info(f'TESSPROFILE: Delete {profile}')
        del get_app().tessprofiles[profile]
        write_tessprofiles(get_app().tessprofiles)
        self.set_profiles(text=self.screen.search_field.text)



