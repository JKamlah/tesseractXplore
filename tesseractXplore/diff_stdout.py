import difflib
from functools import partial

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem

from tesseractXplore.app import alert, get_app
from tesseractXplore.stdout_cache import read_stdout_cache
from tesseractXplore.font import get_fontstyle


def close_dialog(instance, *args):
    instance.parent.parent.parent.parent.dismiss()


def diff_dialog(instance, *args):
    image = instance.selected_image.original_source
    stdout_cache = read_stdout_cache(image)
    layout = MDList()
    if len(stdout_cache.keys()) == 0:
        alert("No stdout text available.")
        return
    item = OneLineListItem(text="Select first text", on_release=partial(select_text, stdout_cache.keys()))
    layout.add_widget(item)
    item = OneLineListItem(
        text="Select second text",
        on_release=partial(select_text, stdout_cache.keys()),
    )
    layout.add_widget(item)
    dialog = MDDialog(title="Compare stdouts",
                      type='custom',
                      auto_dismiss=False,
                      content_cls=layout,
                      buttons=[
                          MDFlatButton(
                              text="COMPARE", on_release=partial(diff, stdout_cache, image)
                          ),
                          MDFlatButton(
                              text="DISCARD", on_release=close_dialog
                          ),
                      ],
                      )
    dialog.open()


def set_text(key, diff_instance, select_instance, *args):
    diff_instance.text = key
    select_instance.parent.parent.parent.parent.dismiss()


def select_text(stdout_keys, instance, *args):
    layout = MDList()
    for key in stdout_keys:
        item = OneLineListItem(
            text=key,
            on_release=partial(set_text, key, instance),
        )
        layout.add_widget(item)
    dialog = MDDialog(title="Select text",
                      type='custom',
                      auto_dismiss=False,
                      content_cls=layout,
                      )
    dialog.open()


def set_item(instance, instance_menu, instance_menu_item):
    instance.text = instance_menu.text
    instance_menu.dismiss()


def diff(stdout_cache, image, instance, *args):
    close_dialog(instance)
    fst_key = instance.parent.parent.parent.parent.content_cls.children[0].text
    fst_text = "\n".join([line for line in stdout_cache[fst_key]["fulltext"].split("\n") if line.strip() != ""])
    snd_key = instance.parent.parent.parent.parent.content_cls.children[1].text
    snd_text = "\n".join([line for line in stdout_cache[snd_key]["fulltext"].split("\n") if line.strip() != ""])
    s = difflib.SequenceMatcher(None, fst_text, snd_text)
    text = f"[b][color=b39ddb]{fst_key}[/color][/b]\n" \
           f"[b][color=00FFFF]{snd_key}[/color][/b]\n\n" \
           f"Ratio between both texts: {round(s.ratio(), 3)}\n\n"
    for groupname, *value in s.get_opcodes():
        if groupname == "equal":
            text += fst_text[value[0]:value[1]]
        elif groupname == "replace":
            text += '[color=b39ddb]' + fst_text[value[0]:value[1]] + "[/color]" + "[color=00FFFF]" + snd_text[
                                                                                                     value[2]:value[
                                                                                                         3]] + "[/color]"
        elif groupname == "add":
            text += "[color=00FFFF]" + snd_text[value[2]:value[3]] + "[/color]"
        else:
            text += "[color=b39ddb]" + fst_text[value[0]:value[1]] + "[/color]"
    return diff_result(text, image)


def diff_result(text, image):
    # TODO: Rework the implementation
    layoutlist = MDList()
    get_app().diffstdout_controller.screen['scrollview'].clear_widgets()
    # layoutlist =
    from kivymd.uix.label import MDLabel
    for textline in text.split("\n"):
        item = MDLabel(
            text=textline,
            markup=True,
            font_style=get_fontstyle(),
            theme_text_color="Primary"
        )
        item.bg_color = (0, 0, 0, 1)
        item.size_hint_y = None
        item.height = 40
        layoutlist.add_widget(item)
    get_app().diffstdout_controller.screen['scrollview'].add_widget(layoutlist)
    get_app().diffstdout_controller.screen['image'].source = image
    get_app().switch_screen('diffstdout')
    get_app().modellist_controller.search = True
