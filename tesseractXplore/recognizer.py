""" Combined entry point for both CLI and GUI """
import time
from functools import partial
from pathlib import Path
from shutil import move
from subprocess import PIPE, Popen

from kivy.uix.textinput import TextInput
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

from tesseractXplore.app import get_app
from tesseractXplore.evaluate import evaluate_report
from tesseractXplore.models.meta_metadata import MetaMetadata
from tesseractXplore.stdout_cache import write_stdout_cache
from tesseractXplore.widgets import LoaderProgressBar


def recognize(images, model="eng", psm="4", oem="3", tessdatadir=None, output_folder=None, outputformats=None,
              print_on_screen=True, subfolder=False, groupfolder=""):
    """
    OCR with tesseract on images
    """
    # TODO: Simplify this a bit
    all_metadata = []
    outputs = []
    app = get_app()
    pb = LoaderProgressBar(color=get_app().theme_cls.primary_color)
    pb.value = 0
    pb.max = len(images) + 1
    status_bar = app.image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    for idx, image in enumerate(images):
        if app.tesseract_controller.ocr_stop: break
        pb.update(None, idx + 1)
        output = None
        params = ["-l", model, "--psm", psm, "--oem", oem, ]
        if tessdatadir:
            params.extend(["--tessdata-dir", tessdatadir])
        if not app.settings_controller.controls['do_invert'].active:
            params.extend(['-c', 'tessedit_do_invert=0'])
        if app.settings_controller.controls['dpi'].text.isdigit():
            params.extend(['--dpi', app.settings_controller.controls['dpi']])
        if app.settings_controller.controls['extra_param'].text != "":
            for param in app.settings_controller.controls['extra_param'].text.split(' '):
                params.extend(['-c', param])
        if not outputformats or print_on_screen:
            tesscmd = get_app().settings_controller.tesseract['tesspath'] if get_app().settings_controller.tesseract['tesspath'] != "" else "tesseract"
            p1 = Popen([tesscmd, *params, image, 'stdout', *outputformats], stdout=PIPE)
        else:
            image_path = Path(image)
            output = image_path.parent.joinpath(image_path.name.rsplit(".", 1)[0]) \
                if output_folder is None else Path(output_folder).joinpath(image_path.name)
            tesscmd = get_app().settings_controller.tesseract['tesspath'] if get_app().settings_controller.tesseract['tesspath'] != "" else "tesseract"
            p1 = Popen([tesscmd, *params, image_path, output, *outputformats], stdout=PIPE)
        stdout, stderr = p1.communicate()
        stdout = str(stdout.decode("utf-8"))
        if not outputformats or print_on_screen:
            pimage = Path(image)
            dialog = MDDialog(title=pimage.name,
                              type='custom',
                              auto_dismiss=False,
                              content_cls=TextInput(text=stdout, size_hint_y=None, height=get_app()._window.size[1]-150, readonly=True),
                              buttons=[
                                  MDFlatButton(
                                      text="EVALUATE", on_release=partial(evaluate_report, stdout)
                                  ),
                                  MDFlatButton(
                                      text="SAVE", on_release=partial(cache_stdout_dialog, pimage, stdout, params)
                                  ),
                                  MDFlatButton(
                                      text="DISCARD", on_release=close_dialog
                                  ),
                              ],
                              )
            if get_app()._platform not in ['win32','win64']:
                # TODO: Focus function seems buggy in win
                dialog.content_cls.focused = True
            # TODO: There should be a better way to set cursor to 0,0
            time.sleep(0.2)
            dialog.content_cls.cursor = (0, 0)
            dialog.open()
        else:
            # TODO: Make it less ugly
            new_path = image_path.parent
            if groupfolder != "":
                new_path = new_path.joinpath(groupfolder)
                if not new_path.exists(): new_path.mkdir()
            for outputformat in outputformats:
                out_path = new_path
                if subfolder:
                    out_path = out_path.joinpath(outputformat.upper())
                    if not out_path.exists(): out_path.mkdir()
                if out_path != image_path.parent:
                    if outputformat == "alto": outputformat = "xml"
                    # print(str(image_path.parent.joinpath(output.name+"."+outputformat)))
                    # print(str(out_path.joinpath(output.name+"."+outputformat)))
                    move(str(image_path.parent.joinpath(output.name + "." + outputformat).absolute()),
                         str(out_path.joinpath(output.name + "." + outputformat).absolute()))

            toast(output.name)
        outputs.append(output)
        # TODO: Storing stdout to metadata?
        # keywords = {stdout:True}
        # all_metadata.append(tag_image(image_path, keywords))
    app.tesseract_controller.ocr_stop = False
    pb.finish()
    return idx + 1, outputs


def close_dialog(instance, *args):
    instance.parent.parent.parent.parent.dismiss()


def cache_stdout_dialog(image: Path, text: str, params: list, instance, *args):
    instance.parent.parent.parent.parent.dismiss()
    dialog = MDDialog(title=image.name,
                      type='custom',
                      auto_dismiss=False,
                      content_cls=MDTextField(text=""),
                      buttons=[
                          MDFlatButton(
                              text="SAVE", on_release=partial(cache_stdout, image, text, params)
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


def cache_stdout(image, text, params, instance, *args):
    id = instance.parent.parent.parent.parent.content_cls.text
    write_stdout_cache(image, id, text, params)
    instance.parent.parent.parent.parent.dismiss()


def tag_image(image_path, keywords):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    return metadata
