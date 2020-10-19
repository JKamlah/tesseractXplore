import json
import os
import glob
from pathlib import Path

from kivy.properties import StringProperty
from tesseractXplore.app import alert, get_app



# TODO: This screen is pretty ugly. Ideally this would be a collection of DataTables.
class FulltextViewController:
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.image = screen.image
        self.text = screen.text
        self.alto = screen.alto
        self.hocr = screen.hocr
        self.tsv = screen.tsv

    def select_fulltext(self, fulltext):
        self.image.source = fulltext.selected_image.original_source
        fname = Path(fulltext.selected_image.original_source)
        self.text.text = self.read_file(fname+'.txt')
        self.alto.text = self.read_file(fname+'.xml')
        self.hocr.text = self.read_file(fname+'.hocr')
        self.tsv.text = self.read_file(fname+'.tsv')

    def read_file(self, fname):
        app = get_app()
        #if outputfolder
        if app.tesseract_controller.selected_output_folder and Path(app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
            return "\n".join(open(os.path.join(app.tesseract_controller.selected_output_foldier,fname)).readlines())
        # else check cwd folder
        if fname.is_file():
            return "\n".join(open(fname).readlines())
        # else check cwd subfolder
        elif glob.glob(fname.parent.joinpath('**').joinpath(fname.name)):
            return "\n".join(open(glob.glob(os.path.join(os.getcwd(), '**/', fname))[0]).readlines())
        return ""
