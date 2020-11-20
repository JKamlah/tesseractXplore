""" Combined entry point for both CLI and GUI """
from tesseractXplore.models.meta_metadata import MetaMetadata
from tesseractXplore.widgets import LoaderProgressBar
from tesseractXplore.app import alert, get_app

from pathlib import Path
from subprocess import PIPE, Popen
from shutil import move
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.textinput import TextInput

def recognize(images, model="eng", psm="4", oem="3", output_folder=None, outputformats=None, subfolder=False, groupfolder=""):
    """
    OCR with tesseract on images
    """
    # TODO: Simplify this a bit
    all_metadata = []
    outputs = []
    idx = -1
    app = get_app()
    pb = LoaderProgressBar(color=get_app().theme_cls.primary_color)
    pb.value = 0
    pb.max = len(images)
    status_bar = app.image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    for idx,image in enumerate(images):
        if app.tesseract_controller.ocr_stop: break
        pb.update(None, idx+1)
        output = None
        params = ["-l", model, "--psm", psm, "--oem", oem]
        if not outputformats:
            p1 = Popen(["tesseract", *params, image, 'stdout'], stdout=PIPE)
        else:
            image_path = Path(image)
            output = image_path.parent.joinpath(image_path.name.rsplit(".",1)[0]) \
                if output_folder is None else Path(output_folder).joinpath(image_path.name)
            p1 = Popen(["tesseract", *params, image_path, output, *outputformats], stdout=PIPE)
        stdout, stderr = p1.communicate()
        stdout = str(stdout.decode("utf-8"))
        if not outputformats:
            dialog = MDDialog(title=output.name,
                     type='custom',
                     content_cls=TextInput(text=stdout, height=400, cursor=(0,0),focus= True, readonly=True),
                     buttons=[
                        MDFlatButton(
                            text="DISCARD", on_release=close_dialog
                        ),
                    ],
                )
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
                    print(str(image_path.parent.joinpath(output.name+"."+outputformat)))
                    print(str(out_path.joinpath(output.name+"."+outputformat)))
                    move(str(image_path.parent.joinpath(output.name+"."+outputformat).absolute()),
                             str(out_path.joinpath(output.name+"."+outputformat).absolute()))

            toast(output.name)
        outputs.append(output)
        # TODO: Storing stdout to metadata?
        #keywords = {stdout:True}
        #all_metadata.append(tag_image(image_path, keywords))
    app.tesseract_controller.ocr_stop = False
    pb.finish()
    return idx+1, outputs

def close_dialog(instance, *args):
    instance.dismiss()

def tag_image(image_path, keywords):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    return metadata
