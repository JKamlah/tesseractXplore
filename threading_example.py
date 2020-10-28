import threading
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.uix.gridlayout import GridLayout


Builder.load_string("""
<AnimWidget@Widget>:
    canvas:
        Color:
            rgba: 0.7, 0.3, 0.9, 1
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint: None, None
    size: 400, 30


<RootWidget>:
    cols: 1

    canvas:
        Color:
            rgba: 0.9, 0.9, 0.9, 1
        Rectangle:
            pos: self.pos
            size: self.size

    anim_box: anim_box
    but_1: but_1
    lab_1: lab_1
    lab_2: lab_2

    Button:
        id: but_1
        font_size: 20
        text: 'Start second thread'
        on_press: root.start_second_thread(lab_2.text)

    Label:
        id: lab_1
        font_size: 30
        color: 0.6, 0.6, 0.6, 1
        text_size: self.width, None
        halign: 'center'

    AnchorLayout:
        id: anim_box

    Label:
        id: lab_2
        font_size: 100
        color: 0.8, 0, 0, 1
        text: '3'
""")


class RootWidget(GridLayout):

    stop = threading.Event()

    def start_second_thread(self, l_text):
        threading.Thread(target=self.second_thread, args=(l_text,)).start()

    def second_thread(self, label_text):
        # Remove a widget, update a widget property, create a new widget,
        # add it and animate it in the main thread by scheduling a function
        # call with Clock.
        Clock.schedule_once(self.start_test, 0)

        # Do some thread blocking operations.
        time.sleep(5)
        l_text = str(int(label_text) * 3000)

        # Update a widget property in the main thread by decorating the
        # called function with @mainthread.
        self.update_label_text(l_text)

        # Do some more blocking operations.
        time.sleep(2)

        # Remove some widgets and update some properties in the main thread
        # by decorating the called function with @mainthread.
        self.stop_test()

        # Start a new thread with an infinite loop and stop the current one.
        threading.Thread(target=self.infinite_loop).start()

    def start_test(self, *args):
        # Remove the button.
        self.remove_widget(self.but_1)

        # Update a widget property.
        self.lab_1.text = ('The UI remains responsive while the '
                           'second thread is running.')

        # Create and add a new widget.
        anim_bar = Factory.AnimWidget()
        self.anim_box.add_widget(anim_bar)

        # Animate the added widget.
        anim = Animation(opacity=0.3, width=100, duration=0.6)
        anim += Animation(opacity=1, width=400, duration=0.8)
        anim.repeat = True
        anim.start(anim_bar)

    @mainthread
    def update_label_text(self, new_text):
        self.lab_2.text = new_text

    @mainthread
    def stop_test(self):
        self.lab_1.text = ('Second thread exited, a new thread has started. '
                           'Close the app to exit the new thread and stop '
                           'the main process.')

        self.lab_2.text = str(int(self.lab_2.text) + 1)

        self.remove_widget(self.anim_box)

    def infinite_loop(self):
        iteration = 0
        while True:
            if self.stop.is_set():
                # Stop running this thread so the main Python process can exit.
                return
            iteration += 1
            print('Infinite loop, iteration {}.'.format(iteration))
            time.sleep(1)


class ThreadedApp(App):

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()

    def build(self):
        return RootWidget()

if __name__ == '__main__':
    ThreadedApp().run()