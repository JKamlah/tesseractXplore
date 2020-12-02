#from tesseractXplore.controllers.model_search_controller import get_model_autocomplete
from tesseractXplore.widgets import AutocompleteSearch
from tesseractXplore.app import get_app


class ModelAutocompleteSearch(AutocompleteSearch):
    """ Autocomplete search for iNaturalist taxa """
    async def get_autocomplete(self, search_str):
        """ Get taxa autocomplete search results, as display text + other metadata """
        async def _get_model_autocomplete():
            return get_app().model_search_controller.get_model_autocomplete(search_str)

        def get_dropdown_info(model):
            display_text = f'{model["name"]} ({model["modelgroup"]})'
            return {'text': display_text, 'suggestion_text': "", 'metadata': model}

        models = await(_get_model_autocomplete())
        return [get_dropdown_info(model) for model in models]


