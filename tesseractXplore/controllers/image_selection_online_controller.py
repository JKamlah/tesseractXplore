import asyncio
import os
import shutil
import webbrowser
from logging import getLogger
from pathlib import Path
from functools import partial

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.toast import toast
from kivymd.uix.list import MDList, OneLineListItem


from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller, ImageBatchLoaderOnline
from tesseractXplore.controllers.fulltext_view_controller import find_file
from tesseractXplore.diff_stdout import diff_dialog
from tesseractXplore.image_glob import get_images_from_paths
from tesseractXplore.pdf import open_pdf

logger = getLogger().getChild(__name__)


class ImageSelectionOnlineController(Controller):
    """ Controller class to manage image selector screen """

    def __init__(self, screen):
        super().__init__(screen)
        self.context_menu = screen.context_menu
        self.screen = screen
        self.image_previews = screen.image_previews
        self.file_chooser = screen.file_chooser
        self.update_filechooser_filter(filters=get_app().settings_controller.get_formatfilters())
        self.user_filter = ""
        self.file_list = []
        self.theme_cls = get_app().theme_cls

        # Context menu item events
        # For recgonize see tesseract_controller
        self.context_menu.ids.edit_fulltext_ctx.bind(on_release=self.edit_fulltext)
        self.context_menu.ids.edit_image_ctx.bind(on_release=self.edit_image)
        self.context_menu.ids.remove_ctx.bind(on_release=lambda x: self.remove_image(x.selected_image))
        self.context_menu.ids.open_pdf_ctx.bind(on_release=self.open_pdf_instance)
        self.context_menu.ids.diff_stdout_ctx.bind(on_release=diff_dialog)

        # Other widget events
        self.screen.clear_button.bind(on_release=self.clear)
        self.screen.load_button.bind(on_release=self.add_file_chooser_images)
        self.screen.open_folder_button.bind(on_release=self.open_folder)
        self.screen.delete_button.bind(on_release=self.delete_file_chooser_selection_dialog)
        self.screen.fileformat_filter_button.bind(on_release=self.fileformat_filter_dialog)
        self.screen.home_button.bind(on_release=self.home_folder)
        self.screen.sort_button.bind(on_release=self.sort_previews)
        self.screen.zoomin_button.bind(on_release=self.zoomin)
        self.screen.zoomout_button.bind(on_release=self.zoomout)

        # Instead see tesseract_controller
        # self.inputs.recognize_button.bind(on_release=self.run)
        self.file_chooser.bind(on_submit=self.add_file_chooser_images)
        self.screen.image_scrollview.bind(on_touch_down=self.on_touch_down)

        # TODO: Not working atm only on main window atm (see app.py)
        # self.screen.image_scrollview.bind(on_keyboard=self.on_keyboard)

    def open_folder(self, *args):
        if self.file_chooser.selection:
            folder = Path(self.file_chooser.selection[0])
            if folder.is_dir():
                webbrowser.open(str(folder.resolve()))
            else:
                webbrowser.open(str(folder.parent.resolve()))

    def home_folder(self, *args):
        self.file_chooser.path = str(Path.home())

    def update_filechooser_filter_by_dialog(self, instance, checkbox_filter_list,):
        # TODO: Rework this
        if checkbox_filter_list.children[0].text != "":
            self.user_filter = checkbox_filter_list.children[0].text
            filters = ['*'+self.user_filter+'*']
        else:
            filters = ['*'+filter.text for filter in checkbox_filter_list.children[1:] if filter.ids._left_container.children[0].active]
        instance.parent.parent.parent.parent.dismiss()
        self.update_filechooser_filter(filters)

    def update_filechooser_filter(self, filters):
        # TODO: Rework this
        self.file_chooser.filters = filters
        self.file_chooser._update_files()

    def zoomin(self, instance, *args):
        currentvalue = self.screen.image_previews.row_default_height
        zoom = currentvalue + 100 if currentvalue < 400 else currentvalue
        self.zoom(self.screen.image_previews, zoom)

    def zoomout(self, instance, *args):
        currentvalue = self.screen.image_previews.row_default_height
        zoom = currentvalue - 100 if currentvalue > 100 else currentvalue
        self.zoom(self.screen.image_previews, zoom)

    def zoom(self, instance, zoom):
        instance.cols = max(int(self.screen.image_previews.width / zoom), 1)
        instance.row_default_height = zoom
        instance.col_default_width = zoom

    def on_touch_down(self, instance, touch):
        if touch.osx < 0.7 and len(self.image_previews.children) > 0:
            if touch.is_mouse_scrolling:
                if touch.button == 'scrolldown':
                    self.zoomin(instance, None)
                elif touch.button == 'scrollup':
                    self.zoomout(instance, None)

    def sort_previews(self, instance, *args):
        if instance.text == 'Sort Up':
            self.file_list = list(sorted(self.file_list))
            instance.text = 'Sort Down'
        elif instance.text == 'Sort Down':
            self.file_list = list(reversed(self.file_list))
            instance.text = 'Sort Up'
        children = self.image_previews.children[:]
        self.image_previews.clear_widgets()
        for fname in self.file_list:
            for child in children:
                if child.original_source == fname:
                    self.image_previews.add_widget(child)

    def post_init(self):
        # Load and save start dir from file chooser with the rest of the app settings
        get_app().add_control_widget(self.file_chooser, 'start_dir_online', 'photos')

    def update_filechooser_multiselection(self, *args):
        self.file_chooser.selection = list(set([sel for sel in self.file_chooser.selection if sel != '../']))
        for sel in self.file_chooser.selection:
            if Path(sel).is_file():
                break
        else:
            return
        self.file_chooser.selection = [sel for sel in self.file_chooser.selection if Path(sel).is_file()]

    def delete_file_chooser_selection_dialog(self, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        if self.file_chooser.multiselection == True:
            self.update_filechooser_multiselection()
        sellist = MDList()
        for sel in self.file_chooser.selection:
            sellist.add_widget(OneLineListItem(text=sel))
        dialog = MDDialog(title="The following selection will be deleted:",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=sellist,
                          buttons=[
                              MDFlatButton(
                                  text="DELETE", on_release=self.delete_file_chooser_selection
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        if get_app()._platform not in ['win32', 'win64']:
            # TODO: Focus function seems buggy in win
            dialog.content_cls.focused = True
        dialog.open()

    def delete_file_chooser_selection(self, instance, *args):
        for sel in self.file_chooser.selection:
            if os.path.isfile(sel):
                os.remove(sel)
            else:
                try:
                    shutil.rmtree(sel)
                except FileNotFoundError:
                    toast(f"No such file or directory: {sel}")
                    logger.error(f"No such file or directory: {sel}")
                    instance.parent.parent.parent.parent.dismiss()
                    return
        self.file_chooser._update_files()
        for file in self.file_list:
            if not os.path.isfile(file):
                self.file_list.remove(file)
                for preview in self.image_previews.children:
                    if file == preview.original_source:
                        self.image_previews.remove_widget(preview)
        instance.parent.parent.parent.parent.dismiss()

    def fileformat_filter_dialog(self, *args):
        from kivymd.uix.list import OneLineIconListItem, MDList
        from tesseractXplore.widgets import LeftCheckbox

        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()

        def item(imageformat):
            item = OneLineIconListItem(
                text=imageformat,
                size_hint=(None, None),
                size=(250,1)
            )
            item.add_widget(LeftCheckbox(active='*'+imageformat in self.file_chooser.filters))
            return item

        layout = MDList()
        for imageformat in sorted(set(['jpg', 'jpeg', 'jp2', 'png', 'ppm', 'gif', 'tif', 'tiff', 'pdf']+[filteritem[1:] for filteritem in get_app().settings_controller.get_formatfilters()])):
            layout.add_widget(item(imageformat))
        layout.add_widget(MDTextField(text=self.user_filter,
                                      hint_text="User specific filter (e.g. {filename}*{extension}",))
        dialog = MDDialog(title="Filter for imageformats",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="FILTER", on_release=partial(self.update_filechooser_filter_by_dialog,
                                                                    checkbox_filter_list=layout)
                              ),
                              MDFlatButton(
                                  text="RESET", on_release=partial(self.update_filechooser_filter)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        if get_app()._platform not in ['win32', 'win64']:
            # TODO: Focus function seems buggy in win
            dialog.content_cls.focused = True
        dialog.open()

    def add_file_chooser_images(self, *args):
        """ Add one or more files and/or dirs selected via a FileChooser """
        if not self.file_chooser.selection:
            self.add_images([fname for fname in self.file_chooser.files[1:] if fname[-4:] != ".pdf"])
        self.add_images(self.file_chooser.selection)

    def add_image(self, path):
        """ Add an image to the current selection """
        self.add_images([path])

    def add_images(self, paths):
        """ Add one or more files and/or dirs, with deduplication """
        # TODO: Loading in one step seems buggy - asyncio.run(self.load_images(paths))
        if self.file_chooser.multiselection == True:
            self.update_filechooser_multiselection()
        for path in paths:
            asyncio.run(self.load_images(path))

    async def load_images(self, paths):
        # Determine images to load, ignoring duplicates
        images = get_images_from_paths(paths, recursive=self.input_dict['recursive'])
        new_images = list(set(images) - set(self.file_list))
        logger.info(f'Main: Loading {len(new_images)} ({len(images) - len(new_images)} already loaded)')
        if not new_images:
            return
        self.file_list.extend(new_images)

        # Start batch loader + progress bar
        loader = ImageBatchLoaderOnline()
        self.start_progress(len(new_images), loader)
        # for new_image in new_images:
        loader.add_batch(new_images, parent=self.image_previews)
        loader.start_thread()

    def open_pdf_instance(self, instance, *args):
        """ Open a pdf via webbrowser or another external software """
        from pathlib import Path
        fname = Path(instance.selected_image.original_source)
        pdf = []
        find_file(fname.parent.joinpath(fname.name.rsplit(".", 1)[0] + ".pdf"), pdf)
        if not pdf:
            alert(f"Couldn't find any matching pdf to {fname.name}")
            return
        open_pdf(str(Path(pdf[0]).absolute()))

    def open_native_file_chooser(self, dirs=False):
        """ A bit of a hack; uses a hidden tkinter window to open a native file chooser dialog """
        from tkinter import Tk
        from tkinter.filedialog import askopenfilenames, askdirectory
        Tk().withdraw()
        # Tkinter does not have a single dialog that combines directory and file selection >:[
        if dirs:
            paths = askdirectory(title='Choose an image directory')
        else:
            paths = askopenfilenames(title='Choose images')
        self.add_images(paths)

    def select_model_from_photo(self, model_id):
        return
        # self.screen.model_id_input.text = str(model_id)

    def select_gt_from_photo(self, gt_id):
        return
        # self.screen.gt_id_input.text = str(gt_id)

    def remove_image(self, image):
        """ Remove an image from file list and image previews """
        logger.info(f'Main: Removing image {image.original_source}')
        self.file_list.remove(image.original_source)
        image.parent.remove_widget(image)

    def clear(self, *args):
        """ Clear all image selections (selected files, previews, and inputs) """
        logger.info('Main: Clearing image selections')
        self.file_list = []
        self.file_chooser.selection = []
        self.image_previews.clear_widgets()

    @property
    def input_dict(self):
        return {
            "gt_id": int(0),
            "model_id": int(0),
            "recursive": self.screen.recursive_chk.active,
        }

    def get_state(self, *args):
        logger.info(
            'Main:',
            f'IDs: {self.ids}\n'
            f'Files:\n{self.file_list}\n'
            f'Input: {self.input_dict}\n'
        )

    def on_image_click(self, instance, touch):
        """ Event handler for clicking an image """
        if not instance.collide_point(*touch.pos):
            return
        # Right-click: Open context menu for the image
        elif touch.button == 'right':
            self.context_menu.show(*get_app().root_window.mouse_pos)
            self.context_menu.ref = instance
            # Enable 'view model/gt' menu items, if applicable
            # self.context_menu.ids.view_model_ctx.disabled = not instance.metadata.model_id
            # self.context_menu.ids.view_gt_ctx.disabled = not instance.metadata.gt_id
            # self.context_menu.ids.copy_flickr_tags_ctx.disabled = not instance.metadata.keyword_meta.flickr_tags
        # Middle-click: remove image
        elif touch.button == 'middle':
            self.remove_image(instance)
        # Left-click: # TODO: larger image view
        else:
            pass

    # TODO: reuse Model object previously found by load_image; needs a bit of refactoring
    @staticmethod
    def view_model(instance):
        get_app().switch_screen('model')
        get_app().select_model(id=instance.metadata.model_id)

    @staticmethod
    def view_metadata(instance):
        get_app().switch_screen('metadata')
        get_app().select_metadata(instance.metadata)

    @staticmethod
    def edit_fulltext(instance):
        get_app().switch_screen('fulltext')
        get_app().select_fulltext(instance)

    @staticmethod
    def edit_image(instance):
        get_app().switch_screen('image')
        get_app().select_image(instance)
        get_app().image_editor_controller.reset()

    @staticmethod
    def on_model_id(input):
        """ Handle entering a model ID and pressing Enter """
        get_app().switch_screen('model')
        get_app().select_model(id=int(input.text))

    @staticmethod
    def get_model(instance):
        get_app().modellist_controller.screen.show_all_chk.active = False
        get_app().modellist_controller.search = True
        get_app().modellist_controller.screen.search_field.text = ""
        get_app().modellist_controller.screen.find_model_btn.disabled = True
        get_app().modellist_controller.set_list("")
        get_app().switch_screen('modellist')


    @staticmethod
    def tesseractxplore(instance):
        get_app().switch_screen('tesseractxplore_online')
