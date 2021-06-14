"""
Custom widgets with more complex behavior that can't be defined in just kvlang.
See widgets.kv for non-behavioral widget settings
"""

# Not sure where else to put thus
def truncate(text: str) -> str:
    """ Truncate a label string to not exceed maximum length """
    if len(text) > MAX_LABEL_CHARS:
        text = text[:MAX_LABEL_CHARS - 2] + '...'
    return text


from tesseractXplore.constants import MAX_LABEL_CHARS
from tesseractXplore.widgets.autocomplete import AutocompleteSearch, DropdownContainer, DropdownItem
from tesseractXplore.widgets.buttons import StarButton, TooltipFloatingButton, TooltipIconButton, MyToggleButton
from tesseractXplore.widgets.images import CachedAsyncImage, IconicTaxaIcon, ImageMetaTile
from tesseractXplore.widgets.inputs import DropdownTextField, TextFieldWrapper
from tesseractXplore.widgets.labels import HideableTooltip, TooltipLabel
from tesseractXplore.widgets.lists import SortableList, SwitchListItem, TextInputListItem, ModelListItem, \
    ThumbnailListItem, ListItemWithCheckbox, LeftCheckbox
from tesseractXplore.widgets.menus import ObjectContextMenu, AutoHideMenuItem, PhotoContextMenuItem, \
    ListContextMenuItem, TessprofileContextMenuItem
from tesseractXplore.widgets.model_autocomplete import ModelAutocompleteSearch
from tesseractXplore.widgets.progress_bar import LoaderProgressBar
from tesseractXplore.widgets.spinner import FntSpinnerOption
from tesseractXplore.widgets.tabs import Tab
from tesseractXplore.widgets.zoom import Zoom
