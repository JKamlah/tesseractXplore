import glob
import os
import re
from collections import namedtuple
from functools import partial
from pathlib import Path

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu

from tesseractXplore.app import get_app
from tesseractXplore.hocr import get_text_and_bbox, save_hocr
from tesseractXplore.widgets.labels import HOCRLabel


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
        self.hocr_data = None
        self.tsv = screen.tsv
        FileCollection = namedtuple('FileCollection', 'text alto hocr tsv')
        self.files = FileCollection([], [], [], [])
        self.current_file = FileCollection([''], [''], [''], [''])
        self.tab_list = [screen.image, screen.text, screen.alto, screen.hocr, screen.tsv]
        self.screen.save_text_button.bind(on_release=self.save_text)
        self.screen.delete_empty_lines_button.bind(on_release=self.delete_empty_lines)
        self.pil_image = None
        # Window.bind(on_dropfile=self.drop_trigger)
        # self.bind(current_tab=self.disable_tabs)

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
        menu = MDDropdownMenu(caller=caller,
                              items=item,
                              position="center",
                              width_mult=20)
        menu.bind(on_release=callback)
        return menu

    def select_fulltext(self, fulltext):
        self.image.source = fulltext.selected_image.original_source
        for collection in self.files:
            collection.clear()
        fpath = Path(fulltext.selected_image.original_source)
        fdir = fpath.parent
        fname = fpath.name.rsplit(".", 1)[0]
        self.text.text = read_file(fdir.joinpath(fname + '.txt'), self.files.text)
        self.text.font_name = get_app().settings_controller.get_font()
        self.screen.fontsize.text = get_app().settings_controller.screen.fontsize.text
        self.text.font_size = int(get_app().settings_controller.screen.fontsize.text)
        self.text.cursor = (0, 0)
        if self.files.text:
            self.screen.textfiles.text = self.files.text[0][-75:]
            self.current_file.text[0] = self.files.text[0]
            self.textfiles_menu = self.create_dropdown(self.screen.textfiles,
                                                       [{'text': textfile} for textfile in self.files.text],
                                                       partial(self.set_file, "text"))
        self.screen.fontsize.text = str(self.text.font_size)
        self.alto.text = read_file(fdir.joinpath(fname + '.xml'), self.files.alto)
        self.alto.font_name = get_app().settings_controller.get_font()
        self.alto.font_size = int(get_app().settings_controller.screen.fontsize.text)
        self.alto.cursor = (0, 0)
        read_file(fdir.joinpath(fname + '.hocr'), self.files.hocr)
        if self.files.hocr:
            self.screen.hocrfiles.text = self.files.hocr[0][-75:]
            self.current_file.hocr[0] = self.files.hocr[0]
            self.hocrfiles_menu = self.create_dropdown(self.screen.hocrfiles,
                                                       [{'text': hocrfile} for hocrfile in self.files.hocr],
                                                       partial(self.set_file, "hocr"))
            self.interactive_hocr(self.current_file.hocr[0])
        self.tsv.text = read_file(fdir.joinpath(fname + '.tsv'), self.files.tsv)
        self.tsv.font_name = get_app().settings_controller.get_font()
        self.tsv.font_size = int(get_app().settings_controller.screen.fontsize.text)
        self.tsv.cursor = (0, 0)

    def interactive_hocr(self, hocrfile):
        layout = MDList()
        self.screen.hocr_view.clear_widgets()
        self.hocr_data = get_text_and_bbox(hocrfile)
        for par_id, par_data in self.hocr_data.items():
            for line_id, line_data in par_data.items():
                # for word_id, word_data in word_data.items():
                widget = HOCRLabel(text=line_data.pop('text'),
                                   bbox=line_data.pop('bbox'),
                                   font_style=get_app().settings_controller.get_fontstyle(),
                                   par_id=par_id,
                                   line_id=line_id,
                                   on_release=partial(self.hocr_dialog),
                                   theme_text_color="Primary")
                widget.size_hint_y = None
                widget.height = 40
                layout.add_widget(widget)
        self.screen.hocr_view.add_widget(layout)
        self.screen.save_hocr_button.bind(
            on_release=partial(save_hocr, self.current_file.hocr[0], self.screen.hocr_view.children[0].children))

    def _update_image(self, img, snippet):
        from io import BytesIO
        from kivy.uix.image import CoreImage
        data = BytesIO()
        snippet.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        img.texture = None
        img.texture = im.texture

    def update_bbox(self, line, instance, *args):
        bbox = self.get_bbox(instance)
        snippet = self.pil_image.crop(bbox)
        self._update_image(instance.parent.parent.parent.parent.children[0].children[2].children[0].children[1],
                           snippet)

    def get_bbox(self, instance):
        bboxinstance = instance.parent.parent.parent.parent.children[0].children[2].children[0].children[2].children[0]
        bbox = [int(bboxinstance.children[3].text),
                int(bboxinstance.children[2].text),
                int(bboxinstance.children[1].text),
                int(bboxinstance.children[0].text)]
        return bbox

    def update_text(self, line, instance, *args):
        line.text = instance.parent.parent.parent.parent.children[0].children[2].children[0].children[0].text
        line.bbox = self.get_bbox(instance)
        line.edited = True
        self.close_dialog(instance, *args)

    def hocr_dialog(self, instance, *args):
        from kivy.uix.image import Image
        from PIL.Image import open
        # texture.get_region seems to be buggy
        if not self.pil_image:
            self.pil_image = open(self.image.source)
        snippet = self.pil_image.crop(instance.bbox)
        image = Image()
        self._update_image(image, snippet)
        from kivymd.uix.boxlayout import BoxLayout
        from kivymd.uix.textfield import TextInput, MDTextField
        layout = BoxLayout(orientation="vertical", size=(500, 200), size_hint=(None, None))
        bboxlayout = BoxLayout(orientation="vertical")
        bboxvaluelayout = BoxLayout(orientation="horizontal")
        bboxlayout.add_widget(OneLineListItem(text="BBOX"))
        for bbox in instance.bbox:
            bboxvaluelayout.add_widget(MDTextField(text=str(bbox)))
        bboxlayout.add_widget(bboxvaluelayout)
        layout.add_widget(bboxlayout)
        layout.add_widget(image)
        layout.add_widget(TextInput(text=instance.text,font_name=get_app().settings_controller.get_font()))
        dialog = MDDialog(title="Snippets",
                          type='custom',
                          auto_dismiss=False,
                          text=instance.text,
                          content_cls=layout,
                          size=(500, 800),
                          size_hint=(None, None),
                          buttons=[
                              MDFlatButton(
                                  text="UPDATE BBOX", on_release=partial(self.update_bbox, instance)
                              ),
                              MDFlatButton(
                                  text="SAVE", on_release=partial(self.update_text, instance)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=partial(self.close_dialog)
                              ),
                          ],
                          )
        dialog.open()

    def close_dialog(self, instance, *args):
        instance.parent.parent.parent.parent.dismiss()

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

    def set_file(self, filetype, instance_button, instance):
        if filetype == 'text':
            self.screen.textfiles.set_item(instance.text[-75:])
            self.current_file.text[0] = instance.text
            self.text.text = "".join(open(instance.text, encoding='utf-8').readlines())
            self.text.cursor = (0, 0)
            self.textfiles_menu.dismiss()
        if filetype == 'hocr':
            self.screen.hocrfiles.set_item(instance.text[-75:])
            self.current_file.hocr[0] = instance.text
            self.interactive_hocr(instance.text)

    def switch_tab(self):
        '''Switching the tab by name.'''
        try:
            self.image.scale = self.image.scale * 1.1
        except StopIteration:
            pass


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
    if fname.is_file():
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
