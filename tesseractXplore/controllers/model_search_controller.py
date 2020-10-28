import asyncio
from logging import getLogger

from pyinaturalist.node_api import get_taxa
from tesseractXplore.constants import ICONIC_TAXA
from tesseractXplore.controllers import Controller, ModelBatchLoader
from tesseractXplore.models import Model
from tesseractXplore.app import get_app
from tesseractXplore.widgets import DropdownTextField, IconicTaxaIcon

logger = getLogger().getChild(__name__)


class ModelSearchController(Controller):
    """ Controller class to manage model search """
    def __init__(self, screen):
        super().__init__(screen)
        self.search_tab = screen.search_tab
        self.search_results_tab = screen.search_results_tab

        # Search inputs
        self.model_id_input = screen.search_tab.ids.model_id_input
        self.model_id_input.bind(on_text_validate=self.on_model_id)
        self.model_search_input = screen.search_tab.ids.model_search_input
        self.model_search_input.bind(on_selection=self.on_selection)
        self.exact_rank_input = screen.search_tab.ids.exact_rank_input
        self.min_rank_input = screen.search_tab.ids.min_rank_input
        self.max_rank_input = screen.search_tab.ids.max_rank_input
        self.iconic_taxa_filters = screen.search_tab.ids.iconic_taxa

        # 'Categories' (iconic taxa) icons
        for id in ICONIC_TAXA:
            icon = IconicTaxaIcon(id)
            icon.bind(on_release=self.on_select_iconic_model)
            self.iconic_taxa_filters.add_widget(icon)

        # Search inputs with dropdowns
        self.rank_menus = (
            DropdownTextField(text_input=self.exact_rank_input, text_items=[]),
            DropdownTextField(text_input=self.min_rank_input, text_items=[]),
            DropdownTextField(text_input=self.max_rank_input, text_items=[]),
        )

        # Buttons
        self.model_search_button = screen.search_tab.ids.model_search_button
        self.model_search_button.bind(on_release=self.search)
        self.reset_search_button = screen.search_tab.ids.reset_search_button
        self.reset_search_button.bind(on_release=self.reset_all_search_inputs)

        # Search results
        self.search_results_list = self.search_results_tab.ids.search_results_list

    @property
    def selected_iconic_taxa(self):
        return [t for t in self.iconic_taxa_filters.children if t.is_selected]

    def search(self, *args):
        """ Run a search with the currently selected search parameters """
        asyncio.run(self._search())

    # TODO: Paginated results
    async def _search(self):
        # TODO: To make async HTTP requests, Pick one of: grequests, aiohttp, twisted, tornado...
        # async def _get_taxa(params):
        #     return get_taxa(**params)['results']

        params = self.get_search_parameters()
        logger.info(f'Searching taxa with parameters: {params}')
        # results = await _get_taxa(params)
        results = get_taxa(**params)['results']
        logger.info(f'Found {len(results)} search results')
        await self.update_search_results(results)

    def get_search_parameters(self):
        """ Get API-compatible search parameters from the input widgets """
        params = {
            'q': self.model_search_input.text_input.text.strip(),
            'model_id': [t.model_id for t in self.selected_iconic_taxa],
            'rank': self.exact_rank_input.text.strip(),
            'min_rank': self.min_rank_input.text.strip(),
            'max_rank': self.max_rank_input.text.strip(),
            'per_page': 30,
            'locale': get_app().locale,
            'preferred_place_id': get_app().preferred_place_id,
        }
        return {k: v for k, v in params.items() if v}

    async def update_search_results(self, results):
        """ Add model info from response to search results tab """
        loader = ModelBatchLoader()
        self.start_progress(len(results), loader)
        self.search_results_list.clear_widgets()

        logger.info(f'Model: loading {len(results)} search results')
        loader.add_batch(results, parent=self.search_results_list)
        self.search_results_tab.select()

        loader.start_thread()

    def reset_all_search_inputs(self, *args):
        logger.info('Resetting search filters')
        self.model_search_input.reset()
        for t in self.selected_iconic_taxa:
            t.toggle_selection()
        self.exact_rank_input.text = ''
        self.min_rank_input.text = ''
        self.max_rank_input.text = ''

    @staticmethod
    def on_select_iconic_model(button):
        """ Handle clicking an iconic model; don't re-select the model if we're de-selecting it """
        if not button.is_selected:  # Note: this is the state *after* the click event
            get_app().select_model(id=button.model_id)

    @staticmethod
    def on_selection(instance, metadata: dict):
        """ Handle clicking a model search result from the autocomplete dropdown """
        get_app().select_model(model_dict=metadata)

    @staticmethod
    def on_model_id(text_input):
        """ Handle entering a model ID and pressing Enter """
        get_app().select_model(id=int(text_input.text))
