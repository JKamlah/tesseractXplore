from tesseractXplore.app import get_app
from tesseractXplore.controllers import BatchLoader
from tesseractXplore.widgets import LoaderProgressBar


class Controller:
    """ Base class for screen controllers """

    def __init__(self, screen):
        self.progress_bar = LoaderProgressBar(color=get_app().theme_cls.primary_color)
        self.status_bar = screen.status_bar
        self.loader = None

    def start_progress(self, max: int, loader: BatchLoader = None):
        """ (Re)start the progress bar, and bind a BatchLoader's progress update events to it """
        self.progress_bar.start(max, loader)
        self.status_bar.clear_widgets()
        self.status_bar.add_widget(self.progress_bar)
