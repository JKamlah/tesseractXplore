from logging import getLogger
import threading

from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller, ImageBatchLoader
from tesseractXplore.recognizer import recognize

from subprocess import check_output
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast

import time

logger = getLogger().getChild(__name__)


class TesseractController(Controller):
    """ Controller class to manage image selector screen """
    def __init__(self, screen):
        super().__init__(screen)
        self.screen = screen
        self.init_dropdown()
        self.output_manager = MDFileManager(
            exit_manager=self.exit_output_manager,
            select_path=self.select_output,
            ext=[""],
        )
        self.selected_output_folder = None
        self.screen.recognize_button.bind(on_release=self.recognize_thread)
        self.screen.pause_button.bind(on_press=self.stop_rec)
        self.screen.model.bind(on_release=get_app().image_selection_controller.get_model)
        self.models = check_output(["tesseract", "--list-langs"]).decode('utf-8').splitlines()[1:]
        self.ocr_event = None
        self.ocr_stop = False
        self.last_rec_time = time.time()
        # Context menu
        self.screen.context_menu.ids.recognize_ctx.bind(on_release=self.recognize_single_thread)
        # Settings menu

    def stop_rec(self, instance):
        """ Unschedule progress event and log total execution time """
        if self.ocr_event:
            self.ocr_stop = True
            logger.info(f'Recognizer: Canceled!')

    def init_dropdown(self):
        screen = self.screen

        # Init dropdownsettingsmenu
        # TODO: Rework this mess
        menu_items = [
            {
                "icon": "git",
                "text": f"Item {i}",
            }
            for i in range(5)
        ]
        self.settings_menu = MDDropdownMenu(
            caller=screen.settings_menu, items=menu_items, width_mult=4
        )
        # Init dropdownmenu
        #psms = [line for line in check_output(["tesseract", "--help-psm"]).decode('utf-8').splitlines()[1:] if
        #        line.strip() != ""]
        psms = ['  0    Orientation and script detection (OSD) only.', '  1    Automatic page segmentation with OSD.', '  2    Automatic page segmentation, but no OSD, or OCR. (not implemented)', '  3    Fully automatic page segmentation, but no OSD. (Default)', '  4    Assume a single column of text of variable sizes.', '  5    Assume a single uniform block of vertically aligned text.', '  6    Assume a single uniform block of text.', '  7    Treat the image as a single text line.', '  8    Treat the image as a single word.', '  9    Treat the image as a single word in a circle.', ' 10    Treat the image as a single character.', ' 11    Sparse text. Find as much text as possible in no particular order.', ' 12    Sparse text with OSD.', ' 13    Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific.']
        self.psm_menu = self.create_dropdown(screen.psm, [{'text': 'PSM: ' + psm} for psm in psms], self.set_psm)

        #oems = [line for line in check_output(["tesseract", "--help-oem"]).decode('utf-8').splitlines()[1:] if
        #        line.strip() != ""]
        oems = ['  0    Legacy engine only.', '  1    Neural nets LSTM engine only.', '  2    Legacy + LSTM engines.', '  3    Default, based on what is available.']
        self.oem_menu = self.create_dropdown(screen.oem, [{'text': 'OEM: ' + oem} for oem in oems], self.set_oem)

    def disable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = True
        self.screen.pause_button.disabled = False

    def enable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = False
        self.screen.pause_button.disabled = True

    def recognize_thread(self,instance,*args):
        self.disable_rec(instance, *args)
        self.ocr_event = threading.Thread(target=self.recognize, args=(instance,args))
        self.ocr_event.start()

    def recognize_single_thread(self,instance,*args):
        self.disable_rec(instance,*args)
        threading.Thread(target=self.recognize,args=(instance,args),kwargs={'file_list':[instance.selected_image.original_source]}).start()

    def recognize(self, instance, *args, file_list=None):
        """ Recognize image with tesseract """
        if file_list is None:
            file_list = get_app().image_selection_controller.file_list
        if not file_list:
            alert(f'Select images to recognize')
            self.enable_rec(instance)
            return
        if instance._ButtonBehavior__touch_time < self.last_rec_time:
            self.enable_rec(instance)
            return

        logger.info(f'Main: Recognize {len(file_list)} images')

        #metadata_settings = get_app().metadata
        # TODO: Handle write errors (like file locked) and show dialog
        model = "eng" if self.screen.model.current_item == '' else self.screen.model.current_item.split(": ")[1].strip()
        psm = "3" if self.screen.psm.current_item == '' else self.screen.psm.current_item.split(": ")[1].strip()
        oem = "3" if self.screen.oem.current_item == '' else self.screen.oem.current_item.split(": ")[1].strip()
        outputformats = [format for format in ['txt','hocr','alto','pdf','tsv'] if self.screen[format].active]
        groupfolder = self.screen.groupfolder.text
        subfolder = self.screen.subfolder_chk.active
        proc_files, outputnames = recognize(file_list, model=model ,psm=psm, oem=oem, output_folder=self.selected_output_folder, outputformats=outputformats, subfolder=subfolder,groupfolder=groupfolder)
        toast(f'{proc_files} images recognized')
        self.last_rec_time = time.time()+2
        self.enable_rec(instance)

        # Update image previews with new metadata
        #previews = {img.metadata.image_path: img for img in get_app().image_selection_controller.image_previews.children}
        #for metadata in all_metadata:
        #    previews[metadata.image_path].metadata = metadata


    def reset_settings(self):
        # TODO: Rework resetting
        self.reset_text(self.screen.model)
        self.reset_text(self.screen.psm)
        self.reset_text(self.screen.oem)
        self.reset_text(self.screen.outputformat)
        self.selected_output_folder = None
        self.screen.output.text = f""
        self.screen.output.set_item('')
        self.screen.output.text = f"Select output folder (default: input folder)"

    def reset_text(self, instance):
        instance.text = instance.text+'!'
        instance.set_item('')
        instance.text = instance.text[:-1]

    def create_dropdown(self, caller, item, callback):
        return MDDropdownMenu(caller=caller,
                       items=item,
                       position="center",
                       width_mult=20,
                       callback=callback)

    def set_model(self, instance):
        self.screen.model.set_item(instance.text)
        self.model_menu.dismiss()

    def set_psm(self, instance):
        self.screen.psm.set_item(instance.text)
        self.psm_menu.dismiss()

    def set_oem(self, instance):
        self.screen.oem.set_item(instance.text)
        self.oem_menu.dismiss()

    def set_outputformat(self, instance):
        self.screen.outputformat.set_item(instance.text)
        self.outputformat_menu.dismiss()

    def select_output(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''

        self.selected_output_folder = path
        self.screen.output.text = f"Selected output folder: {path}"
        self.exit_output_manager()

    def select_output_folder(self):
        self.output_manager.show("/")

    def exit_output_manager(self):
        '''Called when the user reaches the root of the directory tree.'''
        self.output_manager.close()

    def show_example_grid_bottom_sheet(self):
        from kivymd.uix.bottomsheet import MDGridBottomSheet

        bs_menu = MDGridBottomSheet()
        bs_menu.add_item(
            "Facebook",
            icon_src="play",
            callback=self.set_model
        )