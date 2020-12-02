import asyncio
from collections import OrderedDict
from logging import getLogger

from kivy.clock import Clock

from tesseractXplore.app import get_app, alert
from tesseractXplore.controllers import Controller, ModelBatchLoader
from tesseractXplore.widgets import StarButton, ModelListItem

logger = getLogger().getChild(__name__)


# TODO: Better name for this? Maybe 'ModelQuickAccessController'?
class ModelSelectionController(Controller):
    """ Controller class to manage selecting stored taxa """
    def __init__(self, screen):
        super().__init__(screen)
        # Tab references
        #self.history_tab = screen.history_tab
        #self.frequent_tab = screen.frequent_tab
        #self.starred_tab = screen.starred_tab

        # Context menu
        self.context_menu = screen.context_menu
        self.context_menu.ids.move_to_top_ctx.bind(on_release=self.move_starred_to_top)

        # Various model lists
     #  self.model_history_ids = []
     #  self.model_history_map = {}
     #  self.model_history_list = screen.history_tab.ids.model_history_list
     #  self.frequent_taxa_ids = {}
     #  self.frequent_taxa_list = screen.frequent_tab.ids.frequent_taxa_list
     #  self.frequent_taxa_list.sort_key = self.get_frequent_model_idx
     #  self.user_taxa_ids = {}
     #  self.user_taxa_map = {}
     #  self.user_taxa_list = screen.user_tab.ids.user_taxa_list
     #  self.starred_taxa_ids = []
     #  self.starred_taxa_map = {}
     #  self.starred_taxa_list = screen.starred_tab.ids.starred_taxa_list

    def post_init(self):
        Clock.schedule_once(lambda *x: asyncio.run(self.init_stored_taxa()), 1)

    async def init_stored_taxa(self):
        """ Load model history, starred, and frequently viewed items """
        return
        logger.info('Loading stored taxa')
        stored_taxa = get_app().stored_taxa
        self.model_history_ids, self.starred_taxa_ids, self.frequent_taxa_ids = stored_taxa
        self.user_taxa_ids = self.get_user_taxa()

        # Collect all the model IDs we need to load
        starred_taxa_ids = self.starred_taxa_ids[::-1]
        total_taxa = sum(map(len, (
            self.starred_taxa_ids,
        )))

        # Start progress bar with a new batch loader
        loader = ModelBatchLoader()
        self.start_progress(total_taxa, loader)

        # Add the finishing touches after all items have loaded
        def index_list_items(*args):
            for item in self.model_history_list.children:
                self.model_history_map[item.model.id] = item
            for item in self.starred_taxa_list.children:
                self.bind_star(item)
        loader.bind(on_complete=index_list_items)

        # Start loading batches of ModelListItems
        logger.info(
            f'Model: Loading {len(unique_history)} unique taxa from history'
            f' (from {len(self.model_history_ids)} total)'
        )
        loader.add_batch(unique_history, parent=self.model_history_list)
        logger.info(f'Model: Loading {len(starred_taxa_ids)} starred taxa')
        loader.add_batch(starred_taxa_ids, parent=self.starred_taxa_list)
        logger.info(f'Model: Loading {len(top_frequent_ids)} frequently viewed taxa')
        loader.add_batch(top_frequent_ids, parent=self.frequent_taxa_list)
        logger.info(f'Model: Loading {len(top_user_ids)} user-observed taxa')
        loader.add_batch(top_user_ids, parent=self.user_taxa_list)

        loader.start_thread()

    def update_history(self, model_id: int):
        """ Update history + frequency """
        return
        self.model_history_ids.append(model_id)

        # If item already exists in history, move it from its previous position to the top
        if model_id in self.model_history_map:
            item = self.model_history_map[model_id]
            self.model_history_list.remove_widget(item)
        else:
            item = get_app().get_model_list_item(model_id)
            self.model_history_map[model_id] = item

        self.model_history_list.add_widget(item, len(self.model_history_list.children))
        self.add_frequent_model(model_id)

    def add_frequent_model(self, model_id: int):
        self.frequent_taxa_ids.setdefault(model_id, 0)
        self.frequent_taxa_ids[model_id] += 1
        self.frequent_taxa_list.sort()

    @staticmethod
    def get_user_taxa():
        username = get_app().username
        # TODO: Show this alert only when clicking on tab instead
        if not username:
            alert('Please enter iNaturalist username on Settings page')
            return {}
        return ""

    def add_star(self, model_id: int):
        """ Add a model to Starred list """
        logger.info(f'Adding model to starred: {model_id}')
        if model_id not in self.starred_taxa_ids:
            self.starred_taxa_ids.append(model_id)

        item = get_app().get_model_list_item(model_id, disable_button=True)
        self.starred_taxa_list.add_widget(item, len(self.starred_taxa_list.children))
        self.bind_star(item)

    def bind_star(self, item: ModelListItem):
        """ Bind click events on a starred model list item, including an X (remove) button """
        item.bind(on_touch_down=self.on_starred_model_click)
        remove_button = StarButton(item.model.id, icon='close')
        remove_button.bind(on_release=lambda x: self.remove_star(x.model_id))
        item.add_widget(remove_button)
        self.starred_taxa_map[item.model.id] = item

    # TODO: Also remove star from info section if this model happens to be currently selected
    def remove_star(self, model_id: int):
        """ Remove a model from Starred list """
        logger.info(f'Removing model from starred: {model_id}')
        if model_id in self.starred_taxa_map:
            item = self.starred_taxa_map.pop(model_id)
            self.starred_taxa_ids.remove(model_id)
            self.starred_taxa_list.remove_widget(item)

    def is_starred(self, model_id: int) -> bool:
        """ Check if the specified model is in the Starred list """
        return #model_id in self.starred_taxa_map

    def on_starred_model_click(self, instance, touch):
        """ Event handler for clicking a item from starred taxa list """
        if not instance.collide_point(*touch.pos):
            return
        # Right-click: Open context menu
        elif touch.button == 'right':
            self.context_menu.show(*get_app().root_window.mouse_pos)
            self.context_menu.ref = instance
            # self.context_menu.ids.view_model_ctx.disabled = not instance.metadata.model_id
        # Middle-click: remove item
        elif touch.button == 'middle':
            self.remove_star(instance.model.id)
        # Left-cliok: select model
        else:
            get_app().select_model(instance.model)

    def move_starred_to_top(self, instance):
        """ Move a starred model to the top of the list, both in the UI and in persisted list """
        lst = self.starred_taxa_ids
        lst.append(lst.pop(lst.index(instance.model_id)))
        item = self.starred_taxa_map[instance.model_id]
        self.starred_taxa_list.remove_widget(item)
        self.starred_taxa_list.add_widget(item, len(self.starred_taxa_list.children))

    def get_frequent_model_idx(self, list_item) -> int:
        """ Get sort index for frequently viewed taxa (by number of views, descending) """
        num_views = self.frequent_taxa_ids.get(list_item.model.id, 0)
        return num_views * -1  # Effectively the same as reverse=True
