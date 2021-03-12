from kivymd.uix.card import MDCard

class ProcessManagerItem(MDCard):
    """ Displaying active background process to the user"""
    def __init__(self, **kwargs):
        self.orientation = 'vertical'
        self.size_hint = None, None
        self.size = 300, 50
        self.md_bg_color= (.1, .1, .1, .1)
        super().__init__(**kwargs)

