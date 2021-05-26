import json
from logging import getLogger
from os.path import isfile
from typing import Dict

from tesseractXplore.constants import TESSPROFILE_PATH, TESSPROFILE_ONLINE_PATH

logger = getLogger().getChild(__name__)


def read_tessprofiles(online=False) -> Dict:
    """ Read tessprofiles

    Returns:
        Stored tessprofiles
    """
    profile = TESSPROFILE_ONLINE_PATH if online else TESSPROFILE_PATH
    if not isfile(profile):
        tessprofiles = {}
    else:
        with open(profile) as f:
            tessprofiles = json.load(f)
    return tessprofiles


def write_tessprofiles(tessprofiles: Dict, online=False):
    """ Write tessprofiles to json

    Args:
        Complete tessprofiles
    """
    logger.info(f'Writing tessprofiles')
    profile = TESSPROFILE_ONLINE_PATH if online else TESSPROFILE_PATH
    with open(profile, 'w') as f:
        json.dump(tessprofiles, f, indent=4)
