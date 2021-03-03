from logging import getLogger

from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller, ModelBatchLoader
from tesseractXplore.metamodels import read_metamodels

logger = getLogger().getChild(__name__)


class ModelSearchController(Controller):
    """ Controller class to manage model search """

    def __init__(self, screen):
        super().__init__(screen)
        self.screen = screen
        self.metamodels = read_metamodels()
        self.selected_model = None

        self.search_tab = screen.search_tab
        #        self.search_results_tab = screen.search_results_tab

        # Search inputs
        self.model_tagfilter_input = screen.search_tab.ids.model_tagfilter_input
        self.model_tagfilter_input.bind(on_text_validate=self.on_tagfilter)
        self.model_search_input = screen.search_tab.ids.model_search_input
        self.model_search_input.bind(on_selection=self.on_selection)
        self.modelgroup_input = screen.search_tab.ids.modelgroup_input
        self.fastmodel_chk = screen.search_tab.ids.fastmodel_chk
        self.bestmodel_chk = screen.search_tab.ids.bestmodel_chk
        self.languagemodel_chk = screen.search_tab.ids.languagemodel_chk
        self.scriptmodel_chk = screen.search_tab.ids.scriptmodel_chk

        # Buttons
        self.model_search_button = screen.search_tab.ids.model_search_button
        self.model_search_button.bind(on_release=self.apply_filter)
        self.reset_search_button = screen.search_tab.ids.reset_search_button
        self.reset_search_button.bind(on_release=self.reset_all_search_inputs)

        # Search results
        # self.search_results_list = self.search_results_tab.ids.search_results_list

    def get_model_autocomplete(self, search_str):
        res = []
        for modelgroup, modelgroupval in self.metamodels.items():
            if self.modelgroup_input.text == "" or self.modelgroup_input.text.lower() in modelgroup.lower():
                for modelname in modelgroupval.get('models', []):
                    modelval = modelgroupval['models'][modelname]
                    if search_str.lower() in modelname.lower() or any(
                            [1 if search_str.lower() in tag.lower() else 0 for tag in modelval.get("tags", [])]):
                        if (self.bestmodel_chk.active and "best" in modelval["type"]) or (
                                self.fastmodel_chk.active and "fast" in modelval["type"]):
                            if (self.languagemodel_chk.active and "Language" in modelval["category"]) or (
                                    self.scriptmodel_chk.active and "Script" in modelval["category"]):
                                res.append({"modelgroup": modelgroup,
                                            "name": modelname,
                                            "url": modelgroupval['types'],
                                            "id": "Group:" + modelgroup + "Model:" + modelname,
                                            "model": modelval})
        return res

    def apply_filter(self, *args):
        text = self.model_search_input.text_input.text
        self.model_search_input.text_input.text = ''
        self.model_search_input.dropdown_view.data = []
        self.model_search_input.text_input.text = text

    def search(self, *args):
        """ Run a search with the currently selected search parameters """
        # asyncio.run(self._search())

    # TODO: Paginated results
    async def _search(self):
        # TODO: To make async HTTP requests, Pick one of: grequests, aiohttp, twisted, tornado...
        # async def _get_taxa(params):
        #     return get_taxa(**params)['results']

        params = self.get_search_parameters()
        logger.info(f'Searching taxa with parameters: {params}')
        results = self.get_models(**params)
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

    def get_models(self, **params):
        return

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
        self.model_tagfilter_input.text = ""
        self.scriptmodel_chk.active = True
        self.languagemodel_chk.active = True
        self.bestmodel_chk.active = True
        self.fastmodel_chk.active = True

    @staticmethod
    def on_select_model(button):
        """ Handle clicking an iconic model; don't re-select the model if we're de-selecting it """
        if not button.is_selected:  # Note: this is the state *after* the click event
            get_app().select_model(id=button.model_id)

    @staticmethod
    def on_selection(instance, metadata: dict):
        """ Handle clicking a model search result from the autocomplete dropdown """
        get_app().model_search_controller.model_search_input.text_input.text = metadata['name']
        get_app().select_model(model_dict=metadata)

    @staticmethod
    def on_tagfilter(text_input):
        """ Handle entering a model ID and pressing Enter """
        pass
        # get_app().select_model(id=int(text_input.text))
