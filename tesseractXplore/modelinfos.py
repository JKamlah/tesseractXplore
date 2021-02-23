from logging import getLogger
from subprocess import check_output, getstatusoutput
import hashlib
from pathlib import Path
import json

from tesseractXplore.app import alert, get_app

logger = getLogger().getChild(__name__)

def add_model_to_modelinfos(modelinfos, model):
    modelinfos[model.name] = {'url': model.url,
                                 'hash': sha256sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model.name +'.traineddata')),
                                 'tags': model.model.get('tags', ['']),
                                 'description': model.model.get('description', ''),
                                 'category': model.model.get('category', ''),
                                 'type': model.model.get('type', ''),
                                 'fonts': model.model.get('fonts', '')}
    write_modelinfos(modelinfos)
    return modelinfos


def update_modelinfos(modelinfos):
    tesscmd = get_app().settings_controller.tesseract['tesspath'] if get_app().settings_controller.tesseract['tesspath'] != "" else "tesseract"
    for model in check_output([tesscmd, "--tessdata-dir", get_app().settings_controller.tesseract['tessdatadir'], "--list-langs"]).decode('utf-8').splitlines()[1:]:
        if modelinfos.get(model, None) is None:
            modelinfos[model] = {'url': '',
                                 'hash': sha256sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model +'.traineddata')),
                                 'tags': [''],
                                 'description': '',
                                 'category': '',
                                 'type': '',
                                 'fonts': ['']}
    return modelinfos

def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def write_modelinfos(modelinfos):
    with open(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath('modelinfo.json'), 'w') as fout:
        json.dump(modelinfos, fout, indent=4)

def get_modelinfos():
    modelinfofile = Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath('modelinfo.json')
    if modelinfofile.exists():
        with open(modelinfofile, 'r') as fin:
            modelinfos = json.load(fin)
        modelinfos = update_modelinfos(modelinfos)
    else:
        modelinfos = {}
        modelinfos = update_modelinfos(modelinfos)
        write_modelinfos(modelinfos)
    return modelinfos
