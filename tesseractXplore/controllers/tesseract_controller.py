import threading
import time
from logging import getLogger
from subprocess import check_output, getstatusoutput

from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField

from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller
from tesseractXplore.recognizer import recognize
from tesseractXplore.tessprofiles import write_tessprofiles

logger = getLogger().getChild(__name__)


class TesseractController(Controller):
    """ Controller class to manage image selector screen """

    def __init__(self, screen):
        super().__init__(screen)
        self.screen = screen
        self.psms = ['  0    Orientation and script detection (OSD) only.',
                     '  1    Automatic page segmentation with OSD.',
                     '  2    Automatic page segmentation, but no OSD, or OCR. (not implemented)',
                     '  3    Fully automatic page segmentation, but no OSD. (Default)',
                     '  4    Assume a single column of text of variable sizes.',
                     '  5    Assume a single uniform block of vertically aligned text.',
                     '  6    Assume a single uniform block of text.', '  7    Treat the image as a single text line.',
                     '  8    Treat the image as a single word.', '  9    Treat the image as a single word in a circle.',
                     ' 10    Treat the image as a single character.',
                     ' 11    Sparse text. Find as much text as possible in no particular order.',
                     ' 12    Sparse text with OSD.',
                     ' 13    Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific.']
        self.oems = ['  0    Legacy engine only.', '  1    Neural nets LSTM engine only.',
                     '  2    Legacy + LSTM engines.', '  3    Default, based on what is available.']
        self.init_dropdown()
        self.tessprofile_menu = screen.tessprofile_menu
        self.output_manager = MDFileManager(
            exit_manager=self.exit_output_manager,
            select_path=self.select_output,
            ext=[""],
        )
        self.selected_output_folder = None
        self.screen.recognize_button.bind(on_release=self.recognize_thread)
        self.screen.pause_button.bind(on_press=self.stop_rec)
        self.screen.model.bind(on_release=get_app().image_selection_controller.get_model)
        self.models = self.get_models()
        self.ocr_event = None
        self.ocr_stop = False
        self.last_rec_time = time.time()

        # Context menu
        self.screen.context_menu.ids.recognize_ctx.bind(on_release=self.recognize_single_thread)

    def get_models(self):
        tesscmd = get_app().tesspath if get_app().tesspath != "" else "tesseract"
        if getstatusoutput(tesscmd)[0] in [1, 127]: return []
        return check_output([tesscmd, "--tessdata-dir", get_app().tessdatadir, "--list-langs"]).decode(
            'utf-8').splitlines()[1:]

    def stop_rec(self, instance):
        """ Unschedule progress event and log total execution time """
        if self.ocr_event:
            self.ocr_stop = True
            logger.info(f'Recognizer: Canceled!')

    def init_dropdown(self):
        screen = self.screen

        # Init dropdownsettingsmenu
        # TODO: Rework this mess
        # menu_items = [
        #     {
        #         "icon": "git",
        #         "text": f"Item {i}",
        #     }
        #     for i in range(5)
        # ]
        # self.settings_menu = MDDropdownMenu(
        #     caller=screen.settings_menu, items=menu_items, width_mult=4
        # )
        # Init dropdownmenu
        # psms = [line for line in check_output(["tesseract", "--help-psm"]).decode('utf-8').splitlines()[1:] if
        #        line.strip() != ""]
        self.psm_menu = self.create_dropdown(screen.psm, [{'text': 'PSM: ' + psm} for psm in self.psms], self.set_psm)

        # oems = [line for line in check_output(["tesseract", "--help-oem"]).decode('utf-8').splitlines()[1:] if
        #        line.strip() != ""]
        self.oem_menu = self.create_dropdown(screen.oem, [{'text': 'OEM: ' + oem} for oem in self.oems], self.set_oem)

    def disable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = True
        self.screen.pause_button.disabled = False

    def enable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = False
        self.screen.pause_button.disabled = True

    def recognize_thread(self, instance, *args):
        self.disable_rec(instance, *args)
        self.ocr_event = threading.Thread(target=self.recognize, args=(instance, args))
        self.ocr_event.setDaemon(True)
        self.ocr_event.start()

    def recognize_single_thread(self, instance, *args):
        self.disable_rec(instance, *args)
        threading.Thread(target=self.recognize, args=(instance, args),
                         kwargs={'file_list': [instance.selected_image.original_source]}).start()

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

        # metadata_settings = get_app().metadata
        # TODO: Handle write errors (like file locked) and show dialog
        # file_list = get_app().image_selection_controller
        model = "eng" if self.screen.model.current_item == '' else self.screen.model.current_item.split(": ")[1].strip()
        psm = "3" if self.screen.psm.current_item == '' else self.screen.psm.current_item.split(": ")[1].strip()
        oem = "3" if self.screen.oem.current_item == '' else self.screen.oem.current_item.split(": ")[1].strip()
        outputformats = self.active_outputformats()
        groupfolder = self.screen.groupfolder.text
        subfolder = self.screen.subfolder_chk.active
        proc_files, outputnames = recognize(file_list, model=model, psm=psm, oem=oem, tessdatadir=get_app().tessdatadir,
                                            output_folder=self.selected_output_folder, outputformats=outputformats,
                                            subfolder=subfolder, groupfolder=groupfolder)
        toast(f'{proc_files} images recognized')
        self.last_rec_time = time.time() + 2
        get_app().image_selection_controller.file_chooser._update_files()
        self.enable_rec(instance)

        # Update image previews with new metadata
        # previews = {img.metadata.image_path: img for img in get_app().image_selection_controller.image_previews.children}
        # for metadata in all_metadata:
        #    previews[metadata.image_path].metadata = metadata

    def active_outputformats(self):
        return [outputformat for outputformat in ['txt', 'hocr', 'alto', 'pdf', 'tsv'] if
                self.screen[outputformat].state == 'down']

    def on_tesssettings_click(self, *args):
        self.tessprofile_menu.show(*get_app().root_window.mouse_pos)

    def search_tessprofile(self):
        get_app().tessprofiles_controller.set_profiles()
        get_app().switch_screen('tessprofiles')

    def load_tessprofile(self, tessprofileparams):
        self.screen.model.set_item(f"Model: {tessprofileparams.get('model', 'eng')}")
        self.screen.psm.set_item(f"PSM: {self.psms[int(tessprofileparams['psm'])]}")
        self.screen.oem.set_item(f"OEM: {self.oems[int(tessprofileparams['oem'])]}")
        for outputformat in ['txt', 'hocr', 'alto', 'pdf', 'tsv']:
            if outputformat in tessprofileparams['outputformat']:
                self.screen[outputformat.strip()].state = 'down'
            else:
                self.screen[outputformat.strip()].state = 'normal'
        if tessprofileparams['outputdir'] != "":
            self.screen.output.set_item(f"Selected output directory: {tessprofileparams['outputdir']}")
        else:
            self.screen.output.text = ''
            self.screen.output.set_item('')
            self.screen.output.text = f"Select output directory (default: input folder)"
        self.screen.subfolder_chk.active = True if tessprofileparams['subfolder'] == "True" else False
        self.screen.groupfolder.text = tessprofileparams['groupfolder']
        return

    def save_tessprofile_dialog(self):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()

        dialog = MDDialog(title="Name of the profile",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=MDTextField(text=""),
                          buttons=[
                              MDFlatButton(
                                  text="SAVE", on_release=self.save_tessprofile
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        dialog.content_cls.focused = True
        dialog.open()

    def save_tessprofile(self, instance):
        tessprofilename = instance.parent.parent.parent.parent.content_cls.text
        if tessprofilename != '':
            get_app().tessprofiles[tessprofilename] = {
                "model": self.screen.model.current_item.split(" ")[1] if self.screen.model.current_item.split(" ")[
                                                                             0] == "Model:" else "eng",
                "psm": "".join([char for char in self.screen.psm.text if char.isdigit()]),
                "oem": "".join([char for char in self.screen.oem.text if char.isdigit()]),
                "outputformat": self.active_outputformats(),
                "outputdir": "" if self.screen.output.text.split(" ")[0] != "Selected" else
                self.screen.output.text.split(" ")[3],
                "groupfolder": self.screen.groupfolder.text,
                "subfolder": str(self.screen.subfolder_chk.active)
            }
        write_tessprofiles(get_app().tessprofiles)
        instance.parent.parent.parent.parent.dismiss()

    def reset_settings(self):
        # TODO: Rework resetting
        self.reset_text(self.screen.model)
        self.reset_text(self.screen.psm)
        self.reset_text(self.screen.oem)
        self.reset_ouputformat()
        self.selected_output_folder = None
        self.screen.output.text = ''
        self.screen.output.set_item('')
        self.screen.output.text = f"Select output directory (default: input folder)"
        self.screen.subfolder_chk.active = False
        self.screen.groupfolder.text = ''

    def reset_text(self, instance):
        instance.text = instance.text + '!'
        instance.set_item('')
        instance.text = instance.text[:-1]

    def reset_ouputformat(self):
        self.screen.txt.state = 'normal'
        self.screen.alto.state = 'normal'
        self.screen.hocr.state = 'normal'
        self.screen.pdf.state = 'normal'
        self.screen.tsv.state = 'normal'

    def create_dropdown(self, caller, item, callback):
        menu = MDDropdownMenu(caller=caller,
                              items=item,
                              position="center",
                              width_mult=20)
        menu.bind(on_release=callback)
        return menu

    def set_psm(self, menu, instance, *args):
        self.screen.psm.set_item(instance.text)
        self.psm_menu.dismiss()

    def set_oem(self, menu, instance, *args):
        self.screen.oem.set_item(instance.text)
        self.oem_menu.dismiss()

    def select_output(self, path=None):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        if path is None: return
        self.selected_output_folder = path
        self.screen.output.text = f"Selected output directory: {path}"
        self.exit_output_manager()

    def select_output_folder(self):
        self.output_manager.show("/")

    def exit_output_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''
        self.output_manager.close()
