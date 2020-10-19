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

logger = getLogger().getChild(__name__)


class TesseractController(Controller):
    """ Controller class to manage image selector screen """
    def __init__(self, screen):
        super().__init__(screen)
        self.screen = screen
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

        self.output_manager = MDFileManager(
            exit_manager=self.exit_output_manager,
            select_path=self.select_output,
            ext=[""],
        )
        self.selected_output_folder = None
        self.screen.recognize_button.bind(on_release=self.recognize)

    def recognize(self, *args):
        """ Recognize image with tesseract """
        file_list = get_app().image_selection_controller.file_list
        if not file_list:
            alert(f'Select images to recognize')
            return
        #if not self.input_dict['observation_id'] and not self.input_dict['taxon_id']:
        #    alert(f'Select either an observation or an organism to tag images with')
        #    return
        logger.info(f'Main: Recognize {len(file_list)} images')

        #metadata_settings = get_app().metadata
        # TODO: Handle write errors (like file locked) and show dialog
        model = "eng" if self.screen.model.current_item == '' else self.screen.model.current_item.split(": ")[1].strip()
        psm = "3" if self.screen.psm.current_item == '' else self.screen.psm.current_item.split(": ")[1].strip()
        oem = "3" if self.screen.oem.current_item == '' else self.screen.oem.current_item.split(": ")[1].strip()
        outputformat = "txt" if self.screen.outputformat.current_item == '' else self.screen.outputformat.current_item.split(": ")[1].strip()
        outputnames = recognize(file_list, model=model ,psm=psm, oem=oem, output_folder=self.selected_output_folder, outputformat=outputformat)
        alert(f'{len(file_list)} images recognized')

        # Update image previews with new metadata
        #previews = {img.metadata.image_path: img for img in get_app().image_selection_controller.image_previews.children}
        #for metadata in all_metadata:
        #    previews[metadata.image_path].metadata = metadata

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
