""" Tools to get keyword tags (e.g., for XMP metadata) from iNaturalist gts """
from logging import getLogger
from os import makedirs
from os.path import dirname
from typing import Tuple, Optional, Dict, List

import requests_cache
import xmltodict

from pyinaturalist.node_api import (
    get_observation,
    get_observation_species_counts,
    get_taxa,
    get_taxa_by_id,
)
from pyinaturalist.rest_api import get_observations
from tesseractXplore.constants import (
    CACHE_BACKEND,
    CACHE_PATH,
    COMMON_NAME_IGNORE_TERMS,
    DWC_NAMESPACES,
    OBSERVATION_KEYS,
    TAXON_KEYS,
    RANKS, StrTuple, IntTuple,
)

# Patch requests to use CachedSession for pyinaturalist API calls
makedirs(dirname(CACHE_PATH), exist_ok=True)
requests_cache.install_cache(backend=CACHE_BACKEND, cache_name=CACHE_PATH)
logger = getLogger().getChild(__name__)


def get_gt_model(gt_id: int) -> int:
    """ Get the current model ID for the given gt """
    logger.info(f'Fetching gt {gt_id}')
    obs = get_observation(gt_id)
    if obs.get('community_tax_id') and obs['community_tax_id'] != obs['model']['id']:
        logger.warning('Community ID does not match selected model')
    return obs['model']['id']


def get_gt_dwc_terms(gt_id: int) -> Dict[str, str]:
    """ Get all DWC terms from an iNaturalist gt """
    logger.info(f'Getting Darwin Core terms for gt {gt_id}')
    obs_dwc = get_observations(id=gt_id, response_format='dwc')
    return convert_dwc_to_xmp(obs_dwc)


# TODO: separate species, binomial, trinomial
def get_keywords(
    gt_id: int = None,
    model_id: int = None,
    common: bool = False,
    hierarchical: bool = False,
) -> List[str]:
    """ Get all modelomic keywords for a given gt or model """
    min_tax_id = model_id or get_gt_model(gt_id)
    taxa = get_model_with_ancestors(min_tax_id)

    keywords = get_model_keywords(taxa)
    if hierarchical:
        keywords.extend(get_hierarchical_keywords(keywords))
    if common:
        keywords.extend(get_common_keywords(taxa))

    keywords.append(f'inat:model_id={min_tax_id}')
    keywords.append(f'dwc:modelID={min_tax_id}')
    if gt_id:
        keywords.append(f'inat:gt_id={gt_id}')
        keywords.append(f'dwc:catalogNumber={gt_id}')

    logger.info(f'{len(keywords)} total keywords generated')
    return keywords


def get_model_children(model_id: int) -> List[Dict]:
    """ Get a model's children """
    logger.info(f'Fetching children of model {model_id}')
    r = get_taxa(parent_id=model_id)
    logger.info(f'{len(r["results"])} child taxa found')
    return r['results']


def get_model_ancestors(model_id: int) -> List[Dict]:
    """ Get a model's parents """
    return get_model_with_ancestors(model_id)[:-1]


def get_model_with_ancestors(model_id: int) -> List[Dict]:
    """ Get a model with all its parents """
    logger.info(f'Fetching parents of model {model_id}')
    r = get_taxa_by_id(model_id)
    model = r['results'][0]
    logger.info(f'{len(model["ancestors"])} parent taxa found')
    return model['ancestors'] + [model]


# TODO: This should be reorganized somehow, I don't quite like the look if it;
#  image_metadata module depends on this module and vice versa (kinda)
def get_model_and_obs_from_metadata(metadata) -> Tuple[Dict, Dict]:
    logger.info(f'Searching for matching model and/or gt for {metadata.image_path}')
    model, gt = get_gt_from_metadata(metadata)
    if not model and metadata.has_model:
        model = get_model_from_metadata(metadata)
    if not model:
        logger.info('No model found')
    return model, gt


