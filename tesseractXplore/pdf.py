import re
import tempfile
import threading
import webbrowser
from functools import partial
from logging import getLogger
from os import makedirs
from pathlib import Path
from subprocess import Popen, run, getstatusoutput, check_output, DEVNULL, STDOUT, PIPE
from sys import platform as _platform

import io
import requests
import zipfile
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem, OneLineAvatarListItem
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.textfield import MDTextField

from tesseractXplore.app import alert, get_app
from tesseractXplore.constants import PDF_DIR
from tesseractXplore.widgets import LoaderProgressBar
from tesseractXplore.widgets import MyToggleButton
from tesseractXplore.widgets.lists import SwitchListItem
from tesseractXplore.process_manager import create_threadprocess

logger = getLogger().getChild(__name__)


def pdf_dialog(pdfpath,cmds):
    """ Start dialog to ocr a pdf, start a pdf viewer or convert pdf to images"""
    # Called by image_glob.py
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()

    layout = MDList()
    try:
        pdfinfos = str(check_output([cmds["pdfimages"], "-list", pdfpath], universal_newlines=True))
        pdfinfos = re.sub(r' +', ' ', pdfinfos)
        pdfinfos = pdfinfos.split("\n")[2:-1]
        pages = str(len(pdfinfos))
        if pages != "0":
            dpis = [pdfinfo.split(" ")[-3] for pdfinfo in pdfinfos]
            from collections import Counter
            dpi = Counter(dpis).most_common(1)[0][0]
        else:
            pdfinfos = str(check_output([cmds["pdfinfo"], pdfpath], universal_newlines=True))
            for info in pdfinfos.split("\n"):
                if "Pages:" in info[:7]:
                    pages = info.split(": ")[-1].strip()
            dpi = 300
        layout.add_widget(OneLineListItem(text=f'The detected resolution is: {dpi}'))
        layout.add_widget(OneLineListItem(text='First page'))
        # id first
        layout.add_widget(MDTextField(text="0", hint_text="First page", height=(get_app()._window.size[1])//2))
        layout.add_widget(OneLineListItem(text='Last page'))
        # id last
        layout.add_widget(MDTextField(text=pages, hint_text="Last page", height=(get_app()._window.size[1])//2))
        layout.add_widget(OneLineListItem(text='Imageformat (jpg, jp2, png, ppm(default), tiff)'))
        # id = "fileformat"
        boxlayout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
        boxlayout.add_widget(MyToggleButton(text="jpeg", group="imageformat"))
        boxlayout.add_widget(MyToggleButton(text="jp2", group="imageformat"))
        defaulttoggle = MyToggleButton(text="ppm", group="imageformat")
        boxlayout.add_widget(defaulttoggle)
        boxlayout.add_widget(MyToggleButton(text="png", group="imageformat"))
        boxlayout.add_widget(MyToggleButton(text="tiff", group="imageformat"))
        layout.add_widget(boxlayout)
        layout.add_widget(OneLineListItem(text='Process to convert PDF to images'))
        # id="converting",
        boxlayout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
        defaulttoggle = MyToggleButton(text="rendering", group="converting")
        boxlayout.add_widget(defaulttoggle)
        boxlayout.add_widget(MyToggleButton(text="extraction", group="converting"))
        layout.add_widget(boxlayout)
        # id='include_pagenumber',
        pagenumbers = OneLineAvatarListItem(text='Include page numbers in output file names')
        # id = 'include_pagenumber_chk'
        pagenumbers.add_widget(SwitchListItem())
        layout.add_widget(pagenumbers)
        dialog = MDDialog(title="Extract images from PDF",
                          type='custom',
                          auto_dismiss=False,
                          text=pdfpath,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="OCR", on_release=partial(pdfimages_threading, pdfpath, cmds, ocr=True)
                              ),
                              MDFlatButton(
                                  text="CREATE IMAGES", on_release=partial(pdfimages_threading, pdfpath, cmds)
                              ),
                              MDFlatButton(
                                  text="VIEW PDF", on_release=partial(open_pdf, pdfpath)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        defaulttoggle.state = 'down'

        if get_app()._platform not in ['win32', 'win64']:
        # TODO: Focus function seems buggy in win
            dialog.content_cls.focused = True
        dialog.open()
    except:
        logger.error(f"Error while reading information from {pdfpath}")
        toast(f"Error while reading information from {pdfpath}")



def pdfimages_threading(pdfpath, cmds, instance, ocr=False, *args):
    """ Start pdfimages in a separate thread"""
    instance.parent.parent.parent.parent.dismiss()
    create_threadprocess("Working with pdf", pdfimages, [pdfpath, cmds, instance, ocr, args])
    #pdfimages_thread = threading.Thread(target=pdfimages, args=(pdfpath, cmds, instance, ocr, args))
    #pdfimages_thread.setDaemon(True)
    #pdfimages_thread.start()


def open_pdf(fname, *args):
    """ Open a pdf via webbrowser or another external software """
    pdfviewer = get_app().settings_controller.pdfviewer
    if pdfviewer == 'webbrowser':
        webbrowser.open(str(Path(fname).absolute()))
    else:
        try:
            run([pdfviewer, str(Path(fname).absolute())])
        except:
            alert(f"Couldn't find: {pdfviewer}")
            pass


def pdfimages(pdfpath, cmds, instance, ocr, *args):
    """ Converts the pdf to images"""
    pb = MDProgressBar(color=get_app().theme_cls.primary_color, type="indeterminate")
    status_bar = get_app().image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    pb.start()
    if ocr:
        tmpdir = tempfile.TemporaryDirectory()
        pdfdir = Path(tmpdir.name)
    else:
        pdfdir = Path(pdfpath.split('.')[0])
        makedirs(pdfdir, exist_ok=True)
    params = []
    children = instance.parent.parent.parent.parent.content_cls.children
    process = cmds["pdfimages"]
    for idx, child in enumerate(reversed(children)):
        if idx == 6:
            for fileformat in child.children:
                if fileformat.state == 'down':
                    params.extend([f"-{fileformat.text}"])
        if idx == 2 and child.text != "":
            params.extend(["-f", child.text])
        if idx == 4 and child.text != "":
            params.extend(["-l", child.text])
        if idx == 9 and child.ids['_left_container'].children[0].active:
            params.extend(["-p"])
        if idx == 8:
            for convprocess in child.children:
                if convprocess.state == 'down':
                    if convprocess.text == "rendering":
                        process = cmds["pdftoppm"]
                    else:
                        process = cmds["pdfimages"]
                        fileformat.text = "j" if fileformat.text == "jpeg" else fileformat.text
                        fileformat.text = "jpeg" if fileformat.text == "jp2" else fileformat.text
    p1 = Popen([process, *params, pdfpath, pdfdir.joinpath(Path(pdfpath.split('.')[0]).name)])
    p1.communicate()
    get_app().image_selection_controller.file_chooser._update_files()
    if not ocr:
        get_app().image_selection_controller.add_images([pdfdir])
    else:
        images = list(pdfdir.glob('*.*'))
        tc_screen = get_app().tesseract_controller
        thread = tc_screen.recognize_thread(None,file_list=images, profile={'outputformats':['pdf'],'groupfolder':'','subforlder' : False, 'print_on_screen' : False})
        thread.join()
        p2 = Popen([cmds["pdfunite"], *sorted(list(pdfdir.glob('*.pdf'))), pdfpath[:-3]+"ocr.pdf"])
        p2.communicate()
    get_app().image_selection_controller.file_chooser._update_files()
    pb.stop()


def extract_pdf(pdfpath):
    """ Check if all necessary tools for pdf extraction are available and than start the extraction dialog or the installtion"""
    if _platform not in ["win32", "win64"]:
        if getstatusoutput("pdfimages")[0] not in [1, 127]:
            cmds ={"pdfimages":"pdfimages",
                   "pdfinfo":"pdfinfo",
                   "pdftoppm":"pdftoppm",
                   "pdfunite":"pdfunite"}
            pdf_dialog(pdfpath, cmds)
            return pdfpath.split(".")[0]
        else:
            from tesseractXplore.unix import run_cmd_with_sudo_dialog
            run_cmd_with_sudo_dialog(title="Installing Poppler",func=install_poppler_unix_thread)
    else:
        pdftoolpath = Path(PDF_DIR)
        if not pdftoolpath.exists():
            # TODO: Don work atm properly and use the official site
            try:
                create_threadprocess("Installing poppler utils", install_poppler_win,[],**{'pdftoolpath':str(pdftoolpath.absolute())})
                #dl_event = threading.Thread(target=install_poppler_win, kwargs=())
                #dl_event.setDaemon(True)
                #dl_event.start()
            except:
                logger.info(f'Download: Error while downloading')
        else:
            binpath = list(pdftoolpath.glob("./**/**/bin"))[0]
            cmds = {"pdfimages": str(binpath.joinpath("pdfimages.exe").absolute()),
                "pdfinfo": str(binpath.joinpath("pdfinfo.exe").absolute()),
                "pdftoppm": str(binpath.joinpath("pdftoppm.exe").absolute()),
                "pdfunite": str(binpath.joinpath("pdfunite.exe").absolute())}
            pdf_dialog(pdfpath,cmds)
    return pdfpath

def start_installing_loaderprogress():
    """ Start a progress and set the state to 50%"""
    pb = LoaderProgressBar(color=get_app().theme_cls.primary_color)
    pb.value = 0
    pb.max = 2
    status_bar = get_app().image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    pb.update(None, 1)
    return pb

def install_poppler_unix_thread(instance, *args):
    """ Start poppler installation in an extra thread"""
    instance.parent.parent.parent.parent.dismiss()
    dl_event = threading.Thread(target=install_poppler_unix, kwargs=({'sudopwd':instance.parent.parent.parent.parent.content_cls.children[0].text}))
    dl_event.setDaemon(True)
    dl_event.start()


def install_poppler_unix(sudopwd=""):
    """ Installation of poppler utils on unix os"""
    pb = start_installing_loaderprogress()
    install_tesseract = Popen(['sudo', '-S', 'apt-get', 'install', '-y', 'poppler-utils'],
                              stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    install_tesseract.stdin.write(bytes(sudopwd, 'utf-8'))
    install_tesseract.communicate()
    pb.finish()
    toast('Installing: Poppler succesful\nEnable: Working with PDFs')
    logger.info(f'Installing: Succesful')
    return

def install_poppler_win(pdftoolpath=None):
    """ Installation of poppler utils on win platforms"""
    try:
        url = 'https://digi.bib.uni-mannheim.de/~jkamlah/poppler-0.68.0_x86.zip'
        r = requests.get(url, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        Path(pdftoolpath).mkdir(parents=True)
        z.extractall(pdftoolpath)
        toast('Installing: Poppler succesful\nEnable: Working with PDFs')
        logger.info(f'Installing: Succesful')
    except:
        toast('Installing: Poppler not succesful')
        logger.info(f'Download: Not succesful')
