import json
import os
import glob
import re
from pathlib import Path
from collections import namedtuple

from kivy.properties import StringProperty, ObjectProperty
from tesseractXplore.app import alert, get_app
from kivymd.uix.menu import MDDropdownMenu
from functools import partial


# TODO: This screen is pretty ugly.
# TODO: Implement another text provider to display combined grapheme, see:
# https://stackoverflow.com/questions/63646050/kivy-isnt-showing-bengali-joining-character-properly
class FulltextViewController:
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.image = screen.image
        self.text = screen.text
        self.text.font_size = 21.0
        self.alto = screen.alto
        self.hocr = screen.hocr
        self.tsv = screen.tsv
        FileCollection = namedtuple('FileCollection','text alto hocr tsv')
        self.files = FileCollection([],[],[],[])
        self.current_file = FileCollection([''], [''], [''], [''])
        self.tab_list = [screen.image,screen.text,screen.alto,screen.hocr,screen.tsv]
        self.screen.save_button.bind(on_release=self.save_text)
        self.screen.delete_empty_lines_button.bind(on_release=self.delete_empty_lines)
        #Window.bind(on_dropfile=self.drop_trigger)
        #self.bind(current_tab=self.disable_tabs)


    def delete_empty_lines(self, instance, *args):
        self.text.text = "\n".join(filter(lambda x: not re.match(r'^\s*$', x), self.text.text.split("\n")))
        self.text.cursor = (0, 0)

    def save_text(self, instance, *args):
        self.text.text = self.text.text
        with open(self.current_file.text[0], "w") as fout:
            fout.write(self.text.text)

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

    def create_dropdown(self, caller, item, callback):
        return MDDropdownMenu(caller=caller,
                       items=item,
                       position="center",
                       width_mult=20,
                       callback=callback)

    def select_fulltext(self, fulltext):
        self.image.source = fulltext.selected_image.original_source
        for collection in self.files:
            collection.clear()
        fpath = Path(fulltext.selected_image.original_source)
        fdir = fpath.parent
        fname = fpath.name.rsplit(".",1)[0]
        self.text.text = read_file(fdir.joinpath(fname+'.txt'), self.files.text)
        self.text.cursor = (0, 0)
        if self.files.text:
            self.screen.textfiles.text = self.files.text[0][-75:]
            self.current_file.text[0] = self.files.text[0]
            self.textfiles_menu = self.create_dropdown(self.screen.textfiles, [{'text': textfile} for textfile in self.files.text], self.set_textfile)
        self.screen.fontsize.text = str(self.text.font_size)
        self.alto.text = read_file(fdir.joinpath(fname+'.xml'), self.files.alto)
        self.alto.cursor = (0, 0)
        self.hocr.text = read_file(fdir.joinpath(fname+'.hocr'), self.files.hocr)
        self.hocr.cursor = (0, 0)
        self.tsv.text = read_file(fdir.joinpath(fname+'.tsv'), self.files.tsv)
        self.tsv.cursor = (0, 0)

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
        #else:
            #super(ResizableDraggablePicture, self).on_touch_down(touch

    def set_textfile(self, instance):
        self.screen.textfiles.set_item(instance.text[-75:])
        self.current_file.text[0] = instance.text
        self.text.text = "".join(open(instance.text,encoding='utf-8').readlines())
        self.text.cursor = (0, 0)
        self.textfiles_menu.dismiss()

    def switch_tab(self):
        '''Switching the tab by name.'''
        try:
            self.image.scale = self.image.scale * 1.1
        except StopIteration:
            pass


def read_file(fname, collections):
    res = find_file(fname, collections)
    if res:
        return "".join(open(res,encoding='utf-8').readlines())
    else:
        return ""

def find_file(fname, collections):
    app = get_app()
    #if outputfolder
    if app.tesseract_controller.selected_output_folder and Path(app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
        collections.append(os.path.join(app.tesseract_controller.selected_output_foldier,fname.name))
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