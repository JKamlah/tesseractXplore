import threading

from kivymd.uix.card import MDSeparator
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivy.uix.boxlayout import BoxLayout

from tesseractXplore.widgets.process_manager import ProcessManagerItem
from tesseractXplore.app import get_app

def processmanager(processname:str):
    """ Displaying active background process to the user"""
    pm = ProcessManagerItem()
    boxlayout = BoxLayout(orientation="vertical")
    main_label = MDLabel(
        text="Process running",
        theme_text_color= "Custom",
        text_color= (1, 1, 1, 1),
        size_hint_y= None,
        adaptive_height= True,
        )
    boxlayout.add_widget(main_label)
    sep = MDSeparator(height= "1dp", color='cyan')
    boxlayout.add_widget(sep)
    process_label = MDLabel(text= processname,
                            theme_text_color= "Custom",
                            text_color= (1, 1, 1, 1),)
    boxlayout.add_widget(process_label)
    boxlayout2 = BoxLayout(orientation= "vertical")
    pb = MDProgressBar(type= "determinate", running_duration= 1, catching_duration= 1.5)
    boxlayout2.add_widget(pb)
    pb.start()
    boxlayout.add_widget(boxlayout2)
    pm.add_widget(boxlayout)
    return pm

def create_threadprocess(processname:str,func, *args, **kwargs):
    new_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    new_thread.setDaemon(True)
    new_thread.start()
    pm = processmanager(processname)
    get_app().active_threads[new_thread] = pm
    get_app().image_selection_controller.screen.process_list.add_widget(pm)

def create_online_threadprocess(processname:str,func, *args, **kwargs):
    new_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    new_thread.setDaemon(True)
    new_thread.start()
    pm = processmanager(processname)
    get_app().active_threads[new_thread] = pm
    get_app().image_selection_online_controller.screen.process_list.add_widget(pm)