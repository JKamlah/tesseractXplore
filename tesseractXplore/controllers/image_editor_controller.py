import os
import glob
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
from io import BytesIO
from kivy.uix.image import CoreImage


from tesseractXplore.app import alert, get_app
from tesseractXplore.app.screens import HOME_SCREEN

# TODO: This screen is pretty ugly.
class ImageEditorController:
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.image = screen.image
        self.org_img = None
        self.new_img = None
        #Window.bind(on_dropfile=self.drop_trigger)
        self.screen.adjust_button.bind(on_release=self.adjust)
        self.screen.save_button.bind(on_release=self.save)
        self.screen.reset_button.bind(on_release=self.reset)

    def reset(self, instance, *args):
        data = BytesIO()
        self.orig_img.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.image.texture = None
        self.image.texture = im.texture
        self.reset_values()
        self.new_img = self.orig_img

    def reset_values(self):
        self.screen.brightness.value = 100
        self.screen.contrast.value = 100
        self.screen.sharpness.value = 0
        self.screen.autocontrast_chk.active = False
        self.screen.equalize_chk.active = False
        self.screen.stack_chk.active = False

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return

    def adjust(self, instance):
        img = self.new_img if self.screen.stack_chk.active else self.orig_img
        img = self._adjust(img)
        self.new_img = img
        data = BytesIO()
        img.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.image.texture = None
        self.image.texture = im.texture

    def _adjust(self, img):
        img = ImageEnhance.Brightness(img).enhance(self.screen.brightness.value/100)
        img = ImageEnhance.Contrast(img).enhance(self.screen.contrast.value/100)
        img = ImageEnhance.Sharpness(img).enhance(self.screen.sharpness.value)
        img = img.rotate(float(self.screen.rotate.text))
        img = ImageOps.crop(img, border=int(self.screen.crop.text))
        if self.screen.autocontrast_chk.active:
            img = ImageOps.autocontrast(image=img)
        if self.screen.equalize_chk.active:
            img = ImageOps.equalize(image=img)
        return img

    def save(self, instance):
        app = get_app()
        if self.screen.apply_to_selected_chk.active:
            if self.screen.outputfolder.text == '':
                self.screen.outputfolder.text = 'EditImages'
            for image in app.image_selection_controller.file_list:
                self.select_image(image)
                self.new_img = self._adjust(self.orig_img)
                self.new_img.save(str(self._outputpath().joinpath(Path(self.image.source).name)))
        else:
            self.new_img.save(str(self._outputpath().joinpath(self.screen.imagename.text).absolute()))
        app.image_selection_controller.file_chooser._update_files()
        app.switch_screen(HOME_SCREEN)

    def _outputpath(self):
        if self.screen.outputfolder.text != '':
            outputpath = Path(self.image.source).parent.joinpath(self.screen.outputfolder.text + '/')
            if not outputpath.exists():
                outputpath.mkdir(parents=True)
        else:
            outputpath = Path(self.image.source).parent
        return outputpath


    def _save_image(self, image, outputpath):
        self.new_img.save(str(Path(self.image.source).parent.joinpath(self.screen.imagename.text).absolute()))

    def select_image(self, image):
        if isinstance(image, str):
            self.image.source = image
        else:
            self.image.source = image.selected_image.original_source
        self.screen.imagename.text = Path(self.image.source).name
        self.orig_img = Image.open(self.image.source).convert("RGB")
        self.new_img = self.orig_img
        #fpath = Path(image.selected_image.original_source)
        #fdir = fpath.parent
        #fname = fpath.name.rsplit(".",1)[0]


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