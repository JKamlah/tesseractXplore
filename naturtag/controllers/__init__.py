"""
Package for controller classes. The goal is to organize these such that each controller manages
the components & state from a single .kv file.
"""
from naturtag.controllers.image_selection_controller import ImageSelectionController
from naturtag.controllers.metadata_view_controller import MetadataViewController
from naturtag.controllers.observation_search_controller import ObservationSearchController
from naturtag.controllers.settings_controller import SettingsController
from naturtag.controllers.taxon_search_controller import TaxonSearchController
from naturtag.controllers.taxon_selection_controller import TaxonSelectionController
from naturtag.controllers.taxon_view_controller import TaxonViewController
