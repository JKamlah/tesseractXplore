import threading
import time
from logging import getLogger
import re

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField

from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller
from tesseractXplore.tessprofiles import write_tessprofiles, read_tessprofiles
from tesseractXplore.online_components import ocr_image, ocr_bulk_of_images
from tesseractXplore.process_manager import create_online_threadprocess

logger = getLogger().getChild(__name__)


class TesseractOnlineController(Controller):
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
        self.init_dropdown()
        self.tessprofile_menu = screen.tessprofile_menu
        self.output_manager = MDFileManager(
            exit_manager=self.exit_output_manager,
            select_path=self.select_output,
            ext=[""],
        )
        self.selected_output_folder = None
        self.screen.recognize_button.bind(on_release=self.recognize_thread)
        self.screen.jobs_button.bind(on_release=self.switch_jobs)
        self.screen.model.bind(on_release=get_app().image_selection_online_controller.get_model)
        #elf.modelinfos = get_modelinfos()
        self.print_on_screen = False
        self.ocr_event = None
        self.ocr_stop = False
        self.last_rec_time = time.time()

        # Context menu
        self.screen.context_menu.ids.recognize_ctx.bind(on_release=self.recognize_single_thread)

        # Load default settings
        self.load_default_settings()

    def load_default_settings(self):
        for profile, profileparam in get_app().tessprofiles.items():
            if profileparam['default'] == True:
                self.load_tessprofile(profileparam)

    def stop_rec(self, instance):
        """ Unschedule progress event and log total execution time """
        if self.ocr_event:
            self.ocr_stop = True
            logger.info(f'Recognizer: Canceled!')

    def init_dropdown(self):
        screen = self.screen
        # Init dropdownsettingsmenu
        self.psm_menu = self.create_dropdown(screen.psm, [{'text': 'PSM: ' + psm} for psm in self.psms], self.set_psm)

    def disable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = True


    def enable_rec(self, instance, *args):
        self.screen.recognize_button.disabled = False


    def recognize_thread(self, instance, *args, file_list=None, profile=None):
        self.disable_rec(instance, *args)
        self.ocr_event = threading.Thread(target=self.recognize, args=(instance, args),
                                          kwargs={'file_list': file_list, 'profile': profile})
        self.ocr_event.setDaemon(True)
        self.ocr_event.start()
        return self.ocr_event

    def recognize_single_thread(self, instance, *args, file_list=None, profile=None):
        self.disable_rec(instance, *args)
        self.ocr_single_event = threading.Thread(target=self.recognize, args=(instance, args),
                         kwargs={'file_list': instance.selected_image.original_source,'profile': profile})
        self.ocr_single_event.setDaemon(True)
        self.ocr_single_event.start()
        return self.ocr_single_event


    def recognize(self, instance, *args, file_list=None, profile=None):
        """ Recognize image with tesseract """
        if profile is None:
            profile = {}
        if file_list is None:
            file_list = get_app().image_selection_online_controller.file_list
        if not file_list:
            alert(f'Select images to recognize')
            self.enable_rec(instance)
            return
        logger.info(f'Main: Recognize {len(file_list)} images')
        model = profile.get("model", "eng" if self.screen.model.current_item == '' else self.screen.model.current_item.split(": ")[1].strip())
        psm = profile.get("psm", "3" if self.screen.psm.current_item == '' else self.screen.psm.current_item.split(": ")[1].strip())
        outputformats = ';'.join(profile.get("outputformats", self.active_outputformats()))
        if isinstance(file_list, str):
            print_on_screen = profile.get("print_on_screen", self.screen.print_on_screen_chk.active)
            create_online_threadprocess("Start recognize online", ocr_image, file_list, model=model, psm=psm, outputformats=outputformats, print_on_screen=print_on_screen)
        else:
            jobname = profile.get("jobname", "Job_01" if self.screen.jobname.text == '' else self.screen.jobname.text)
            jobname = re.sub(r"[\s,\.,!,/,\\]", "_", jobname)
            create_online_threadprocess(f"{jobname}: Upload images", ocr_bulk_of_images, jobname, file_list, model=model, psm=psm, outputformats=outputformats, overwrite=str(self.screen.overwrite_job_chk.active))
            self.enable_rec(instance)


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
        for outputformat in ['txt', 'hocr', 'alto', 'pdf', 'tsv']:
            if outputformat in tessprofileparams['outputformat']:
                self.screen[outputformat.strip()].state = 'down'
            else:
                self.screen[outputformat.strip()].state = 'normal'
        self.screen.print_on_screen_chk.active = True if tessprofileparams['print_on_screen'] == "True" else False
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
                          content_cls=MDTextField(text="",mode="rectangle"),
                          buttons=[
                              MDFlatButton(
                                  text="SAVE", on_release=self.save_tessprofile
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

    def save_tessprofile(self, instance):
        tessprofilename = instance.parent.parent.parent.parent.content_cls.text
        if tessprofilename != '':
            get_app().tessprofiles[tessprofilename] = {
                "model": self.screen.model.current_item.split(" ")[1] if self.screen.model.current_item.split(" ")[
                                                                             0] == "Model:" else "eng",
                "psm": "".join([char for char in self.screen.psm.text if char.isdigit()]),
                "outputformat": self.active_outputformats(),
                "print_on_screen": str(self.screen.print_on_screen_chk.active),
                "outputdir": "" if self.screen.output.text.split(" ")[0] != "Selected" else
                self.screen.output.text.split(" ")[3],
                "groupfolder": self.screen.groupfolder.text,
                "subfolder": str(self.screen.subfolder_chk.active),
                "default": False
            }
        write_tessprofiles(get_app().tessprofiles)
        instance.parent.parent.parent.parent.dismiss()

    def reset_settings(self):
        # TODO: Rework resetting
        self.reset_text(self.screen.model)
        self.reset_text(self.screen.psm)
        self.reset_text(self.screen.oem)
        self.reset_ouputformat()
        self.screen.print_on_screen_chk.active = False
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
                              position='bottom',
                              width_mult=20)
        menu.bind(on_release=callback)
        return menu

    def set_psm(self, menu, instance, *args):
        self.screen.psm.set_item(instance.text)
        self.psm_menu.dismiss()

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

    @staticmethod
    def switch_jobs(instance):
        get_app().switch_screen('jobs')
        get_app().jobs_controller.update_jobdata()