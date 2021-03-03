from logging import getLogger
from subprocess import check_output, getstatusoutput
import hashlib
from pathlib import Path
from os.path import isfile
import json
from typing import Dict, Any


from tesseractXplore.app import alert, get_app
from tesseractXplore.constants import MODELINFO_PATH


logger = getLogger().getChild(__name__)

class Modelinformations():

    def __init__(self):
        self.modelinfos = self.read_modelinfos()

    def get_modelinfos(self):
        if self.current_tessdatadir not in self.modelinfos:
            self.create_blank_modelinformations()
        return self.modelinfos.get(self.current_tessdatadir, {})

    @property
    def current_tessdatadir(self):
        return get_app().settings_controller.screen['tessdatadir'].text

    def update_modelinformations(self, model, modelinfo):
        self.modelinfos[self.current_tessdatadir][model] = modelinfo

    def add_model_to_modelinfos(self, model):
        self.modelinfos[self.current_tessdatadir][model.name] = {'url': model.url,
                                     'hash': self.sha1sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model.name +'.traineddata')),
                                     'tags': model.model.get('tags', ['']),
                                     'description': model.model.get('description', ''),
                                     'category': model.model.get('category', ''),
                                     'type': model.model.get('type', ''),
                                     'fonts': model.model.get('fonts', '')}
        self.write_modelinfos()
        return

    def write_modelinfos(self):
        """  Write updated modelinformations to the modelinformations file """
        logger.info(f'Writing modelinformations {MODELINFO_PATH}')
        with open(MODELINFO_PATH, 'w') as fout:
            json.dump(self.modelinfos, fout, indent=4)

    def read_modelinfos(self) -> Dict[str, Any]:
        """  Read settings from the settings file
        Returns:
            Stored config state
        """
        if not isfile(MODELINFO_PATH):
            return {}
        logger.info(f'Reading modelinfos {MODELINFO_PATH}')
        with open(MODELINFO_PATH, encoding="utf-8") as fin:
            return json.load(fin)

    def create_blank_modelinformations(self):
        modelinfos = {}
        tesscmd = get_app().settings_controller.tesseract['tesspath'] if get_app().settings_controller.tesseract['tesspath'] != "" else "tesseract"
        for model in check_output([tesscmd, "--tessdata-dir", get_app().settings_controller.tesseract['tessdatadir'], "--list-langs"]).decode('utf-8').splitlines()[1:]:
            if modelinfos.get(model, None) is None:
                modelinfos[model] = {'url': '',
                                     'hash': self.sha1sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model +'.traineddata')),
                                     'tags': [''],
                                     'description': '',
                                     'category': '',
                                     'type': '',
                                     'fonts': ['']}
        self.modelinfos[self.current_tessdatadir] = modelinfos
        return

    def sha1sum(self, filename):
        h = hashlib.sha1()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()
