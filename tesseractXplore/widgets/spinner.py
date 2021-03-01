from kivy.uix.spinner import Spinner, SpinnerOption
from tesseractXplore.font import chk_font_renderabilty

class FntSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # TODO: Find a method to check if a font can get rendered before crash
            if chk_font_renderabilty(self.text):
                self.font_name= self.text if self.text else self.font_name
            else:
                self.text = "Font is renderable"
                pass
        except Exception as e:
            pass
    pass

class FntSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = self.text if self.text else self.font_name
        self.option_cls = FntSpinnerOption

