""" Combined entry point for both CLI and GUI """
from tesseractXplore.models.meta_metadata import MetaMetadata
from pathlib import Path
from subprocess import PIPE, Popen
from kivymd.toast import toast


def recognize(images, model="eng", psm="4", oem="3", output_folder=None, outputformat="stdout"):
    """
    Get taxonomy tags from an iNaturalist observation or taxon, and write them to local image
    metadata. See :py:func:`~tesseractXplore.cli.tag` for details.
    """
    # TODO: Simplify this a bit
    all_metadata = []
    outputs = []
    for image_path in images:
        output = None
        params = ["-l", model, "--psm", psm, "--oem", oem]
        if outputformat == "stdout":
            output = outputformat
        else:
            output = Path(image_path).parent.joinpath(Path(image_path).name.rsplit(".",1)[0]) \
                if output_folder is None else Path(output_folder).joinpath(Path(image_path).name)
        p1 = Popen(["tesseract", *params, image_path, output, outputformat], stdout=PIPE)
        stdout, stderr = p1.communicate()
        stdout = str(stdout.decode("utf-8"))
        fname_out = str(output.absolute())+{'txt':'txt','hocr':'hocr','alto':'xml','tsv':'tsv'}[outputformat]
        if outputformat == "stdout":
            toast(stdout)
        else:
            toast(fname_out)
        outputs.append(fname_out)
        # TODO: Storing stdout to metadata?
        #keywords = {stdout:True}
        #all_metadata.append(tag_image(image_path, keywords))
    return outputs


def tag_image(image_path, keywords):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    return metadata
