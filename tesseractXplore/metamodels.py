""" Basic utilities for reading and writing settings from config files """
from logging import getLogger
from os import makedirs
from os.path import isfile
from shutil import copyfile
from typing import Dict, Any

import yaml

from tesseractXplore.constants import DATA_DIR, DEFAULT_MODEL_PATH, MODEL_PATH

logger = getLogger().getChild(__name__)


def read_metamodels() -> Dict[str, Any]:
    """  Read settings from the settings file

    Returns:
        Stored config state
    """
    if not isfile(MODEL_PATH):
        reset_defaults()
    logger.info(f'Reading settings from {MODEL_PATH}')
    with open(DEFAULT_MODEL_PATH) as f:
        return setdefault(yaml.safe_load(f))


def reset_defaults():
    """ Reset settings to defaults """
    logger.info(f'Resetting {MODEL_PATH} to defaults')
    makedirs(DATA_DIR, exist_ok=True)
    copyfile(DEFAULT_MODEL_PATH, MODEL_PATH)


def setdefault(metamodel: Dict[str, Any]):
    """ Setting default that no value is missing """
    for maincat in metamodel.values():
        maincat.setdefault('types', {})
        maincat.setdefault('scrape', True)
        maincat.setdefault('models', {})
        for model in maincat['models'].values():
            model.setdefault('name', '')
            model.setdefault('alias', [])
            model.setdefault('description', '')
            model.setdefault('category', '')
            model.setdefault('type', [])
            model.setdefault('fonts', [])
            model.setdefault('unicode', {})
            model['unicode'].setdefault('false', '')
            model['unicode'].setdefault('low', '')
            model['unicode'].setdefault('missing', '')
            model.setdefault('dataset', {})
            model['dataset'].setdefault('name', '')
            model['dataset'].setdefault('description', {})
            model['dataset'].setdefault('url', '')
    return metamodel


# TODO: Implement writting and uploading modelfiles to github
# def write_settings(new_config: Dict[str, Any]):
#     """  Write updated settings to the settings file
#
#     Args:
#         new_config (dict): Updated config state
#     """
#     # First re-read current config, in case it changed on disk (manual edits)
#     # And update on a per-section basis so we don't overwrite with an empty section
#     settings = read_settings()
#     logger.info(f'Writing settings to {CONFIG_PATH}')
#     for k, v in new_config.items():
#         settings.setdefault(k, {})
#         settings[k].update(v)
#
#     with open(CONFIG_PATH, 'w') as f:
#         yaml.safe_dump(settings, f)
#
#


def convert_int_dict(int_dict):
    """  Convery JSOn string keys to ints """
    return {int(k): int(v) for k, v in int_dict.items() if _is_int(k) and _is_int(v)}


def _is_int(value):
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False
