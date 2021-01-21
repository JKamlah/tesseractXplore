from typing import Dict

import attr

kwarg = attr.ib(default=None)


# TODO
@attr.s
class GT:
    id: int = kwarg

    @classmethod
    def from_id(cls, id: int):
        """ Lookup and create a new GT object from an ID """
        return {}

    @classmethod
    def from_dict(cls, json: Dict, partial: bool = False):
        """ Create a new GT object from an API response """
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        attr_names = attr.fields_dict(cls).keys()
        valid_json = {k: v for k, v in json.items() if k in attr_names and v is not None}
        return cls(partial=partial, **valid_json)
