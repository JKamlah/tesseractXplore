import asyncio
import os
from functools import partial
from logging import getLogger
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL, STDOUT
from sys import platform as _platform
import threading
from typing import List

from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivymd.uix.textfield import MDTextField

from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller
from tesseractXplore.downloader import download_with_progress, switch_to_home_for_dl
from tesseractXplore.models import Model

logger = getLogger().getChild(__name__)


class ModelViewController(Controller):
    """ Controller class to manage displaying info about a selected model """

    def __init__(self, screen):
        super().__init__(screen)

        self.screen = screen
        # Controls
        # self.model_link = screen.model_links.ids.selected_model_link_button
        self.download_button = screen.model_links.ids.download_button
        self.download_button.bind(on_release=lambda x: self.check_download_model())
        self.download_via_url_button = screen.search_tab.ids.download_via_url_button
        self.download_via_url_button.bind(on_release=lambda x: self.download_via_url_dialog())

        # Outputs
        self.selected_model = None

    def check_download_model(self):
        outputpath = Path(self.screen.tessdatadir.text).joinpath(self.screen.filename.text).absolute()
        if outputpath.exists():
            self.overwrite_existing_file_dialog(self.start_download_model,outputpath)
        else:
            self.download_model(outputpath)

    def overwrite_existing_file_dialog(self,overwrite_func, outputpath):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        layout = MDBoxLayout(orientation="vertical", adaptive_height=True)
        layout.add_widget(OneLineListItem(text="Overwrite existing destination file?", font_style="H6"))
        layout.add_widget(MDTextField(text=str(outputpath.absolute()), multiline=True, readonly=True))
        dialog = MDDialog(title="",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="OVERWRITE", on_release=partial(overwrite_func, outputpath)
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

    def start_download_model(self, outputpath, instance):
        instance.parent.parent.parent.parent.dismiss()
        self.download_model(outputpath)

    def download_model(self, outputpath):
        if self.screen.best_toggle.state == 'down':
            self.selected_model.url = self.selected_model.url['best']['url'] + self.selected_model.model['name']
            self.selected_model.model['type'] = 'best'
        else:
            self.selected_model.url= self.selected_model.url['fast']['url'] + self.selected_model.model['name']
            self.selected_model.model['type'] = 'fast'
        logger.info(f'Download: {self.selected_model.url} -> {str(outputpath)}')
        if outputpath.parent.exists():
            if not self.check_folder_access(outputpath.parent):
                return self.unlock_folder_dialog(outputpath.parent, outputpath, self.selected_model.url)
        else:
            try:
                outputpath.parent.mkdir(parents=True)
            except PermissionError:
                mainfolder = self.get_permitted_folder(outputpath)
                if not self.check_folder_access(mainfolder):
                    return self.unlock_folder_dialog(mainfolder, outputpath, self.selected_model.url)
                logger.warning("Could not create folder '%s'", outputpath)
            except:
                logger.warning("Could not create folder '%s'", outputpath)
        switch_to_home_for_dl()
        toast(f"Download: {self.selected_model.model['name']}")
        self._dl_model(self.selected_model.url,outputpath)

    def download_via_url_dialog(self):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        layout = MDBoxLayout(orientation="vertical", adaptive_height=True)
        layout.add_widget(OneLineListItem(text="Options for download via URL", font_style="H6"))
        layout.add_widget(OneLineListItem(text="URL to model"))
        layout.add_widget(MDTextField(text=""))
        layout.add_widget(OneLineListItem(text="Downloadpath"))
        layout.add_widget(MDTextField(text=self.screen.tessdatadir.text))
        layout.add_widget(OneLineListItem(text="Modelname (default: filename)"))
        layout.add_widget(MDTextField(text=""))
        dialog = MDDialog(title="",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="DOWNLOAD", on_release=partial(self.check_download_via_url)
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

    def check_download_via_url(self, instance, *args):
        instance.parent.parent.parent.parent.dismiss()
        parentinstance = instance.parent.parent.parent.children[2].children[0]

        url = parentinstance.children[4].text
        outputpath = parentinstance.children[2].text
        modelname = parentinstance.children[0].text
        if modelname == "":
            modelname = Path(url).name
        if ".traineddata" not in modelname:
            modelname += ".traineddata"
        outputpath = Path(outputpath).joinpath(modelname)
        self.selected_model = Model.from_dict({'modelgroup':'',
                                               'name': modelname.rsplit('.',1)[0],
                                               'url': url,
                                               'model': {'name': modelname,
                                                         'tags': [''],
                                                         'description': '',
                                                         'category': '',
                                                         'type': '',
                                                         'fonts': ['']}})
        if outputpath.exists():
            self.overwrite_existing_file_dialog(self.download_via_url, outputpath)
        else:
            self.download_via_url(outputpath)

    def download_via_url(self, outputpath):
        switch_to_home_for_dl()
        toast(f"Download: {self.selected_model.url}")
        self._dl_model(self.selected_model.url, outputpath)



    def _dl_model(self, url, outputpath):
        from tesseractXplore.process_manager import create_threadprocess
        create_threadprocess("Start download model", download_with_progress, url, outputpath, self.update_models)

    def update_models(self, instance, *args):
        toast('Download: Succesful')
        logger.info(f'Download: Succesful')
        # Update Modelslist
        get_app().modelinformations.add_model_to_modelinfos(self.selected_model)


    def select_model(self, model_obj: Model = None, model_dict: dict = None, id: int = None, if_empty: bool = False):
        """ Update model info display by either object, ID, partial record, or complete record """
        # Initialize from object, dict, or ID
        if if_empty and self.selected_model is not None:
            return
        if not any([model_obj, model_dict, id]):
            return
        if not model_obj:
            model_obj = Model.from_dict(model_dict) if model_dict else Model.from_id(int(id))
        # Don't need to do anything if this model is already selected
        if self.selected_model is not None and model_obj.id == self.selected_model.id:
            return

        logger.info(f'Model: Selecting model {model_obj.id}')
        # self.screen.basic_info.clear_widgets()
        self.selected_model = model_obj
        asyncio.run(self.load_model_info())

        # Add to model history, and update model id on image selector screen
        get_app().update_history(self.selected_model.id)
        get_app().select_model_from_photo(self.selected_model.id)

    def check_folder_access(self, folderpath):
        if not os.access(folderpath, os.W_OK):
            return False
        return True

    def get_permitted_folder(self, outputpath):
        mainfolder = outputpath.parent
        while not mainfolder.exists():
            mainfolder = mainfolder.parent
        return mainfolder


    def unlock_folder_dialog(self, folderpath, outputpath, url):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        layout = MDBoxLayout(orientation="vertical", adaptive_height=True)
        layout.add_widget(MDTextField(text="Sudo password to change the rights of the destination folder", font_style="H6"))
        layout.add_widget(MDTextField(hint_text="Password",password=True))
        dialog = MDDialog(title="",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="ENTER", on_release=partial(self.unlock_folder, folderpath, outputpath, url)
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

    def unlock_folder(self, folderpath, outputpath, url, instance, *args):
        instance.parent.parent.parent.parent.dismiss()
        pwd = instance.parent.parent.parent.parent.content_cls.children[1].text
        if _platform not in ["win32", "win64"]:
            set_userrights = Popen(['sudo', '-S', 'chmod', 'o+rw', str(folderpath.absolute())],
                               stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
        else:
            toast(f"Please set write rights for the current user to folder {folderpath}")
            return
            # TODO: Make the cmd run
            #set_userrights = Popen(['runas', '/noprofile', '/user:Administrator', 'NeedsAdminPrivilege.exe'],
            #                       stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
        set_userrights.stdin.write(bytes(pwd, 'utf-8'))
        set_userrights.communicate()
        if not outputpath.parent.exists():
            outputpath.parent.mkdir(parents=True)
        self._dl_model(url,outputpath)
        return

    async def load_model_info(self):
        await asyncio.gather(
            self.load_basic_info_section(),
        )

    async def load_basic_info_section(self):
        """ Load basic info for the currently selected model """
        # Name, rank
        logger.info('Model: Loading basic info section')
        # Icon (if available)

        # TODO: Can we apply an icon for the categories?
        # icon_path = None #get_icon_path(self.selected_model.scrip)
        # if icon_path:
        #    item.add_widget(ImageLeftWidget(source=icon_path))
        self.screen.model_header.text = 'Model: '+self.selected_model.name
        self.screen.basic_info.text = self.selected_model.name
        self.screen.basic_info.secondary_text = self.selected_model.modelgroup

        self.download_button.disabled = False

        self.screen.info_description.secondary_text = self.selected_model.model['description']
        self.screen.info_tags.clear_widgets()
        for tag in self.selected_model.model['tags']:
            self.screen.info_tags.add_widget(OneLineListItem(text=tag,
                                                             font_style='Subtitle2', text_color="FFFFFF"))
        self.screen.info_category.secondary_text = self.selected_model.model['category']
        self.screen.filename.set_text(self.screen.filename ,self.selected_model.model['name'])

        # Star Button
        # star_icon = StarButton(
        #    1,
        #    is_selected=get_app().is_starred(1),
        # )
        # star_icon.bind(on_release=self.on_star)
        # item.add_widget(star_icon)

        # Other attrs

    #    for k in ['name']:
    #        label = k.title().replace('_', ' ')
    #        value = getattr(self.selected_model, k)
    #        item = OneLineListItem(text=f'id: {value}')
    #        self.basic_info.add_widget(item)

    def on_star(self, button):
        """ Either add or remove a model from the starred list """
        if button.is_selected:
            get_app().add_star(self.selected_model.id)
        else:
            get_app().remove_star(self.selected_model.id)


def _get_label(text: str, items: List) -> str:
    return text + (f' ({len(items)})' if items else '')
