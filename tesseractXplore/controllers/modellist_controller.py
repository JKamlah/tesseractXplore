from functools import partial

from kivy.properties import StringProperty
from kivy.clock import Clock
from kivymd.uix.list import OneLineListItem, OneLineAvatarIconListItem, TwoLineAvatarIconListItem, MDList, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton

from tesseractXplore.app import get_app
from tesseractXplore.app.screens import HOME_SCREEN_ONLINE
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
        self.modelinfos = {}
        self.screen.model_selection_button.bind(on_release=self.set_model_btn)
        self.screen.show_all_chk.bind(active=partial(self.thread_set_list))

    def thread_set_list(self, *args, text="", search=False):
        import threading
        # TODO: Why is threading still blocking the ui and the pb not working?
        if not args[0].active:
            self.layout.clear_widgets()
            self.screen.modellist.clear_widgets()
            self.screen.modellist.add_widget(self.layout)
            return
        self.ocr_single_event = threading.Thread(target=self.process_set_list, args=(args),
                                                 kwargs={'text': text,
                                                         'search': search})
        self.ocr_single_event.setDaemon(True)
        self.ocr_single_event.start()
        return

    def process_set_list(self, *args, text="", search=False):
        from kivymd.uix.progressbar import MDProgressBar
        pb = MDProgressBar(type="determinate", running_duration=1, catching_duration=1.5)
        status_bar = get_app().modellist_controller.screen.status_bar
        status_bar.clear_widgets()
        status_bar.add_widget(pb)
        pb.start()
        Clock.schedule_once(partial(self.set_list, self, *args, text=text, search=search))
        pb.stop()

    def set_list(self, *args, text="", search=False):
        ''' Lists all installed models '''

        def add_item(model):
            description = self.modelinfos.get(model).get('description','')
            description = 'No description' if description == '' else description
            item = TwoLineAvatarIconListItem(
                text=model,
                secondary_text= description,
                on_release=partial(self.set_model, model),
                size_hint=(None, None),
                size=(600,1)
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
        self.modelinfos = get_app().modelinformations.get_modelinfos()

        for model in list(self.modelinfos.keys()):
            if model == "osd": continue
            if self.screen.show_all_chk.active and len(text) == 0:
                add_item(model)
            if search and len(text) > 1:
                if self.screen.exact_match_chk.active:
                    if text == model[:len(text)]:
                        add_item(model)
                else:
                    textparts = text.split(" ")
                    if sum([True if textpart.lower() in model.lower() else False for textpart in textparts]) == len(
                            textparts):
                        add_item(model)
                    elif sum([True if textpart.lower() in " ".join(self.modelinfos.get(model).get('tags', [''])).lower() else False for textpart in textparts]) == len(
                            textparts):
                        add_item(model)
        Clock.schedule_once(partial(self.screen.modellist.add_widget, self.layout))



    def edit_description(self, model, description, instance, *args):
        def close_dialog(instance, *args):
            instance.parent.parent.parent.parent.dismiss()
        dialog = MDDialog(title=f"Edit the description of {model}",
                          type='custom',
                          auto_dismiss=False,
                          content_cls=MDTextField(text=description,mode="rectangle"),
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
        if get_app().home_screen == HOME_SCREEN_ONLINE:
            get_app().tesseract_online_controller.screen.model.set_item('Model: ' + '+'.join(selected_models))
        else:
            get_app().tesseract_controller.screen.model.set_item('Model: ' + '+'.join(selected_models))
        get_app().switch_screen(get_app().home_screen)
