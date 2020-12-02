import attr
from typing import List, Dict, Optional

from tesseractXplore.constants import ATLAS_APP_ICONS, CC_LICENSES

kwarg = attr.ib(default=None)


@attr.s
class Model:
    """ A data class containing information about a model, matching the schema of ``GET /taxa``
    from the iNaturalist API: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    Examples of partial records include nested ``ancestors``, ``children``, and results from
    :py:func:`get_taxa_autocomplete`
    """
    id: int = kwarg
    name: str = kwarg
    gts_count: int = kwarg
    partial: bool = kwarg
    modelgroup: str = kwarg
    url: Dict = attr.ib(factory=dict)
    model: Dict = attr.ib(factory=dict)

    # Nested collections with defaults
    ancestor_ids: List[int] = attr.ib(factory=list)
    ancestors: List[Dict] = attr.ib(factory=list)
    default_photo: Dict = attr.ib(factory=dict)

    @classmethod
    def from_dict(cls, json: Dict, partial: bool = False):
        """ Create a new Model object from all or part of an API response """
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(partial=partial, **valid_json)

    @property
    def ancestry_str(self):
        return ' | '.join(t.name for t in [])

    @property
    def icon_path(self) -> str:
        return get_icon_path(1)

def get_icon_path(id: int) -> Optional[str]:
    """ An iconic function to return an icon for an iconic model """
    return f'{ATLAS_APP_ICONS}'
