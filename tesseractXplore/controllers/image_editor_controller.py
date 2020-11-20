import os
import glob
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
from io import BytesIO
from kivy.uix.image import CoreImage

from tesseractXplore.app import alert, get_app

# TODO: This screen is pretty ugly.
class ImageEditorController:
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.image = screen.image
        self.org_img = None
        self.adjust_img= None
        #Window.bind(on_dropfile=self.drop_trigger)
        self.screen.preview_button.bind(on_release=self.preview)
        self.screen.save_button.bind(on_release=self.save)

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return

    def preview(self, instance):
        img = ImageEnhance.Brightness(self.img).enhance(self.screen.brightness.value/100)
        img = ImageEnhance.Contrast(img).enhance(self.screen.contrast.value/100)
        img = ImageEnhance.Sharpness(img).enhance(self.screen.sharpness.value)
        if self.screen.autocontrast_chk.active:
            img = ImageOps.autocontrast(image=img)
        if self.screen.equalize_chk.active:
            img = ImageOps.equalize(image=img)
        data = BytesIO()
        img.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.image.texture = None
        self.image.texture = im.texture

    def save(self, instance):
        self.img.save(str(Path(self.image.source).parent.joinpath(self.screen.imagename.text).absolute()))

    def select_image(self, image):
        self.image.source = image.selected_image.original_source
        self.screen.imagename.text = Path(self.image.source).name
        self.img = Image.open(image.selected_image.original_source)
        fpath = Path(image.selected_image.original_source)
        fdir = fpath.parent
        fname = fpath.name.rsplit(".",1)[0]


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
            #super(ResizableDraggablePicture, self).on_touch_down(touch)

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