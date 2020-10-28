import asyncio
from logging import getLogger

from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller, ImageBatchLoader
from tesseractXplore.image_glob import get_images_from_paths
from tesseractXplore.recognizer import recognize
from tesseractXplore.widgets import ImageMetaTile

from subprocess import check_output
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.filemanager import MDFileManager
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
        self.screen.recognize_button.bind(on_press=self.disable_rec)
        self.screen.pause_button.bind(on_press=self.stop_rec)
        self.ocr_event = None
        self.ocr_stop = False
        self.last_rec_time = time.time()

    def stop_rec(self, instance):
        """ Unschedule progress event and log total execution time """
        if self.ocr_event:
            self.ocr_stop = True
            logger.info(f'Recognizer: Canceled!')

    def init_dropdown(self):
        screen = self.screen
        # Init dropdownmenus
        models = check_output(["tesseract", "--list-langs"]).decode('utf-8').splitlines()[1:]
        self.model_menu = self.create_dropdown(screen.model, [{'text': 'Model: ' + model} for model in models], self.set_model)

        psms = [line for line in check_output(["tesseract", "--help-psm"]).decode('utf-8').splitlines()[1:] if
                line.strip() != ""]
        self.psm_menu = self.create_dropdown(screen.psm, [{'text': 'PSM: ' + psm} for psm in psms], self.set_psm)

        oems = [line for line in check_output(["tesseract", "--help-oem"]).decode('utf-8').splitlines()[1:] if
                line.strip() != ""]
        self.oem_menu = self.create_dropdown(screen.oem, [{'text': 'OEM: ' + oem} for oem in oems], self.set_oem)

        outputformats = ["txt", "alto", "hocr", "tsv", "pdf", "stdout"]
        self.outputformat_menu =  self.create_dropdown(screen.outputformat, [{'text': 'Outputformat: ' + outputformat} for outputformat in
                                                      outputformats], self.set_outputformat)

    def disable_rec(self, instance, *args):
        instance.disabled = True
        self.screen.pause_button.disabled = False

    def enable_rec(self, instance, *args):
        instance.disabled = False
        self.screen.pause_button.disabled = True

    def recognize_thread(self,instance,*args):
        import threading
        self.ocr_event = threading.Thread(target=self.recognize, args=(instance,args))
        self.ocr_event.start()

    def recognize(self, instance, *args):
        """ Recognize image with tesseract """
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
        outputformat = "txt" if self.screen.outputformat.current_item == '' else self.screen.outputformat.current_item.split(": ")[1].strip()
        proc_files, outputnames = recognize(file_list, model=model ,psm=psm, oem=oem, output_folder=self.selected_output_folder, outputformat=outputformat)
        alert(f'{proc_files} images recognized')
        self.last_rec_time = time.time()+2
        self.enable_rec(instance)

        # Update image previews with new metadata
        #previews = {img.metadata.image_path: img for img in get_app().image_selection_controller.image_previews.children}
        #for metadata in all_metadata:
        #    previews[metadata.image_path].metadata = metadata


    def reset_settings(self):
        # TODO: Rework resetting
        self.screen.model.text = self.screen.model.text+'!'
        self.screen.model.set_item('')
        self.screen.model.text = self.screen.model.text[:-1]
        self.screen.psm.text = self.screen.psm.text + '!'
        self.screen.psm.set_item('')
        self.screen.psm.text = self.screen.psm.text[:-1]
        self.screen.oem.text = self.screen.oem.text + '!'
        self.screen.oem.set_item('')
        self.screen.oem.text = self.screen.oem.text[:-1]
        self.screen.outputformat.text = self.screen.outputformat.text + '!'
        self.screen.outputformat.set_item('')
        self.screen.outputformat.text = self.screen.outputformat.text[:-1]
        self.screen.output.set_item('')
        self.selected_output_folder = None
        self.screen.output.text = f"Selected output folder: (default: inputfolder)"


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