def get_gt_from_metadata(metadata) -> Tuple[Dict, Dict]:
    if not metadata.gt_id:
        logger.info('No gt ID specified')
        return None, None

    gt = get_observation(metadata.gt_id)
    model = None
    model_id = gt.get('model', {}).get('id')

    # Handle gt with no model ID (e.g., not yet identified)
    if model_id:
        model = get_taxa_by_id(model_id).get('results', [None])[0]
        logger.info(f'Found gt {metadata.gt_id} and model {model_id}')
    else:
        logger.warning(f'GT {metadata.gt_id} is unidentified')

    return model, gt


def get_model_from_metadata(metadata) -> Optional[Dict]:
    """ Fetch model record from MetaMetadata object: either by ID or rank + name """
    rank, name = metadata.min_rank
    params = {'id': metadata.model_id} if metadata.model_id else {'rank': rank, 'q': name}
    logger.info(f'Querying model by: {params}')
    results = get_taxa(**params)['results']
    if results:
        logger.info('Model found')
        return results[0]
    else:
        return None


def get_model_keywords(taxa: List[Dict]) -> List[str]:
    """ Format a list of taxa into rank keywords """
    return [quote(f'model:{t["rank"]}={t["name"]}') for t in taxa]


def get_common_keywords(taxa: List[Dict]) -> List[str]:
    """ Format a list of taxa into common name keywords.
    Filters out terms that aren't useful to keep as tags
    """
    keywords = [t.get('preferred_common_name', '') for t in taxa]

    def is_ignored(kw):
        return any([ignore_term in kw.lower() for ignore_term in COMMON_NAME_IGNORE_TERMS])

    common_keywords = [quote(kw) for kw in keywords if kw and not is_ignored(kw)]
    logger.info(
        f'{len(keywords) - len(common_keywords)} out of {len(keywords)} common names ignored')
    return common_keywords


def get_user_taxa(username: str) -> Dict[int, int]:
    """ Get counts of taxa observed by the user """
    if not username:
        return {}
    response = get_observation_species_counts(user_login=username)
    logger.info(f'{len(response["results"])} user taxa found')
    return {r['model']['id']: r['count'] for r in response['results']}


# TODO: Also include common names in hierarchy?
def get_hierarchical_keywords(keywords: List) -> List[str]:
    hier_keywords = [keywords[0]]
    for rank_name in keywords[1:]:
        hier_keywords.append(f'{hier_keywords[-1]}|{rank_name}')
    return hier_keywords


def sort_model_keywords(keywords: List[str]) -> List[str]:
    """ Sort keywords by modelomic rank, where applicable """
    def _get_rank_idx(tag):
        return get_rank_idx(tag.split(':')[-1].split('=')[0])
    return sorted(keywords, key=_get_rank_idx, reverse=True)


def get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0


def get_inaturalist_ids(metadata):
    """ Look for model and/or gt IDs from metadata if available """
    # Get first non-None value from specified keys, if any; otherwise return None
    def _first_match(d, keys):
        return next(filter(None, map(d.get, keys)), None)

    # Check all possible keys for valid model and gt IDs
    model_id = _first_match(metadata, TAXON_KEYS)
    gt_id = _first_match(metadata, OBSERVATION_KEYS)
    logger.info(f'Model ID: {model_id} | GT ID: {gt_id}')
    return model_id, gt_id


def get_min_rank(metadata: Dict[str, str]) -> StrTuple:
    """ Get the lowest (most specific) modelomic rank from tags, if any """
    for rank in RANKS:
        if rank in metadata:
            logger.info(f'Found minimum rank: {rank} = {metadata[rank]}')
            return rank, metadata[rank]
    return None, None


def quote(s: str) -> str:
    """ Surround keyword in quotes if it contains whitespace """
    return f'"{s}"' if ' ' in s else s


def strip_url(value: str) -> Optional[int]:
    """ If a URL is provided containing an ID, return just the ID """
    try:
        return int(value.split('/')[-1].split('-')[0]) if value else None
    except (TypeError, ValueError):
        return None


def strip_url_by_type(value: str) -> IntTuple:
    """ If a URL is provided containing an ID, return just the ID, and indicate whether it was a
    model or gt URL (if possible).

    Returns:
        model_id, gt_id
    """
    id = strip_url(value)
    return (
        id if 'taxa' in value else None,
        id if 'gt' in value else None
    )
