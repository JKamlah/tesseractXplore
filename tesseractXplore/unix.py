"""Utilities  to work with unix os"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from functools import partial
from kivymd.uix.textfield import MDTextField

def run_cmd_with_sudo_dialog(title="",func=None):
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()
    layout = MDBoxLayout(orientation="horizontal", adaptive_height=True)
    layout.add_widget(MDTextField(hint_text="Password",password=True))
    dialog = MDDialog(title=title,
                      type='custom',
                      auto_dismiss=False,
                      content_cls=layout,
                      buttons=[
                          MDFlatButton(
                              text="ENTER", on_release=partial(func)
                          ),
                          MDFlatButton(
                              text="DISCARD", on_release=close_dialog
                          ),
                      ],
                      )
    dialog.content_cls.focused = True
    dialog.open()