import tempfile
import threading
from functools import partial
from logging import getLogger
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL, STDOUT
from sys import platform as _platform

from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem

from tesseractXplore.app import get_app
from tesseractXplore.downloader import download_with_progress, switch_to_home_for_dl
from tesseractXplore.unix import run_cmd_with_sudo_dialog

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
        switch_to_home_for_dl()
        toast('Download: Tesseract installer\nThe app will be closed and the installer will be started automatically!')
        dl_install_tesseract_win()
    else:
        run_cmd_with_sudo_dialog(title="Enter sudo password to change the rights of the destination folder",func=thread_install_tesseract_unix)

def dl_install_tesseract_win():
    try:
        if _platform == "win32":
            url = get_app().settings_controller.tesseract['win32url']
        else:
            url = get_app().settings_controller.tesseract['win64url']
        download_with_progress(url, Path(tempfile.gettempdir()).joinpath("tesseract.exe"), install_tesseract_win)
    except Exception as e:
        print(e)
        toast('Download: Error')
        logger.info(f'Download: Error while downloading')

def install_tesseract_win(instance, *args):
    toast('Download: Succesful')
    logger.info(f'Download: Succesful')
    from os import startfile
    startfile(Path(tempfile.gettempdir()).joinpath("tesseract.exe"))
    reset_tesspaths()
    get_app().stop()

def thread_install_tesseract_unix(instance, *args):
    instance.parent.parent.parent.parent.dismiss()
    switch_to_home_for_dl()
    toast('Installing: Tesseract\nThe app will be closed after installation automatically!')
    th_install = threading.Thread(target=install_tesseract_unix, kwargs={'instance':instance})
    th_install.setDaemon(True)
    th_install.start()

def install_tesseract_unix(instance=None):
    install_tesseract = Popen(['sudo', '-S', 'apt-get', 'install', '-y', 'tesseract-ocr'],
                           stdin=PIPE)
    install_tesseract.stdin.write(bytes(instance.parent.parent.parent.parent.content_cls.children[0].text, 'utf-8'))
    install_tesseract.communicate()
    reset_tesspaths()
    get_app().stop()
    return