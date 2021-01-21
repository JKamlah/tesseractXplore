import os
import glob
import os
from pathlib import Path

from tesseractXplore.app import get_app


# TODO: This screen is pretty ugly.
class DiffStdoutController:
    """ Controller class to manage image metadata screen """

    def __init__(self, screen, **kwargs):
        self.screen = screen

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return

    def select_fulltext(self, fulltext):
        self.image.source = fulltext.selected_image.original_source
        for collection in self.files:
            collection.clear()
        fpath = Path(fulltext.selected_image.original_source)
        fdir = fpath.parent
        fname = fpath.name.rsplit(".", 1)[0]

    def on_touch_down(self, touch):
        # Override Scatter's `on_touch_down` behavior for mouse scrolli
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.scale < 10:
                    self.scale = self.scale * 1.1
            elif touch.button == 'scrollup':
                if self.scale > 1:
                    self.scale = self.scale * 0.8
        # If some other kind of "touch": Fall back on Scatter's behavior
        # else:
        # super(ResizableDraggablePicture, self).on_touch_down(touch

    def set_textfile(self, instance):
        self.screen.textfiles.set_item(instance.text[-75:])
        self.current_file.text[0] = instance.text
        self.text.text = "".join(open(instance.text, encoding='utf-8').readlines())
        self.text.cursor = (0, 0)
        self.textfiles_menu.dismiss()


def read_file(fname, collections):
    res = find_file(fname, collections)
    if res:
        return "".join(open(res, encoding='utf-8').readlines())
    else:
        return ""


def find_file(fname, collections):
    app = get_app()
    # if outputfolder
    if app.tesseract_controller.selected_output_folder and Path(
            app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
        collections.append(os.path.join(app.tesseract_controller.selected_output_foldier, fname.name))
    # else check cwd folder
    elif fname.is_file():
        collections.append(str(fname.absolute()))
    # else check cwd subfolder (depth 1)
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        collections.extend(subfoldermatch)
    # check cwd subfolder (depth 2)
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        collections.extend(subfoldermatch)
    if collections:
        return collections[0]
    return None
