from kivy.properties import BooleanProperty
from kivy.properties import ListProperty
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.uix.button import ButtonBehavior
from kivymd.uix.label import MDLabel
from kivymd.uix.tooltip import MDTooltip


# TODO: Debug root cause of rogue tooltips!
class HideableTooltip(MDTooltip):
    """
    This is a workaround for unexpected behavior with tooltips and tabs. If a HideableTooltip is
    in an unselected tab, it will always report that the mouse cursor does not intersect it.
    """
    def __init__(self, is_visible_callback, **kwargs):
        self.is_visible_callback = is_visible_callback
        super().__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if self.is_visible_callback():
            super().on_mouse_pos(*args)

class HOCRLabel(RectangularRippleBehavior, ButtonBehavior,MDLabel):
    """ Label class with tooltip behavior """
    # Bug workaround; a fix has been committed, but not released
    _no_ripple_effect = BooleanProperty(False)
    def __init__(self,par_id,line_id,text,bbox,**kwargs):
        self.par_id = par_id
        self.line_id = line_id
        self.bbox = bbox
        self.edited = False
        kwargs['text'] = text
        super().__init__(**kwargs)


    def close_dialog(self, instance, *args):
        instance.parent.parent.parent.parent.dismiss()



class TooltipLabel(MDLabel, MDTooltip):
    """ Label class with tooltip behavior """
    # Bug workaround; a fix has been committed, but not released
    padding = ListProperty([0, 0, 0, 0])
