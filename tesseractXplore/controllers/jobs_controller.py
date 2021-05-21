import glob
import json
import os
import webbrowser
from functools import partial
from logging import getLogger
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
#from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivymd.uix.textfield import MDTextField
from tesseractXplore.widgets.datatables import MDDataTable

from tesseractXplore.app import get_app
from tesseractXplore.constants import DOWNLOAD_DIR, JOBS_DIR
from tesseractXplore.online_components import check_all_job_status, remove_jobs, dl_jobdata_to_folder, \
    dl_jobdata_as_folder
from tesseractXplore.widgets import MyToggleButton

logger = getLogger().getChild(__name__)


class JobsController:
    """ Controller class to manage online jobs"""

    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.job_data = screen.job_data
        self.job_table = None
        self.screen.update_btn.bind(on_release=self.update_jobdata)
        self.screen.download_btn.bind(on_release=self.download_to_folder)
        self.screen.download_folder_btn.bind(on_release=self.download_as_folder_dialog)
        self.screen.remove_btn.bind(on_release=self.remove_jobdata_dialog)

    def update_jobdata(self, *args):
        data = check_all_job_status()['Jobs']
        for idx, job in enumerate(data):
            if job[1] == "Finished":
                job[1] = ("checkbox-marked-circle",
                          [39 / 256, 174 / 256, 96 / 256, 1], "Finished")
            else:
                job[1] = ("alert-circle", [1, 0, 0, 1], "Running")
            job.append(("information", [255 / 256, 165 / 256, 0, 1], ""))
        if len(data) == 1:
            data.append(data[0])
        self.job_data.clear_widgets()
        layout = AnchorLayout()
        data_tables = MDDataTable(
            size_hint=(0.9, 0.9),
            use_pagination=True,
            check=True,
            column_data=[
                ("Jobname", dp(50), self.sort_on_jobname),
                ("Progress", dp(30)),
                ("Status", dp(30)),
                ("Get information", dp(30)),
            ],
            row_data=data,
        )
        data_tables.bind(on_row_press=self.show_jobdata_info)
        # TODO: Rework color settings for better readability
        layout.add_widget(data_tables)
        self.job_data.add_widget(layout)
        self.job_table = data_tables
        return

    @staticmethod
    def show_jobdata_info(instance, cell, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()

        if (cell.index+1)%4 != 0: return
        jobindex = len(cell.parent.children) - 1 - cell.range[0]
        jobname = cell.parent.children[jobindex].text
        jobfile = Path(JOBS_DIR).joinpath(jobname + '.json')
        if jobfile.exists():
            with open(jobfile, 'r') as fin:
                jobinfo = json.load(fin)
            dialog = MDDialog(title="Job description",
                              type='custom',
                              auto_dismiss=False,
                              content_cls=TextInput(text=json.dumps(jobinfo, indent=4),
                                                    size_hint_y=None,
                                                    height=get_app()._window.size[1] - 150,
                                                    readonly=True),
                              buttons=[
                                  MDFlatButton(
                                      text="DISCARD", on_release=close_dialog
                                  ),
                              ],
                              )
            if get_app()._platform not in ['win32', 'win64']:
                dialog.content_cls.focused = True
            dialog.open()
        return

    @staticmethod
    def sort_on_jobname(data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][0]
            )
        )

    def remove_jobdata_dialog(self, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()

        layout = MDBoxLayout(orientation="vertical", adaptive_height=True)
        layout.add_widget(OneLineListItem(text="You really want to delete these jobs?", font_style="H6"))
        layout.add_widget(MDTextField(text=" / ".join(set([job[0] for job in self.job_table.get_row_checks()])),
                                      multiline=True, readonly=True, mode="rectangle"))
        dialog = MDDialog(title="Remove jobdata from server",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="DELETE", on_release=partial(self.remove_jobdata)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        if get_app()._platform not in ['win32', 'win64']:
            dialog.content_cls.focused = True
        dialog.open()

    def remove_jobdata(self, instance, *args):
        instance.parent.parent.parent.parent.dismiss()
        jobs = set([job[0] for job in self.job_table.get_row_checks()])
        logger.info(remove_jobs(jobs))
        self.update_jobdata()
        return

    def download_to_folder(self, *args):
        for job in set([job[0] for job in self.job_table.get_row_checks()]):
            dl_jobdata_to_folder(job)
        return

    def download_as_folder_dialog(self, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()

        layout = MDBoxLayout(orientation="vertical", adaptive_height=True)
        layout.add_widget(OneLineListItem(text="You want to download:", font_style="H6"))
        layout.add_widget(MDTextField(text=" / ".join(set([job[0] for job in self.job_table.get_row_checks()])),
                                      multiline=True, readonly=True, mode="rectangle"))
        layout.add_widget(OneLineListItem(text="Please insert output directory!", font_style="H6"))
        layout.add_widget(MDTextField(text=DOWNLOAD_DIR, mode="rectangle"))
        layout.add_widget(OneLineListItem(text="Add images to folder?", font_style="H6"))
        boxlayout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
        defaulttoggle = MyToggleButton(text="No", group="add_images")
        boxlayout.add_widget(defaulttoggle)
        boxlayout.add_widget(MyToggleButton(text="Yes", group="add_images"))
        layout.add_widget(boxlayout)
        dialog = MDDialog(title="Download job as one folder",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=layout,
                          buttons=[
                              MDFlatButton(
                                  text="DOWNLOAD", on_release=partial(self.download_as_folder)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        defaulttoggle.state = 'down'
        if get_app()._platform not in ['win32', 'win64']:
            dialog.content_cls.focused = True
        dialog.open()

    def download_as_folder(self, instance, *args):
        instance.parent.parent.parent.parent.dismiss()
        parentinstance = instance.parent.parent.parent.children[2].children[0]
        outputdir = Path(parentinstance.children[2].text)
        add_images = False if parentinstance.children[0].children[0].state == 'normal' else True
        for job in set([job[0] for job in self.job_table.get_row_checks()]):
            dl_jobdata_as_folder(job, outputdir, add_images)
        webbrowser.open(str(outputdir.resolve()))
        return


def read_file(fname, collections):
    res = find_file(fname, collections)
    if res:
        return "".join(open(res, encoding='utf-8').readlines())
    else:
        return ""


def find_file(fname, collections):
    app = get_app()
    # if outputfolder
    if app.tesseract_controller.selected_output_folder and Path(
            app.tesseract_controller.selected_output_folder).joinpath(fname.name()).is_file():
        collections.append(os.path.join(app.tesseract_controller.selected_output_foldier, fname.name))
    # else check cwd folder
    if fname.is_file():
        collections.append(str(fname.absolute()))
    # else check cwd subfolder (depth 1)
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        collections.extend(subfoldermatch)
    # check cwd subfolder (depth 2)
    subfoldermatch = glob.glob(str(fname.parent.joinpath('**').joinpath('**').joinpath(fname.name)))
    if subfoldermatch:
        collections.extend(subfoldermatch)
    if collections:
        return collections[0]
    return None
