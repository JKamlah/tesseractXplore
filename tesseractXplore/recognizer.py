""" Combined entry point for both CLI and GUI """
from tesseractXplore.models.meta_metadata import MetaMetadata
from tesseractXplore.inat_metadata import get_keywords
from pathlib import Path
from subprocess import PIPE, Popen
from kivymd.toast import toast


def recognize(images,output_folder=None, outputformat="stdout", add_meta=True):
    """
    Get taxonomy tags from an iNaturalist observation or taxon, and write them to local image
    metadata. See :py:func:`~tesseractXplore.cli.tag` for details.
    """
    # TODO: Simplify this a bit
    all_metadata = []
    for image_path in images:
        params = ["-l", "deu", "--psm", "4", "--oem", "3"]
        output = Path(image_path).base.joinpath(
            Path(image_path).name) if outputformat != "stdout" else outputformat
        p1 = Popen(["tesseract", *params, image_path, output, outputformat], stdout=PIPE)
        stdout, stderr = p1.communicate()
        if outputformat == "stdout":
            toast(str(stdout.decode("utf-8")))
        else:
            toast(output)
        #import hashlib
        #keywords = get_keywords(common=stdout)
        #all_metadata.append(tag_image(image_path, keywords))
    return None, None


def tag_image(image_path, keywords):
    metadata = MetaMetadata(image_path)
    metadata.update_keywords(keywords)
    return metadata
