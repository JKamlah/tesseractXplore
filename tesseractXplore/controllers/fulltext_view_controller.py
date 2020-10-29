import json
import os
import glob
from pathlib import Path

from kivy.properties import StringProperty
from tesseractXplore.app import alert, get_app
from kivy.core.window import Window

# TODO: This screen is pretty ugly. Ideally this would be a collection of DataTables.
class FulltextViewController:
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.image = screen.image
        self.image_text = screen.image_text
        self.text = screen.text
        self.alto = screen.alto
        self.hocr = screen.hocr
        self.tsv = screen.tsv
        self.tab_list = [screen.image,screen.text,screen.alto,screen.hocr,screen.tsv]
        #Window.bind(on_dropfile=self.drop_trigger)
        #self.bind(current_tab=self.disable_tabs)

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return

    def disable_tabs(self, widget, value):
        """Manage the event when the current_tab changes.

        It enables the tab's editor to which the user changed and
        disables all others.
        """

        for tab in self.tab_list:
            tab.content.editor.disabled = True

        widget.current_tab.content.editor.disabled = False

    def select_fulltext(self, fulltext):
        self.image.source = fulltext.selected_image.original_source
        fpath = Path(fulltext.selected_image.original_source)
        fdir = fpath.parent
        fname = fpath.name.rsplit(".",1)[0]
        self.image_text.source = fulltext.selected_image.original_source
        self.text.text = read_file(fdir.joinpath(fname+'.txt'))
        self.alto.text = read_file(fdir.joinpath(fname+'.xml'))
        self.hocr.text = read_file(fdir.joinpath(fname+'.hocr'))
        self.tsv.text = read_file(fdir.joinpath(fname+'.tsv'))

    def on_touch_down(self, touch):
        # Override Scatter's `on_touch_down` behavior for mouse scrolli
        print("HEY")
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.scale < 10:
                    self.scale = self.scale * 1.1
            elif touch.button == 'scrollup':
                if self.scale > 1:
                    self.scale = self.scale * 0.8
        # If some other kind of "touch": Fall back on Scatter's behavior
        #else:
            #äsuper(ResizableDraggablePicture, self).on_touch_down(touch)

    def on_bring_to_front(self, touch):
        print("HEY")

    def on_transform_with_touch(self, touch):
        print("HO")

    def switch_tab(self):
        '''Switching the tab by name.'''
        try:
            self.image.scale = self.image.scale * 1.1
        except StopIteration:
            pass


def read_file(fname):
    res = find_file(fname)
    if res:
        return "\n".join(open(res).readlines())
    else:
        return ""

def find_file(fname):
    app = get_app()
    #if outputfolder
    if app.tesseract_controller.selected_output_folder and Path(app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
        return os.path.join(app.tesseract_controller.selected_output_foldier,fname)
    # else check cwd folder
    elif fname.is_file():
        return fname
    # else check cwd subfolder
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        return subfoldermatch[0]
    return None