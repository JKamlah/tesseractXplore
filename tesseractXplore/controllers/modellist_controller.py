from functools import partial

from kivy.properties import StringProperty
from kivymd.uix.list import OneLineListItem, OneLineAvatarIconListItem, TwoLineAvatarIconListItem, MDList, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton

from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller
from tesseractXplore.widgets import LeftCheckbox

class CustomOneLineListItem(OneLineListItem):
    icon = StringProperty()


class ModelListController(Controller):
    """ Controller class to manage image metadata screen """

    def __init__(self, screen, **kwargs):
        self.screen = screen
        self.layout = MDList()
        self.checked_models = None
        self.screen['model_selection_button'].bind(on_release=self.set_model_btn)

    def set_list(self, text="", search=False):
        '''Lists all installed models '''

        def add_item(model):
            description = get_app().modelinformations.get_modelinfos().get(model).get('description','')
            description = 'No description' if description  == '' else description
            item = TwoLineAvatarIconListItem(
                text=model,
                secondary_text= description,
                on_release=partial(self.set_model, model),
            )
            if model not in self.checked_models:
                self.checked_models[model] = False
            item.add_widget(LeftCheckbox(active=self.checked_models[model]))
            item.add_widget(IconRightWidget(icon='file-edit', on_release=partial(self.edit_description, model, description)))
            self.layout.add_widget(item)

        if self.checked_models is None:
            self.checked_models = {}
            for model in list(get_app().modelinformations.get_modelinfos().keys()):
                self.checked_models[model] = False
        else:
            self.chk_active_models()
        self.layout.clear_widgets()
        self.screen.modellist.clear_widgets()
        for model in list(get_app().modelinformations.get_modelinfos().keys()):
            if search:
                if self.screen.exact_match_chk.active:
                    if text == model[:len(text)]:
                        add_item(model)
                else:
                    textparts = text.split(" ")
                    if sum([True if textpart.lower() in model.lower() else False for textpart in textparts]) == len(
                            textparts):
                        add_item(model)
            else:
                add_item(model)
        self.screen.modellist.add_widget(self.layout)

    def edit_description(self, model, description, instance, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        dialog = MDDialog(title=f"Edit the description of {model}",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=MDTextField(text=description),
                          buttons=[
                              MDFlatButton(
                                  text="SAVE", on_release=partial(self.save_description, model, instance)
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

    def save_description(self, model, model_instance, dialog_instance, *args):
        dialog_instance.parent.parent.parent.parent.dismiss()
        model_instance.parent.parent.children[2].children[1].text = dialog_instance.parent.parent.parent.children[2].children[0].text
        modelinfo = get_app().modelinformations.get_modelinfos().get(model)
        modelinfo['description'] = dialog_instance.parent.parent.parent.children[2].children[0].text
        get_app().modelinformations.update_modelinformations(model, modelinfo)
        get_app().modelinformations.write_modelinfos()

    def chk_active_models(self):
        for model in self.layout.children:
            self.checked_models[model.children[2].children[2].text] = model.children[1].children[0].active

    def set_model_btn(self, instance, *args):
        self.set_model("")

    def set_model(self, model, *args):
        selected_models = []
        if model != "": selected_models.append(model)
        self.chk_active_models()
        for chk_model, state in self.checked_models.items():
            if state and chk_model != model:
                selected_models.append(chk_model)
        get_app().tesseract_controller.screen.model.set_item('Model: ' + '+'.join(selected_models))
        get_app().switch_screen('tesseract_xplore')
