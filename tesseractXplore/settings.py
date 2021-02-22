""" Basic utilities for reading and writing settings from config files """
from logging import getLogger
from os import makedirs, remove
from os.path import isfile
from shutil import copyfile
from typing import Dict, Any

import yaml

from tesseractXplore.constants import DATA_DIR, CONFIG_PATH, DEFAULT_CONFIG_PATH

logger = getLogger().getChild(__name__)


def read_settings() -> Dict[str, Any]:
    """  Read settings from the settings file

    Returns:
        Stored config state
    """
    if not isfile(CONFIG_PATH):
        reset_defaults()
    logger.info(f'Reading settings from {CONFIG_PATH}')
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def write_settings(new_config: Dict[str, Any]):
    """  Write updated settings to the settings file

    Args:
        new_config (dict): Updated config state
    """
    # First re-read current config, in case it changed on disk (manual edits)
    # And update on a per-section basis so we don't overwrite with an empty section
    settings = read_settings()
    logger.info(f'Writing settings to {CONFIG_PATH}')
    for k, v in new_config.items():
        settings.setdefault(k, {})
        settings[k].update(v)

    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(settings, f)


def reset_defaults():
    """ Reset settings to defaults """
    logger.info(f'Resetting {CONFIG_PATH} to defaults')
    makedirs(DATA_DIR, exist_ok=True)
    if isfile(CONFIG_PATH):
        remove(CONFIG_PATH)
    copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)


def convert_int_dict(int_dict):
    """  Convery JSOn string keys to ints """
    return {int(k): int(v) for k, v in int_dict.items() if _is_int(k) and _is_int(v)}


def _is_int(value):
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False
