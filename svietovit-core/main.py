"""Punkt wejścia Śviętovita. Właściwa aplikacja jest w svietovit_app.py; ten plik tylko ją ładuje
i, gdy ładowanie się nie uda (np. brakuje pliku), pokazuje błąd na ekranie zamiast cicho się zamykać."""
import os
import sys
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_TB = None
try:
    import svietovit_app as _impl
    globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})
except Exception:
    _impl = None
    _TB = traceback.format_exc()


def _run_crash_app(tb):
    from kivy.app import App
    from kivy.metrics import dp, sp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class CrashApp(App):
        title = "Śviętovit"

        def build(self):
            try:
                with open(os.path.join(self.user_data_dir, "crash.log"), "a", encoding="utf-8") as fh:
                    fh.write(tb + "\n")
            except Exception:
                pass
            box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
            box.add_widget(Label(text="Śviętovit: błąd przy uruchomieniu. Zrób zrzut ekranu i wyślij.",
                                 size_hint_y=None, height=dp(48), color=(1, 0.8, 0.5, 1), font_size=sp(15)))
            sv = ScrollView()
            lbl = Label(text=tb[-3500:], font_size=sp(10), size_hint_y=None, halign="left", valign="top")
            lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
            lbl.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
            sv.add_widget(lbl)
            box.add_widget(sv)
            return box

    CrashApp().run()


if __name__ == "__main__":
    if _impl is None:
        _run_crash_app(_TB)
    else:
        _impl.SvietovitApp().run()
