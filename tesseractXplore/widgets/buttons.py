from kivy.properties import BooleanProperty
from kivy.properties import (
    NumericProperty,
)
from kivymd.color_definitions import colors

from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivymd.uix.button import MDFloatingActionButton, \
    MDRoundFlatIconButton, \
    MDRectangleFlatButton
from kivymd.uix.list import IconRightWidget
from kivymd.uix.tooltip import MDTooltip

from tesseractXplore.app import get_app

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
    def set_text(self, interval):
        pass


class TooltipIconButton(MDRoundFlatIconButton, MDTooltip):
    """ Flat button class with icon and tooltip behavior """

def hex_to_rgba(value, hue=0.5,normalized=False):
    value = value.lstrip('#')
    lv = len(value)
    hex = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    if normalized:
        hex = [color/255 for color in hex]
    hex.append(hue)
    return tuple(hex)

class MyToggleButton(MDToggleButton, MDRectangleFlatButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color= 0, 206, 209, 0.001
        self.background_normal = 0, 206, 209, 0.001
        #self.background_down = get_color_from_hex(colors[get_app().theme_cls.primary_palette][get_app().theme_cls.primary_hue])
        self.__is_filled = False

    def _update_bg(self, ins, val):
        """Updates the color of the background."""
        if val == "down":
            self.md_bg_color = hex_to_rgba(colors[get_app().theme_cls.primary_palette][get_app().theme_cls.primary_hue])
            if (
                self.__is_filled is False
            ):  # If the background is transparent, and the button it toggled,
                # the font color must be withe [1, 1, 1, 1].
                self.text_color = self.font_color_down
            if self.group:
                self._release_group(self)
        else:
            self.md_bg_color = self.background_normal
            if (
                self.__is_filled is False
            ):  # If the background is transparent, the font color must be the
                # primary color.
                self.text_color = hex_to_rgba(colors[get_app().theme_cls.primary_palette][get_app().theme_cls.primary_hue], hue=1.0, normalized=True)

    def on_md_bg_color(self, instance, value):
        self.background_down = hex_to_rgba(colors[get_app().theme_cls.primary_palette][get_app().theme_cls.primary_hue])
        pass

