#!/usr/bin/env python3
import time
import unicodedata
from collections import defaultdict, Counter, OrderedDict
from typing import DefaultDict, Dict

from kivy.uix.textinput import TextInput
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from tesseractXplore.app import get_app


def get_defaultdict(resultslvl: Dict, newlvl, instance=OrderedDict) -> None:
    """
    Creates a new dictionary instance into another
    :param resultslvl: instance of the current level
    :param newlvl: name of the new  level
    :param instance: type of the defaultdict instance
    :return:
    """
    resultslvl[newlvl] = defaultdict(instance) if not resultslvl.get(newlvl, None) else resultslvl[newlvl]
    return


def controlcharacter_check(glyph: str):
    """
    Checks if glyph is controlcharacter (unicodedata cant handle CC as input)
    :param glyph: unicode glyph
    :return:
    """
    if len(glyph) == 1 and (ord(glyph) < int(0x001F) or int(0x007F) <= ord(glyph) <= int(0x009F)):
        return True
    else:
        return False


def categorize(results: DefaultDict, category='combined') -> None:
    """
    Puts the unicode character in user-definied categories
    :param results: results instance
    :param category: category
    :return:
    """
    get_defaultdict(results["combined"], "cat")
    if category == 'combined':
        for glyph, count in results[category]['all']['character'].items():
            if controlcharacter_check(glyph):
                uname, ucat, usubcat = "L", "S", "CC"
            else:
                uname = unicodedata.name(glyph)
                ucat = unicodedata.category(glyph)
                usubcat = uname.split(' ')[0]
            get_defaultdict(results[category]["cat"], ucat[0])
            get_defaultdict(results[category]["cat"][ucat[0]], usubcat)
            get_defaultdict(results[category]["cat"][ucat[0]][usubcat], ucat)
            results[category]["cat"][ucat[0]][usubcat][ucat].update({glyph: count})
    return


def print_unicodeinfo(val: str, key: str) -> str:
    """
    Prints the occurrence, unicode character or guideline rules and additional information
    :param args: arguments instance
    :param val: count of the occurrences of key
    :param key: key (glyph or guideline rules)
    :return:
    """
    return f"{val:-{6}}  {'{'}{repr(key) if controlcharacter_check(key) else key}{'}'}{addinfo(key)}"


def addinfo(key) -> str:
    """
    Adds info to the single unicode statistics like the hexa code or the unicodename
    :param args: arguments instance
    :param key: key string (glyphs or guideline rules)
    :return:
    """
    info = " "
    if len(key) > 1 or controlcharacter_check(key): return ""
    info += unicodedata.name(key)
    return info.rstrip()


def report_subsection(report, subsection: str, result: DefaultDict, header="", subheaderinfo="") -> None:
    """
    Creats subsection reports
    :param fout: name of the outputfile
    :param subsection: name of subsection
    :param result: result instance
    :param header: header info string
    :param subheaderinfo: subheader info string
    :return:
    """
    addline = '\n'
    report += f"""
    {header}
    {subheaderinfo}{addline if subheaderinfo != "" else ""}"""
    if not result:
        report += f"""{"-" * 60}\n"""
        return report
    for condition, conditionres in result[subsection].items():
        report += f"""
        {condition}
        {"-" * len(condition)}"""
        for key, val in conditionres.items():
            if isinstance(val, dict):
                report += f"""
            {key}:"""
                for subkey, subval in sorted(val.items()):
                    if isinstance(subkey, int) or len(subkey) == 1:
                        subkey = ord(subkey)
                        report += f"""
                            {print_unicodeinfo(subval, subkey)}"""
                    else:
                        report += f"""
                            {print_unicodeinfo(subval, chr(subkey))}"""
            else:
                if isinstance(key, int):
                    report += f"""
                        {print_unicodeinfo(val, chr(key))}"""
                else:
                    report += f"""
                        {print_unicodeinfo(val, key)}"""
    report += f"""
    \n{"-" * 60}\n"""
    return report


def sum_statistics(result: DefaultDict, section: str) -> int:
    """
    Sums up all occrurences
    :param result: result instance
    :param section: section to sum
    :return:
    """
    return sum([val for subsection in result[section].values() for val in subsection.values()])


