import glob
import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
from kivy.uix.image import CoreImage

from tesseractXplore.app import get_app
from tesseractXplore.app.screens import HOME_SCREEN


# TODO: This screen is pretty ugly.
class ImageEditorController:
    """ Controller class to manage image metadata screen """

    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.image = screen.image
        self.orig_img = None
        self.orig_thumbnail = None
        # Window.bind(on_dropfile=self.drop_trigger)
        # Main settings
        self.screen.adjust_button.bind(on_release=self.adjust)
        self.screen.save_button.bind(on_release=self.save)
        self.screen.reset_button.bind(on_release=self.reset)

    def reset(self, *args):
        data = BytesIO()
        self.orig_thumbnail.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.image.texture = None
        self.image.texture = im.texture
        self.reset_values()

    def reset_values(self):
        self.screen.brightness.value = 100
        self.screen.contrast.value = 100
        self.screen.sharpness.value = 0
        self.screen.rotate.text = '0'
        self.screen.autocontrast_chk.active = False
        self.screen.equalize_chk.active = False
        self.screen.apply_to_selected_chk.active = False

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return

    def transpose(self, img):
        """
        One of PIL.Image.FLIP_LEFT_RIGHT,
        PIL.Image.FLIP_TOP_BOTTOM,
        PIL.Image.ROTATE_90,
        PIL.Image.ROTATE_180,
        PIL.Image.ROTATE_270,
        PIL.Image.TRANSPOSE or PIL.Image.TRANSVERSE.
        """
        if self.screen['rotate_left_chk'].state == 'down':
            img = img.transpose(method=Image.ROTATE_90)
        elif self.screen['rotate_180_chk'].state == 'down':
            img = img.transpose(method=Image.ROTATE_180)
        elif self.screen['rotate_right_chk'].state == 'down':
            img = img.transpose(method=Image.ROTATE_270)
        if self.screen['flip_left2right_chk'].state == 'down':
            img = img.transpose(method=Image.FLIP_LEFT_RIGHT)
        elif self.screen['flip_top2bottom_chk'].state == 'down':
            img = img.transpose(method=Image.FLIP_TOP_BOTTOM)
        return img

    def adjust(self, instance):
        img = self.orig_img if self.screen.fullsize_img_chk.active else self.orig_thumbnail
        img = self._adjust(img)
        self._update_preview(img)

    def _update_preview(self, img):
        data = BytesIO()
        img.save(data, format='png')
        data.seek(0)  # yes you actually need this
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.image.texture = None
        self.image.texture = im.texture

    def _adjust(self, img):
        img = ImageEnhance.Brightness(img).enhance(self.screen.brightness.value / 100)
        img = ImageEnhance.Contrast(img).enhance(self.screen.contrast.value / 100)
        img = ImageEnhance.Sharpness(img).enhance(self.screen.sharpness.value)
        img = self.transpose(img)
        img = img.rotate(float(self.screen.rotate.text), expand=True)
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
            img = self._adjust(self.orig_img)
            img.save(str(self._outputpath().joinpath(self.screen.imagename.text).absolute()))
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
        self.screen.imagename.set_text(self.screen.imagename, Path(self.image.source).name)
        self.orig_img = Image.open(self.image.source).convert("RGB")
        self.orig_thumbnail = self.orig_img.copy()
        self.thumbnail_size = int(get_app().settings_controller.controls['ie_thumbnail_size'].text)
        self.orig_thumbnail.thumbnail([self.thumbnail_size, self.thumbnail_size])

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
        # super(ResizableDraggablePicture, self).on_touch_down(touch)

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
    # if outputfolder
    if app.tesseract_controller.selected_output_folder and Path(
            app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
        return os.path.join(app.tesseract_controller.selected_output_foldier, fname)
    # else check cwd folder
    elif fname.is_file():
        return fname
    # else check cwd subfolder
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        return subfoldermatch[0]
    return None
