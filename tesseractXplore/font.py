from logging import getLogger
import os

from kivy.core.text import LabelBase
from kivy.utils import reify
from kivy.core.text import Label as CoreLabel
from kivy.resources import resource_find, resource_add_path
from kivymd.font_definitions import theme_font_styles

from tesseractXplore.app import get_app
from tesseractXplore.constants import  FONTS_DIR


logger = getLogger().getChild(__name__)


def get_font_list():
    '''Get a list of all the fonts available on this system.
    '''
    CoreLabel._fonts_dirs.append(FONTS_DIR)
    fonts_path = CoreLabel.get_system_fonts_dir()
    flist = []
    resource_add_path(FONTS_DIR)
    for fdir in fonts_path:
        for fpath in sorted(os.listdir(fdir)):
            if fpath.endswith('.ttf'):
                flist.append(fpath[:-4])
    return sorted(flist)

def get_font():
    return get_app().settings_controller.screen.fontname.text

def get_fontsize():
    return get_app().settings_controller.screen.fontsize.text

def get_fontstyle():
    fontname = get_font()
    filename = resource_find(fontname)
    if not filename and not fontname.endswith('.ttf'):
        fontname = '{}.ttf'.format(fontname)
        filename = resource_find(fontname)
    try:
        LabelBase.register(
            name=fontname,
            fn_regular=filename)
        theme_font_styles.append(fontname)
        get_app().theme_cls.font_styles[fontname] = [fontname, int(get_app().settings_controller.screen.fontsize.text), False, 0.15]
        return fontname
    except:
        return "Body1"