def summerize(results: DefaultDict, category: str) -> None:
    """
    Summarizes the results of multiple input data
    :param results: results instance
    :param category: category
    :return:
    """
    if category in results:
        get_defaultdict(results, "sum")
        results["sum"]["sum"] = results["sum"].get('sum', 0)
        get_defaultdict(results["sum"], category)
        results["sum"][category]["sum"] = 0
        for sectionkey, sectionval in results[category].items():
            get_defaultdict(results["sum"][category], sectionkey)
            results["sum"][category][sectionkey]["sum"] = 0
            if isinstance(list(sectionval.values())[0], dict):
                for subsectionkey, subsectionval in sorted(sectionval.items()):
                    get_defaultdict(results["sum"][category][sectionkey], subsectionkey)
                    intermediate_sum = sum(subsectionval.values())
                    results["sum"][category][sectionkey][subsectionkey]["sum"] = intermediate_sum
                    results["sum"][category][sectionkey]["sum"] += intermediate_sum
                    results["sum"][category]["sum"] += intermediate_sum
                    results["sum"]["sum"] += intermediate_sum
            else:
                intermediate_sum = sum(sectionval.values())
                results["sum"][category][sectionkey]["sum"] = intermediate_sum
                results["sum"][category]["sum"] += intermediate_sum
                results["sum"]["sum"] += intermediate_sum
    return


def get_nested_val(ndict, keys, default=0):
    """
    Returns a value or the default value for a key in a nested dictionary
    :param ndict: nested dict instance
    :param keys: keys
    :param default: default value
    :return:
    """
    # TODO: Maybe it is faster with try (ndict[allkeys]) and except (default)..
    val = default
    for key in keys:
        val = ndict.get(key, default)
        if isinstance(val, dict):
            ndict = val
        elif val == 0:
            return val
    return val


def create_report(result: DefaultDict) -> str:
    """
    Creates the report
    :param result: results instance
    :param output: output string
    :return:
    """
    fpoint = 10
    report = f"""
    Analyse-Report Version 0.1
    \n{"-" * 60}\n"""
    if "combined" in result.keys():
        subheader = f"""
        {get_nested_val(result, ['combined', 'cat', 'sum', 'Z', 'SPACE', 'Zs', 'sum']):-{fpoint}} : ASCII Spacing Symbols
        {get_nested_val(result, ['combined', 'cat', 'sum', 'N', 'DIGIT', 'Nd', 'sum']):-{fpoint}} : ASCII Digits
        {get_nested_val(result, ['combined', 'cat', 'sum', 'L', 'LATIN', 'sum']):-{fpoint}} : ASCII Letters
        {get_nested_val(result, ['combined', 'cat', 'sum', 'L', 'LATIN', 'Ll', 'sum']):-{fpoint}} : ASCII Lowercase Letters
        {get_nested_val(result, ['combined', 'cat', 'sum', 'L', 'LATIN', 'Lu', 'sum']):-{fpoint}} : ASCII Uppercase Letters
        {get_nested_val(result, ['combined', 'cat', 'sum', 'P', 'sum']):-{fpoint}} : Punctuation & Symbols
        {get_nested_val(result, ['combined', 'cat', 'sum', 'sum']):-{fpoint}} : Total Glyphes
    """
        report = report_subsection(report, "L", defaultdict(str), header="Statistics combined", subheaderinfo=subheader)
    if "combined" in result.keys():
        result["combined"]["all"]["character"] = dict(result["combined"]["all"]["character"].most_common())
        report = report_subsection(report, "all", result["combined"], header={"Overall unicode character statistics"})
    return report


def evaluate_text(text):
    """
    Reads text files, evaluate the unicode character and creates a report
    :return:
    """
    results = defaultdict(OrderedDict)
    text = unicodedata.normalize("NFC", text)

    get_defaultdict(results['single'], "TEXT")
    results['single']["TEXT"]['text'] = text

    # Analyse the combined statistics
    get_defaultdict(results, 'combined')
    results['combined']['all']['character'] = Counter(
        "".join([text for fileinfo in results['single'].values() for text in fileinfo.values()]))
    # Categorize the combined statistics with standard categories
    categorize(results, category='combined')

    # Summerize category data
    for section in ["cat", "usr"]:
        for key in set(results["combined"][section].keys()):
            summerize(results["combined"][section], key)

    # Result output
    return create_report(results)


def evaluate_report(text, *args):
    def close_dialog(instance, *args):
        instance.parent.parent.parent.parent.dismiss()

    report = evaluate_text(text)
    dialog = MDDialog(title="Report",
                      type='custom',
                      auto_dismiss=False,
                      content_cls=TextInput(text=report,
                                            size_hint_y=None,
                                            height=get_app()._window.size[1]-150,
                                            font=get_app().settings_controller.get_font(),
                                            font_size=int(get_app().settings_controller.screen.fontsize.text),
                                            readonly=True),
                      buttons=[
                          MDFlatButton(
                              text="DISCARD", on_release=close_dialog
                          ),
                      ],
                      )
    if get_app()._platform not in ['win32', 'win64']:
    # TODO: Focus function seems buggy in win
        dialog.content_cls.focused = True
    time.sleep(1)
    dialog.content_cls.cursor = (0, 0)
    dialog.open()
