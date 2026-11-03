"""WERSJA DIAGNOSTYCZNA Śviętovita (do wklejenia w miejsce main.py na czas szukania awarii).
Pokazuje na ekranie kolejne etapy startu. Ostatnia linia „>> TERAZ” wskazuje etap, na którym aplikacja się zamyka."""
import os
import sys
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform

LOG = []
M = None


def st_info(app):
    return "platforma=%s okno=%s dp=%.2f" % (platform, Window.size, dp(1))


def st_import(app):
    global M
    import svietovit_app as mod
    M = mod
    return "kursów=%d" % len(M.COURSES)


def st_hubfont(app):
    M.use_hub_fonts()
    lbl = Label(text="ꙮ Ąę Śviętovit", font_size=sp(20))
    lbl.texture_update()
    return "tekstura=%s" % (lbl.texture_size,)


def course_stage(info):
    def fn(app):
        name = "T_" + info["id"]
        LabelBase.register(name=name, fn_regular=info["native_font"])
        lbl = Label(text=info["native"] + " " + info["glyph"], font_name=name, font_size=sp(22))
        lbl.texture_update()
        return "tekstura=%s" % (lbl.texture_size,)
    return fn


def roboto_stage(info):
    def fn(app):
        reg, bold = info["roboto"]
        LabelBase.register(name="Roboto", fn_regular=reg, fn_bold=bold)
        lbl = Label(text="Ąę ćł 字 あ 한 Ж", font_size=sp(18))
        lbl.texture_update()
        lb = Label(text="Ąę ćł", font_size=sp(18), bold=True)
        lb.texture_update()
        return "ok"
    return fn


def st_build(app):
    real = M.SvietovitApp()
    root = real.build()
    app.root_widget_test = root
    return "build() zwrócił %s" % type(root).__name__


class Diag(App):
    title = "Śviętovit diag"

    def build(self):
        Window.clearcolor = (0.09, 0.09, 0.11, 1)
        box = BoxLayout(orientation="vertical", padding=dp(8))
        self.lbl = Label(text="start", font_size=sp(12), halign="left", valign="top", color=(0.93, 0.9, 0.83, 1))
        self.lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], v[1])))
        box.add_widget(self.lbl)
        self.stages = [("informacje o systemie", st_info), ("import svietovit_app", st_import),
                       ("czcionka ekranu głównego", st_hubfont)]
        self.i = 0
        return box

    def on_start(self):
        Clock.schedule_once(self.setup_rest, 0.5)

    def setup_rest(self, dt):
        self.next(0)

    def show(self, running=None):
        text = "DIAGNOSTYKA ŚVIĘTOVITA\n" + "\n".join(LOG)
        if running:
            text += "\n>> TERAZ: " + running
        self.lbl.text = text

    def next(self, dt):
        if self.i == len(self.stages) and M is not None and not getattr(self, "extended", False):
            self.extended = True
            for info in M.COURSES:
                self.stages.append(("czcionka kursu " + info["id"], course_stage(info)))
            for info in M.COURSES:
                self.stages.append(("krój podstawowy " + info["id"], roboto_stage(info)))
            self.stages.append(("budowa ekranu głównego (build)", st_build))
        if self.i >= len(self.stages):
            LOG.append("KONIEC: wszystko przeszło")
            self.show()
            return
        name, fn = self.stages[self.i]
        self.show(name)
        Clock.schedule_once(lambda d: self.run_stage(name, fn), 0.7)

    def run_stage(self, name, fn):
        try:
            res = fn(self)
            LOG.append("OK    %s %s" % (name, res or ""))
        except Exception:
            LOG.append("BŁĄD  %s\n%s" % (name, traceback.format_exc()[-500:]))
        self.i += 1
        self.show()
        Clock.schedule_once(self.next, 0.5)


if __name__ == "__main__":
    Diag().run()
