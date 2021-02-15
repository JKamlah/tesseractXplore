import threading
from functools import partial
from logging import getLogger
from os import makedirs
from pathlib import Path
import re
from subprocess import Popen, run, getstatusoutput, check_output
from sys import platform as _platform

from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem, OneLineAvatarListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

from tesseractXplore.widgets import MyToggleButton
from tesseractXplore.app import alert, get_app
from tesseractXplore.constants import PDF_DIR
from tesseractXplore.widgets.lists import SwitchListItem
from kivymd.uix.progressbar import MDProgressBar


logger = getLogger().getChild(__name__)


def pdf_dialog(pdfpath,cmds):
    # Called by image_glob.py
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()

    layout = MDList()
    pdfinfos = check_output([cmds["pdfimages"], "-list", pdfpath]).decode('utf-8')
    pdfinfos = re.sub(r' +', ' ', pdfinfos)
    pdfinfos = pdfinfos.split("\n")[2:-1]
    pages = str(len(pdfinfos))
    if pages != "0":
        dpis = [pdfinfo.split(" ")[-3] for pdfinfo in pdfinfos]
        from collections import Counter
        dpi = Counter(dpis).most_common(1)[0][0]
    else:
        pdfinfos = check_output([cmds["pdfinfo"], pdfpath]).decode('utf-8')
        pages = pdfinfos.split("\n")[9].split(": ")[-1].strip()
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
    boxlayout.add_widget(MyToggleButton(text="rendering", group="converting"))
    defaulttoggle = MyToggleButton(text="extraction", group="converting")
    boxlayout.add_widget(defaulttoggle)
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


def pdfimages_threading(pdfpath, cmds, instance, *args):
    instance.parent.parent.parent.parent.dismiss()
    pdfimages_thread = threading.Thread(target=pdfimages, args=(pdfpath, cmds, instance, args))
    pdfimages_thread.setDaemon(True)
    pdfimages_thread.start()


def open_pdf(fname, *args):
    """ Open a pdf via webbrowser or another external software """
    pdfviewer = get_app().settings_controller.pdfviewer
    if pdfviewer == 'webbrowser':
        import webbrowser
        webbrowser.open(str(Path(fname).absolute()))
    else:
        try:
            run([pdfviewer, str(Path(fname).absolute())])
        except:
            alert(f"Couldn't find: {pdfviewer}")
            pass


def pdfimages(pdfpath, cmds, instance, *args):
    pb = MDProgressBar(color=get_app().theme_cls.primary_color, type="indeterminate")
    status_bar = get_app().image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    pb.start()
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
    p1 = Popen([process, *params, pdfpath, pdfdir.joinpath(pdfdir.name)])
    p1.communicate()
    get_app().image_selection_controller.file_chooser._update_files()
    get_app().image_selection_controller.add_images([pdfdir])
    pb.stop()


def extract_pdf(pdfpath):
    if _platform not in ["win32", "win64"]:
        if getstatusoutput("pdfimages")[0] not in [1, 127]:
            cmds ={"pdfimages":"pdfimages",
                   "pdfinfo":"pdfinfo",
                   "pdftoppm":"pdftoppm"}
            pdf_dialog(pdfpath, cmds)
            return pdfpath.split(".")[0]
        else:
            toast("Please install Poppler-utils to work convert PDFs to images with:")
            toast("sudo apt-get install poppler-utils")
    else:
        pdftoolpath = Path(PDF_DIR)
        if not pdftoolpath.exists():
            # TODO: Don work atm properly and use the official site
            try:
                install_win(pdftoolpath)
            except:
                logger.info(f'Download: Error while downloading')
                return
        binpath = list(pdftoolpath.glob("./**/**/bin"))[0]
        cmds = {"pdfimages": str(binpath.joinpath("pdfimages.exe").absolute()),
                "pdfinfo": str(binpath.joinpath("pdfinfo.exe").absolute()),
                "pdftoppm": str(binpath.joinpath("pdftoppm.exe").absolute())}
        pdf_dialog(pdfpath,cmds)
    return pdfpath

def install_win(pdftoolpath):
    import requests, zipfile, io
    url = 'https://digi.bib.uni-mannheim.de/~jkamlah/poppler-0.68.0_x86.zip'
    #url = 'http://blog.alivate.com.au/wp-content/uploads/2018/10/poppler-0.68.0_x86.7z'
    r = requests.get(url, stream=True)
    pdftoolpath.mkdir(parents=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(str(pdftoolpath.absolute()))
    toast('Download: Poppler succesful')
    logger.info(f'Download: Succesful')