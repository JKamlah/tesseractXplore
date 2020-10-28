from pyinaturalist.node_api import get_taxa_autocomplete
from tesseractXplore.widgets import AutocompleteSearch


class ModelAutocompleteSearch(AutocompleteSearch):
    """ Autocomplete search for iNaturalist taxa """
    async def get_autocomplete(self, search_str):
        """ Get taxa autocomplete search results, as display text + other metadata """
        async def _get_taxa_autocomplete():
            return get_taxa_autocomplete(q=search_str).get('results', [])

        def get_dropdown_info(model):
            common_name = f' ({model["preferred_common_name"]})' if 'preferred_common_name' in model else ''
            display_text = f'{model["rank"].title()}: {model["name"]}{common_name}'
            return {'text': display_text, 'suggestion_text': model['matched_term'], 'metadata': model}

        results = await(_get_taxa_autocomplete())
        return [get_dropdown_info(model) for model in results]

