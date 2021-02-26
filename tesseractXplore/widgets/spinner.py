from kivy.uix.spinner import Spinner, SpinnerOption

class FntSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name= self.text if self.text else self.font_name
    pass

class FntSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = self.text if self.text else self.font_name
        self.option_cls = FntSpinnerOption

