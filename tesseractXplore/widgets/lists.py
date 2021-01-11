from typing import Union

from kivy.core.clipboard import Clipboard
from kivymd.uix.list import MDList, ILeftBody, ILeftBodyTouch, OneLineListItem
from kivymd.uix.list import ThreeLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextFieldRound, MDTextField
from kivymd.uix.list import IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox

from tesseractXplore.app import alert
from tesseractXplore.models import Model
from tesseractXplore.widgets.images import CachedAsyncImage


class SortableList(MDList):
    """ List class that can be sorted by a custom sort key """
    def __init__(self, sort_key=None, **kwargs):
        self.sort_key = sort_key
        super().__init__(**kwargs)

    def sort(self):
        """ Sort child items in-place using current sort key """
        children = self.children.copy()
        self.clear_widgets()
        for child in sorted(children, key=self.sort_key):
            self.add_widget(child)


class SwitchListItem(ILeftBodyTouch, MDSwitch):
    """ Switch that works as a list item """

class ListItemWithCheckbox(OneLineAvatarIconListItem):
    '''Custom list item.'''

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    '''Custom right container.'''

class TextInputListItem(OneLineListItem, MDTextFieldRound):
    """ Text input that works as a list item """

class ModelListItem(ThreeLineAvatarIconListItem):
    """ Class that displays condensed model info as a list item """
    def __init__(
            self,
            model: Union[Model, int, dict] = None,
            disable_button: bool = False,
            **kwargs,
    ):
        if not model:
            raise ValueError('Must provide either a model object or ID')
        if isinstance(model, int):
            model = Model.from_id(model)
        elif isinstance(model, dict):
            model = Model.from_dict(model)
        self.model = model

        # Set click event unless disabled
        if not disable_button:
            self.bind(on_touch_down=self._on_touch_down)
        self.disable_button = disable_button

        super().__init__(
            font_style='H6',
            text=model.name,
            secondary_text=model.rank,
            tertiary_text=model.preferred_common_name,
            **kwargs,
        )

        # Select the associated model when this list item is pressed
        self.add_widget(ThumbnailListItem(source=model.thumbnail_url or model.icon_path))

    def _on_touch_down(self, instance, touch):
        """ Copy text on right-click """
        if not self.collide_point(*touch.pos):
            return
        elif touch.button == 'right':
            Clipboard.copy(self.text)
            alert('Copied to clipboard')
        else:
            super().on_touch_down(touch)


class ThumbnailListItem(CachedAsyncImage, ILeftBody):
    """ Class that contains a model thumbnail to be used in a list item """
    def __init__(self, **kwargs):
        super().__init__(thumbnail_size='small', **kwargs)
