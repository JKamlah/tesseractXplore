import json
from logging import getLogger
from os.path import isfile
from typing import Dict

from tesseractXplore.constants import TESSPROFILE_PATH

logger = getLogger().getChild(__name__)



def read_tessprofiles() -> Dict:
    """ Read tessprofiles

    Returns:
        Stored tessprofiles
    """
    if not isfile(TESSPROFILE_PATH):
        tessprofiles = {}
    else:
        with open(TESSPROFILE_PATH) as f:
            tessprofiles = json.load(f)
    return tessprofiles


def write_tessprofiles(tessprofiles: Dict):
    """ Write tessprofiles to json

    Args:
        Complete tessprofiles
    """
    logger.info(f'Writing tessprofiles')
    with open(TESSPROFILE_PATH, 'w') as f:
        json.dump(tessprofiles, f, indent=4)