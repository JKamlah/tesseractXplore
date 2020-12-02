from kivymd.uix.list import OneLineListItem, ThreeLineAvatarIconListItem, ImageLeftWidget
from tesseractXplore.app import alert, get_app
from tesseractXplore.controllers import Controller
from kivy.properties import StringProperty
from functools import partial

class CustomOneLineListItem(OneLineListItem):
    icon = StringProperty()

class ModelListController(Controller):
    """ Controller class to manage image metadata screen """
    def __init__(self, screen, **kwargs):
        self.screen = screen


    def set_list(self, text="", search=False):
        '''Lists all installed models '''

        def add_item(model):
            self.screen.modellist.data.append(
                {
                    "viewclass": "OneLineListItem",
                    "text": model,
                    "on_release": partial(self.set_model, model)
                }
            )
        self.screen.modellist.data = []
        for model in get_app().tesseract_controller.models:
            if search:
                if self.screen.exact_match_chk.active:
                    if text == model[:len(text)]:
                        add_item(model)
                else:
                    textparts = text.split(" ")
                    if sum([True if textpart.lower() in model.lower() else False for textpart in textparts]) == len(textparts):
                        add_item(model)
            else:
                add_item(model)

    def set_model(self, model):
        get_app().tesseract_controller.screen.model.set_item('Model: '+model)
        get_app().switch_screen('tesseract_xplore')
