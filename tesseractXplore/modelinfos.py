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

    @property
    def current_tessdatadir(self):
        return get_app().settings_controller.screen['tessdatadir'].text

    def update_modelinformations(self, model, modelinfo):
        self.modelinfos[self.current_tessdatadir][model] = modelinfo

    def add_model_to_modelinfos(self, model):
        self.modelinfos[self.current_tessdatadir][model.model['name'].replace('.traineddata','')] = {'url': model.url,
                                     'hash': self.sha1sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model.model['name'])),
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
        logger.info(f'Reading modelinfos {MODELINFO_PATH}')
        if not isfile(MODELINFO_PATH):
            return {}
        with open(MODELINFO_PATH, encoding="utf-8") as fin:
            return json.load(fin)

    @property
    def installed_models(self):
        try:
            tesscmd = get_app().settings_controller.tesseract['tesspath'] if \
                get_app().settings_controller.tesseract['tesspath'] != "" else "tesseract"
            return check_output(
                [tesscmd, "--tessdata-dir", self.current_tessdatadir, "--list-langs"], universal_newlines=True).splitlines()[1:]
        except:
            from kivymd.toast import toast
            toast("Please install Tesseract!")
            return {}

    def get_modelinfos(self):
        if self.current_tessdatadir not in self.modelinfos:
            self.modelinfos[self.current_tessdatadir] = {}
        missing_models = set(self.installed_models).difference(set(self.modelinfos[self.current_tessdatadir].keys()))
        if missing_models:
            for model in missing_models:
                self.modelinfos[self.current_tessdatadir][model] = {'url': '',
                                     'hash': self.sha1sum(Path(get_app().settings_controller.tesseract['tessdatadir']).joinpath(model +'.traineddata')),
                                     'tags': [''],
                                     'description': '',
                                     'category': '',
                                     'type': '',
                                     'fonts': ['']}
            self.write_modelinfos()
        return self.modelinfos[self.current_tessdatadir]

    def sha1sum(self, filename):
        h = hashlib.sha1()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()
