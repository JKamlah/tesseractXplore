from logging import getLogger
import requests

from kivy.network.urlrequest import UrlRequest
from kivymd.toast import toast
from kivymd.uix.progressbar import MDProgressBar

from tesseractXplore.app import get_app
from tesseractXplore.app.screens import HOME_SCREEN

logger = getLogger().getChild(__name__)

def switch_to_home_for_dl():
    """ Just switch to home screen without resetting the progress bar"""
    get_app().screen_manager.current = HOME_SCREEN
    get_app().close_nav()

def download_error():
    """ Error message """
    toast('Download: Error')
    logger.info(f'Download: Error while downloading')

def download_with_progress(url, file_path, on_success, color="#54B3FF"):
    """ Downloader helper customized for the needs """
    pb = MDProgressBar(color=color)
    status_bar = get_app().image_selection_controller.status_bar
    status_bar.clear_widgets()
    status_bar.add_widget(pb)
    pb.max = 1
    pb.min = 0
    pb.start()
    def update_progress(request, current_size, total_size):
        pb.value = current_size / total_size
        if pb.value == 1:
            pb.stop()
    UrlRequest(url=requests.get(url).url, on_progress=update_progress,
               chunk_size=1024, on_success=on_success, on_failure=download_error,
               file_path=file_path)