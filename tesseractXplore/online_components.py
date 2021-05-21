""" Combined entry point for both CLI and GUI """
import hashlib
import io
import json
import tempfile
import time
import zipfile
from functools import partial
from pathlib import Path
from shutil import move, copyfile, rmtree

import requests
from kivy.uix.textinput import TextInput
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from tesseractXplore.app import get_app
from tesseractXplore.constants import JOBS_DIR, URL_TESSERACTXPLORE_ONLINE
from tesseractXplore.evaluate import evaluate_report
from tesseractXplore.font import get_font, fontproperties_dialog
from tesseractXplore.recognizer import cache_stdout_dialog, close_dialog


def authenticate() -> dict:
    if get_app().token is not None:
        return get_app().token
    user = get_app().settings_controller.username
    pwd = get_app().settings_controller.password
    headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'username': user,
            'password': pwd}
    try:
        r = requests.post(f'{URL_TESSERACTXPLORE_ONLINE}/token', headers=headers, data=data, verify=False)
    except:
        toast(f"Connection error to the host. Please try again later.")
        return {}
    if r.status_code == 401:
        status_code = create_user(user, pwd)
        if status_code != 200:
            toast('Wrong password!')
            return {}
        print(f"User created: {user}")
        r = requests.post(f'{URL_TESSERACTXPLORE_ONLINE}/token', headers=headers, data=data, verify=False)
    token = json.loads(r.text)
    return token


def create_user(user, pwd) -> int:
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = '{"username": "' + user + '","password_hash": "' + pwd + '"}'
    r = requests.post(f'{URL_TESSERACTXPLORE_ONLINE}/create_user', headers=headers, data=data, verify=False)
    return r.status_code


