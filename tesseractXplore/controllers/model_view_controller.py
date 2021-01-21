import asyncio
from logging import getLogger
from pathlib import Path
from typing import List

import requests
from kivymd.uix.list import OneLineListItem

from tesseractXplore.app import get_app
from tesseractXplore.controllers import Controller, ModelBatchLoader
from tesseractXplore.models import Model

logger = getLogger().getChild(__name__)


class ModelViewController(Controller):
    """ Controller class to manage displaying info about a selected model """

    def __init__(self, screen):
        super().__init__(screen)

        self.screen = screen
        # Controls
        # self.model_link = screen.model_links.ids.selected_model_link_button
        self.download_button = screen.model_links.ids.download_button
        self.download_button.bind(on_release=lambda x: self.download_model())

        # Outputs
        self.selected_model = None
        # self.model_photo = screen.selected_model_photo
        # self.model_ancestors_label = screen.model_section.ids.model_ancestors_label
        # self.model_children_label = screen.model_section.ids.model_children_label
        # self.model_ancestors = screen.model_section.ids.model_ancestors
        # self.model_children = screen.model_section.ids.model_children

    def download_model(self, model_obj: Model = None, model_dict: dict = None, id: int = None, if_empty: bool = False):
        if self.screen.best_toggle.state == 'down':
            url = self.selected_model.url['best']['url']
        else:
            url = self.selected_model.url['fast']['url']
        url += self.selected_model.model['name']
        outputpath = Path(self.screen.tessdatadir.text).joinpath(self.screen.filename.text).absolute()
        logger.info(f'Download: {url} -> {str(outputpath)}')
        try:
            r = requests.get(url)
            if not outputpath.parent.exists():
                outputpath.parent.mkdir(parents=True)
            with open(outputpath, 'wb') as f:
                f.write(r.content)
            logger.info(f'Download: Succesful')
            # Update Modelslist
            get_app().tesseract_controller.models = get_app().tesseract_controller.get_models()
        except:
            logger.info(f'Download: Error while downloading')

    def select_model(self, model_obj: Model = None, model_dict: dict = None, id: int = None, if_empty: bool = False):
        """ Update model info display by either object, ID, partial record, or complete record """
        # Initialize from object, dict, or ID
        if if_empty and self.selected_model is not None:
            return
        if not any([model_obj, model_dict, id]):
            return
        if not model_obj:
            model_obj = Model.from_dict(model_dict) if model_dict else Model.from_id(int(id))
        # Don't need to do anything if this model is already selected
        if self.selected_model is not None and model_obj.id == self.selected_model.id:
            return

        logger.info(f'Model: Selecting model {model_obj.id}')
        # self.screen.basic_info.clear_widgets()
        self.selected_model = model_obj
        asyncio.run(self.load_model_info())

        # Add to model history, and update model id on image selector screen
        get_app().update_history(self.selected_model.id)
        get_app().select_model_from_photo(self.selected_model.id)

    async def load_model_info(self):
        await asyncio.gather(
            self.load_photo_section(),
            self.load_basic_info_section(),
            self.load_model(),
        )

    async def load_photo_section(self):
        """ Load model photo + links """
        logger.info('Model: Loading photo section')
        # if self.selected_model.photo_url:
        #    self.model_photo.source = self.selected_model.photo_url

        # Configure link to iNaturalist page
        # self.model_link.bind(on_release=lambda *x: webbrowser.open(self.selected_model.link))
        # self.model_link.tooltip_text = self.selected_model.link
        # self.model_link.disabled = False

        # Configure 'View parent' button
        # if self.selected_model.parent:
        #    self.model_parent_button.disabled = False
        #    self.model_parent_button.model = self.selected_model
        #    self.model_parent_button.tooltip_text = f'Go to {self.selected_model.parent.name}'
        # else:
        #    self.model_parent_button.disabled = True
        #    self.model_parent_button.tooltip_text = ''

    async def load_basic_info_section(self):
        """ Load basic info for the currently selected model """
        # Name, rank
        logger.info('Model: Loading basic info section')
        # Icon (if available)

        # TODO: Can we apply an icon for the categories?
        # icon_path = None #get_icon_path(self.selected_model.scrip)
        # if icon_path:
        #    item.add_widget(ImageLeftWidget(source=icon_path))
        self.screen.basic_info.text = self.selected_model.name
        self.screen.basic_info.secondary_text = self.selected_model.modelgroup

        self.download_button.disabled = False

        self.screen.info_description.secondary_text = self.selected_model.model['description']
        self.screen.info_tags.clear_widgets()
        for tag in self.selected_model.model['tags']:
            self.screen.info_tags.add_widget(OneLineListItem(text=tag,
                                                             font_style='Subtitle2', text_color="FFFFFF"))
        self.screen.info_category.secondary_text = self.selected_model.model['category']
        self.screen.filename.text = self.selected_model.model['name']

        # Star Button
        # star_icon = StarButton(
        #    1,
        #    is_selected=get_app().is_starred(1),
        # )
        # star_icon.bind(on_release=self.on_star)
        # item.add_widget(star_icon)

        # Other attrs

    #    for k in ['name']:
    #        label = k.title().replace('_', ' ')
    #        value = getattr(self.selected_model, k)
    #        item = OneLineListItem(text=f'id: {value}')
    #        self.basic_info.add_widget(item)

    async def load_model(self):
        """ Populate ancestors and children for the currently selected model """
        return
        total_taxa = len(self.selected_model.parent_taxa) + len(self.selected_model.child_taxa)

        # Set up batch loader + event bindings
        if self.loader:
            self.loader.cancel()
        self.loader = ModelBatchLoader()
        self.start_progress(total_taxa, self.loader)

        # Start loading ancestors
        # logger.info(f'Model: Loading {len(self.selected_model.parent_taxa)} ancestors')
        # self.model_ancestors_label.text = _get_label('Ancestors', self.selected_model.parent_taxa)
        # self.model_ancestors.clear_widgets()
        # self.loader.add_batch(self.selected_model.parent_taxa_ids, parent=self.model_ancestors)

        # logger.info(f'Model: Loading {len(self.selected_model.child_taxa)} children')
        # self.model_children_label.text = _get_label('Children', self.selected_model.child_taxa)
        # self.model_children.clear_widgets()
        # self.loader.add_batch(self.selected_model.child_taxa_ids, parent=self.model_children)

        self.loader.start_thread()

    def on_star(self, button):
        """ Either add or remove a model from the starred list """
        if button.is_selected:
            get_app().add_star(self.selected_model.id)
        else:
            get_app().remove_star(self.selected_model.id)


def _get_label(text: str, items: List) -> str:
    return text + (f' ({len(items)})' if items else '')
