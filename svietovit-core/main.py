from kivy.app import App
from kivy.uix.label import Label


class Hello(App):
    def build(self):
        return Label(text="Działa! Śviętovit Hello", font_size="28sp")


Hello().run()