def hash_file(fname):
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    md5 = hashlib.md5()
    with open(fname, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def ocr_image(image, model="eng", psm="4", oem="3", outputformats=None, print_on_screen=True):
    token = authenticate()
    if not token:
        return None, None
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    files = {'image': open(f'{image}', 'rb')}
    data = {'lang': model,
            'psm': psm,
            'oem': oem,
            'outputformats': outputformats}
    r = requests.post(f'{URL_TESSERACTXPLORE_ONLINE}/api/v1/single_text', files=files, data=data, headers=headers, verify=False)
    if not outputformats or print_on_screen:
        pimage = Path(image)
        params = ["-l", model, "--psm", psm, "--oem", oem]
        dialog = MDDialog(title=pimage.name,
                          type='custom',
                          auto_dismiss=False,
                          content_cls=TextInput(text=json.loads(r.text)['text'],
                                                size_hint_y=None,
                                                height=get_app()._window.size[1] - 150,
                                                readonly=True,
                                                font_name=get_font(),
                                                font_size=int(get_app().settings_controller.screen.fontsize.text)),
                          buttons=[
                              MDFlatButton(
                                  text="SET FONT", on_release=fontproperties_dialog
                              ),
                              MDFlatButton(
                                  text="EVALUATE", on_release=partial(evaluate_report, json.loads(r.text)['text'])
                              ),
                              MDFlatButton(
                                  text="SAVE",
                                  on_release=partial(cache_stdout_dialog, pimage, json.loads(r.text)['text'], params)
                              ),
                              MDFlatButton(
                                  text="DISCARD", on_release=close_dialog
                              ),
                          ],
                          )
        if get_app()._platform not in ['win32', 'win64']:
            # TODO: Focus function seems buggy in win
            dialog.content_cls.focused = True
        # TODO: There should be a better way to set cursor to 0,0
        time.sleep(1)
        dialog.content_cls.cursor = (0, 0)
        dialog.open()
    return


def save_jobdescription(jobname, jobdescription):
    jobsdir = Path(JOBS_DIR)
    if not jobsdir.exists():
        jobsdir.mkdir()
    with open(jobsdir.joinpath(jobname + ".json"), "w") as fout:
        json.dump(jobdescription, fout)


def ocr_bulk_of_images(jobname, images, model="eng", psm="4", oem="3", outputformats=None, overwrite=True):
    """
    Create an OCR Job for multiple files
    """
    # if app.settings_controller.controls['dpi'].text.isdigit():
    #    params.extend(['--dpi', app.settings_controller.controls['dpi']])
    # if app.settings_controller.controls['extra_param'].text != "":
    #    for param in app.settings_controller.controls['extra_param'].text.split(' '):
    #        params.extend(['-c', param])
    token = authenticate()
    if token is None: return
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    imagehashs = {hash_file(image): image for image in images}
    imagefiles = {key: open(f'{val}', 'rb') for key, val in imagehashs.items()}
    data = {'jobname': jobname,
            'overwrite': overwrite,
            'lang': model,
            'psm': psm,
            'oem': oem,
            'outputformats': outputformats}
    jobdescription = data
    jobdescription['images'] = imagehashs
    save_jobdescription(jobname, jobdescription)
    r = requests.post(f'{URL_TESSERACTXPLORE_ONLINE}/api/v1/bulk',
                      files=imagefiles,
                      data=data,
                      headers=headers,
                      verify=False)
    if r.status_code == 413:
        toast("Please remove some data to create new jobs!")
    elif r.status_code == 409:
        toast("This job already exists, please set overwrite job flag to overwrite.")
    return


def check_job_status(jobname="TestJob") -> dict:
    token = authenticate()
    if token is None:
        return {}
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    r = requests.get(f'{URL_TESSERACTXPLORE_ONLINE}/users/content/{jobname}/info',
                     headers=headers,
                     verify=False)
    return json.loads(r.text)


def remove_jobs(jobs=None) -> dict:
    token = authenticate()
    if token is None:
        return {}
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    res = {}
    for jobname in jobs:
        r = requests.get(f'{URL_TESSERACTXPLORE_ONLINE}/users/content/{jobname}/remove',
                         headers=headers,
                         verify=False)
        rmtree(Path(JOBS_DIR).joinpath(jobname + ".json"))
        res = {jobname: json.loads(r.text)}

    return res


def check_all_job_status() -> dict:
    token = authenticate()
    if token is None:
        return {}
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    r = requests.get(f'{URL_TESSERACTXPLORE_ONLINE}/users/content_all',
                     headers=headers,
                     verify=False)
    return json.loads(r.text)


def resolve_hashs(jobname, fpath, add_images=False):
    jobfile = Path(JOBS_DIR).joinpath(jobname + ".json")
    if jobfile.exists():
        with open(jobfile, 'r') as fin:
            jobinfo = json.load(fin)
    add_extension = True if len(jobinfo.keys()) != len(set([Path(key).name for key in jobinfo.keys()])) else False
    for fname in fpath.glob('*'):
        fhash = fname.name.rsplit('.', 1)[0]
        imagepath = jobinfo['images'].get(fhash, None)
        if imagepath is not None:
            imagepath = Path(imagepath)
            if add_extension:
                resolve_fname = fname.parent.joinpath(imagepath.name.rsplit('.', 1)[0] + '.' + fhash + fname.suffix)
            else:
                resolve_fname = fname.parent.joinpath(imagepath.name.rsplit('.', 1)[0] + fname.suffix)
            move(fname, resolve_fname)
            if add_images:
                if add_extension:
                    copyfile(imagepath,
                             fname.parent.joinpath(imagepath.name.rsplit('.', 1)[0] + '.' + fhash + imagepath.suffix))
                else:
                    copyfile(imagepath, fname.parent.joinpath(imagepath.name))


def move_to_folder(jobname, tmpfolder):
    jobfile = Path(JOBS_DIR).joinpath(jobname + ".json")
    if jobfile.exists():
        with open(jobfile, 'r') as fin:
            jobinfo = json.load(fin)
    for fname in tmpfolder.glob('*'):
        fhash = fname.name.rsplit('.', 1)[0]
        imagepath = jobinfo['images'].get(fhash, None)
        move(fname, Path(imagepath.rsplit('.')[0] + fname.suffix))


def dl_jobdata_to_folder(jobname: str):
    token = authenticate()
    if token is None: return
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    r = requests.get(f'{URL_TESSERACTXPLORE_ONLINE}/users/content/{jobname}/data',
                     headers=headers,
                     verify=False)
    with tempfile.TemporaryDirectory() as tmpdirname:
        with zipfile.ZipFile(io.BytesIO(r.content), 'r') as myzip:
            myzip.extractall(tmpdirname)
        move_to_folder(jobname, Path(tmpdirname))
    return


def dl_jobdata_as_folder(jobname: str, outputpath, add_images=False):
    token = authenticate()
    if token is None: return
    headers = {'Authorization': token['token_type'] + ' ' + token['access_token']}
    r = requests.get(f'{URL_TESSERACTXPLORE_ONLINE}/users/content/{jobname}/data',
                     headers=headers,
                     verify=False)
    with zipfile.ZipFile(io.BytesIO(r.content), 'r') as myzip:
        myzip.extractall(str(outputpath.joinpath(jobname).resolve()))
    resolve_hashs(jobname, outputpath.joinpath(jobname), add_images=add_images)
    return
