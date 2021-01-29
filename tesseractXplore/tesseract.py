from logging import getLogger
from sys import platform as _platform
from subprocess import Popen, run, PIPE,DEVNULL, STDOUT
from pathlib import Path

import requests
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton
from kivymd.toast import toast
from functools import partial

from tesseractXplore.constants import DATA_DIR


logger = getLogger().getChild(__name__)


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
    dialog.content_cls.focused = True
    dialog.open()

def install_tesseract(instance):
    instance.parent.parent.parent.parent.dismiss()
    if _platform in ["win32", "win64"]:
        install_win()
    else:
        install_unix_dialog()

def install_win():
    try:
        if _platform == "win32":
            url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w32-setup-v5.0.0-alpha.20201127.exe"
        else:
            url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.0.0-alpha.20201127.exe"
        r = requests.get(url)
        fout = Path(DATA_DIR).joinpath("tesseract.exe")
        logger.info(fout)
        with open(fout, 'wb') as f:
            f.write(r.content)
        toast('Download: Succesful')
        logger.info(f'Download: Succesful')
        from os import startfile
        startfile(fout)
    except Exception as e:
        print(e)
        toast('Download: Error')
        logger.info(f'Download: Error while downloading')


def install_unix_dialog():
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()
    layout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
    layout.add_widget(MDTextField(hint_text="Password",password=True))
    dialog = MDDialog(title="Enter sudo password to change the rights of the destination folder",
                      type='custom',
                      auto_dismiss=False,
                      content_cls=layout,
                      buttons=[
                          MDFlatButton(
                              text="ENTER", on_release=partial(install_unix)
                          ),
                          MDFlatButton(
                              text="DISCARD", on_release=close_dialog
                          ),
                      ],
                      )
    dialog.content_cls.focused = True
    dialog.open()

def install_unix(instance, *args):
    pwd = instance.parent.parent.parent.parent.content_cls.children[0].text
    instance.parent.parent.parent.parent.dismiss()
    install_tesseract = Popen(['sudo', '-S', 'ap-get', 'install', '-y', 'tesseract-ocr'],
                           stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    install_tesseract.stdin.write(bytes(pwd, 'utf-8'))
    install_tesseract.communicate()
    return