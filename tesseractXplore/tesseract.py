import tempfile
from logging import getLogger
from os import startfile
from sys import platform as _platform
from subprocess import Popen, PIPE,DEVNULL, STDOUT
from pathlib import Path

import requests
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.toast import toast
from functools import partial

from tesseractXplore.unix import run_cmd_with_sudo_dialog
from tesseractXplore.app import get_app

logger = getLogger().getChild(__name__)

def reset_tesspaths():
    """ Reset tesspaths to default """
    sc = get_app().settings_controller
    sc.settings_dict['tesseract']['tesspath'] = ""
    sc.settings_dict['tesseract']['tessdatadir'] = ""
    sc.settings_dict['tesseract']['tessdatadir_system'] = ""
    sc.settings_dict['tesseract']['tessdatadir_user'] = ""
    sc.save_settings()

def install_tesseract_dialog():
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()
    layout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
    layout.add_widget(OneLineListItem(text="Tesseract wasn't found on the system. You can install it now or set"
                                           "the right path in the settings-menu. (Restart required)"))
    dialog = MDDialog(title="Installing tesseract?",
                      type='custom',
                      auto_dismiss=False,
                      content_cls=layout,
                      buttons=[
                          MDFlatButton(
                              text="INSTALL", on_release=partial(install_tesseract)
                          ),
                          MDFlatButton(
                              text="DISCARD", on_release=close_dialog
                          ),
                      ],
                      )
    if get_app()._platform not in ['win32', 'win64']:
    # TODO: Focus function seems buggy in win
        dialog.content_cls.focused = True
    dialog.open()

def install_tesseract(instance):
    instance.parent.parent.parent.parent.dismiss()
    if _platform in ["win32", "win64"]:
        install_tesseract_win()
    else:
        run_cmd_with_sudo_dialog(title="Enter sudo password to change the rights of the destination folder",func=install_tesseract_unix)

def install_tesseract_win():
    try:
        if _platform == "win32":
            url = get_app().settings_controller.tesseract['win32url']
        else:
            url = get_app().settings_controller.tesseract['win64url']
        r = requests.get(url)
        fout = Path(tempfile.gettempdir()).joinpath("tesseract.exe")
        logger.info(f"Creating: {fout}")
        with open(fout, 'wb') as f:
            f.write(r.content)
        toast('Download: Succesful')
        logger.info(f'Download: Succesful')
        startfile(fout)
        reset_tesspaths()
        get_app().stop()
    except Exception as e:
        print(e)
        toast('Download: Error')
        logger.info(f'Download: Error while downloading')

def install_tesseract_unix(instance, *args):
    pwd = instance.parent.parent.parent.parent.content_cls.children[0].text
    instance.parent.parent.parent.parent.dismiss()
    install_tesseract = Popen(['sudo', '-S', 'apt-get', 'install', '-y', 'tesseract-ocr'],
                           stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    install_tesseract.stdin.write(bytes(pwd, 'utf-8'))
    install_tesseract.communicate()
    reset_tesspaths()
    get_app().stop()
    return