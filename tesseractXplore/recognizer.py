""" Combined entry point for both CLI and GUI """
from tesseractXplore.models.meta_metadata import MetaMetadata
from tesseractXplore.widgets import LoaderProgressBar
from tesseractXplore.app import alert, get_app
from pathlib import Path
from subprocess import PIPE, Popen
from kivymd.toast import toast

def recognize(images, model="eng", psm="4", oem="3", output_folder=None, outputformat="stdout"):
    """
    Get model tags from an iNaturalist gt or model, and write them to local image
    metadata. See :py:func:`~tesseractXplore.cli.tag` for details.
    """
    # TODO: Simplify this a bit
    all_metadata = []
    outputs = []
    app = get_app()
    pb = LoaderProgressBar(color=get_app().theme_cls.primary_color)
    pb.value = 0
    pb.max = len(images)
    status_bar = app.image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    for idx,image_path in enumerate(images):
        if app.tesseract_controller.ocr_stop: break
        pb.update(None, idx+1)
        output = None
        fname_out = None
        params = ["-l", model, "--psm", psm, "--oem", oem]
        if outputformat == "stdout":
            output = outputformat
        else:
            output = Path(image_path).parent.joinpath(Path(image_path).name.rsplit(".",1)[0]) \
                if output_folder is None else Path(output_folder).joinpath(Path(image_path).name)
            fname_out = str(output.absolute()) + {'txt': 'txt', 'hocr': 'hocr', 'alto': 'xml', 'tsv': 'tsv'}.get(
                outputformat, "stdout")
        p1 = Popen(["tesseract", *params, image_path, output, outputformat], stdout=PIPE)
        stdout, stderr = p1.communicate()
        stdout = str(stdout.decode("utf-8"))
        if outputformat == "stdout":
            toast(stdout)
        else:
            toast(fname_out)
        outputs.append(fname_out)
        # TODO: Storing stdout to metadata?
        #keywords = {stdout:True}
        #all_metadata.append(tag_image(image_path, keywords))
    app.tesseract_controller.ocr_stop = False
    pb.finish()
    return idx, outputs


def tag_image(image_path, keywords):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    return metadata
