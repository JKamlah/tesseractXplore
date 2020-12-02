from kivy.properties import NumericProperty, BooleanProperty
from kivymd.uix.button import MDFloatingActionButton, MDRoundFlatIconButton, MDRectangleFlatButton
from kivymd.uix.list import IconRightWidget
from tesseractXplore.widgets.tooltip import MDTooltip
from tesseractXplore.widgets.tooglebutton import MDToggleButton
from tesseractXplore.app import get_app
from kivy.properties import (
    NumericProperty,
)


class StarButton(IconRightWidget):
    """
    Selectable icon button that optionally toggles between 'selected' and 'unselected' star icons
    """
    model_id = NumericProperty()
    is_selected = BooleanProperty()

    def __init__(self, model_id, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.model_id = model_id
        self.is_selected = is_selected
        self.custom_icon = 'icon' in kwargs
        self.set_icon()

    def on_press(self):
        self.is_selected = not self.is_selected
        self.set_icon()

    def set_icon(self):
        if not self.custom_icon:
            self.icon = 'star' if self.is_selected else 'star-outline'

class TooltipFloatingButton(MDFloatingActionButton, MDTooltip):
    """ Floating action button class with tooltip behavior """


class TooltipIconButton(MDRoundFlatIconButton, MDTooltip):
    """ Flat button class with icon and tooltip behavior """


class MyToggleButton(MDRectangleFlatButton, MDToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #md_bg_color: app.theme_cls.primary_dark
        self.background_down = get_app().theme_cls.primary_dark
