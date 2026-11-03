"""Elementy wspólne dla wszystkich kursów Śviętovita."""
import math
import os
import random

from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
SVIET_REG = os.path.join(FONTS, "Sviet-Regular.ttf")
SVIET_BOLD = os.path.join(FONTS, "Sviet-Bold.ttf")
LabelBase.register(name="Sviet", fn_regular=SVIET_REG, fn_bold=SVIET_BOLD)

OKO = "ꙮ"  # ꙮ — wieloki O, znak Śviętovita

# Siedem oczu ꙮ: dwa u góry, trzy w środku, dwa na dole (w jednostkach szerokości oka).
_EYES = [(-0.5, 1.04), (0.5, 1.04), (-1.0, 0.0), (0.0, 0.0), (1.0, 0.0), (-0.5, -1.04), (0.5, -1.04)]
_EYE_W, _EYE_H = 1.0, 1.26


class Oko(Widget):
    """Znak ꙮ rysowany wektorowo; każde z siedmiu oczu mruga w losowych chwilach.

    Czasem mrugnie jedno oko, czasem kilka, a od czasu do czasu wszystkie naraz.
    """
    color = ListProperty([0.79, 0.64, 0.29, 1])

    def __init__(self, calm=1.0, **kw):
        super().__init__(**kw)
        self.calm = calm            # większe = rzadziej mruga
        self.lids = [0.0] * 7       # 0 = otwarte, 1 = zamknięte
        self._phase = [None] * 7    # czas od początku mrugnięcia (albo ujemne opóźnienie)
        self._dur = [0.2] * 7
        self._tick_ev = None
        self.bind(pos=self._draw, size=self._draw, center=self._draw, color=self._draw)
        Clock.schedule_once(lambda dt: self._schedule(), random.uniform(0.3, 1.5))

    # -- losowe mruganie -----------------------------------------------------
    def _schedule(self):
        Clock.schedule_once(self._blink, random.uniform(0.5, 3.2) * self.calm)

    def _blink(self, dt):
        if self.get_root_window() is not None:
            r = random.random()
            if r < 0.55:
                eyes = [random.randrange(7)]
            elif r < 0.8:
                eyes = random.sample(range(7), random.randint(2, 3))
            elif r < 0.92:
                eyes = list(range(7))
                random.shuffle(eyes)
            else:
                eyes = list(range(7))
            stagger = 0.0 if r >= 0.92 else 0.07
            for k, i in enumerate(eyes):
                if self._phase[i] is None:
                    self._phase[i] = -k * stagger * random.uniform(0.6, 1.4)
                    self._dur[i] = random.uniform(0.16, 0.26)
            if self._tick_ev is None:
                self._tick_ev = Clock.schedule_interval(self._tick, 1 / 45.0)
        self._schedule()

    def _tick(self, dt):
        busy = False
        for i in range(7):
            p = self._phase[i]
            if p is None:
                continue
            p += dt
            if p >= self._dur[i]:
                self._phase[i], self.lids[i] = None, 0.0
                continue
            busy = True
            self._phase[i] = p
            self.lids[i] = math.sin(math.pi * max(0.0, p) / self._dur[i])
        self._draw()
        if not busy:
            self._tick_ev.cancel()
            self._tick_ev = None

    # -- rysowanie -----------------------------------------------------------
    def _draw(self, *_):
        u = min(self.width / 3.15, self.height / 3.5)
        if u <= 0:
            return
        cx, cy = self.center
        stroke = max(1.0, u * 0.11)
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            for (ex, ey), lid in zip(_EYES, self.lids):
                w = _EYE_W * u
                h = _EYE_H * u * (1 - 0.8 * lid)
                x, y = cx + ex * u, cy + ey * u
                # Powieka się zamyka: oko spłaszcza się w cienką soczewkę, a obwódka chudnie.
                Line(ellipse=(x - w / 2, y - h / 2, w, h), width=max(1.0, min(stroke, h * 0.22)))
                if lid < 0.6:
                    pr = 0.15 * u
                    ph = 2 * pr * (1 - lid / 0.6)
                    Ellipse(pos=(x - pr, y - ph / 2), size=(2 * pr, ph))


class HubButton(ButtonBehavior, Widget):
    """Mrugające ꙮ na górnym pasku kursu: powrót do wyboru języka."""

    def __init__(self, app, color, **kw):
        super().__init__(size_hint=(None, 1), width=dp(38), **kw)
        self.app = app
        self.oko = Oko(calm=2.5, color=list(color))
        self.add_widget(self.oko)
        self.bind(pos=self._place, size=self._place)
        self.bind(on_release=lambda *a: app.hub.show_hub())

    def _place(self, *_):
        s = min(self.width, self.height) * 0.78
        self.oko.size = (s, s)
        self.oko.center = self.center
        self.oko._draw()
        Clock.schedule_once(lambda dt: self.oko._draw(), 0)


# ---------------------------------------------------------------------------
# Duże odpowiedzi do wyboru
# ---------------------------------------------------------------------------
def enlarge_options(widget, grid, buttons, max_h=None):
    """Rozciąga przyciski odpowiedzi, żeby zajęły wolne miejsce na ekranie (wygodniej na telefonie)."""
    max_h = max_h or dp(150)
    for b in buttons:
        b._base_h, b._base_fs = b.height, b.font_size

    def fit(*_):
        sv = widget.parent
        if sv is None or sv.height < dp(100) or not buttons:
            return
        kids = [c for c in widget.children if c is not grid]
        others = sum(c.height for c in kids) + widget.spacing * len(kids) + widget.padding[1] + widget.padding[3]
        rows = int(math.ceil(len(buttons) / float(grid.cols)))
        free = sv.height - others - grid.spacing[1] * (rows - 1)
        h = min(max_h, free / rows)
        for b in buttons:
            nh = max(b._base_h, h)
            if abs(b.height - nh) > 1:
                b.height = nh
                b.font_size = b._base_fs * min(1.35, max(1.0, nh / b._base_h * 0.8))

    trig = Clock.create_trigger(fit)
    widget.bind(parent=lambda *a: trig(), minimum_height=lambda *a: trig())

    def watch(*_):
        if widget.parent is not None:
            widget.parent.bind(height=lambda *a: trig())
            trig()
    widget.bind(parent=watch)
    Clock.schedule_once(fit, 0)


# ---------------------------------------------------------------------------
# Zgłaszanie błędów
# ---------------------------------------------------------------------------
class ReportFlag(ButtonBehavior, Widget):
    """Chorągiewka „oznacz błąd” na pasku lekcji."""

    def __init__(self, color, on_report, **kw):
        super().__init__(size_hint_x=None, width=dp(36), **kw)
        self.color = list(color)
        self.bind(pos=self._draw, size=self._draw, state=self._draw)
        self.bind(on_release=lambda *a: on_report())

    def _draw(self, *_):
        cx, cy = self.center
        s = dp(11)
        self.canvas.clear()
        with self.canvas:
            Color(*self.color[:3], 0.55 if self.state == "down" else 1)
            Line(points=[cx - s * 0.7, cy - s, cx - s * 0.7, cy + s], width=dp(1.3))
            Line(points=[cx - s * 0.7, cy + s, cx + s * 0.8, cy + s * 0.55, cx - s * 0.7, cy + s * 0.1],
                 width=dp(1.3), joint="round", close=True)


def exercise_report(ex, widget=None):
    """Zwięzły, czytelny opis ćwiczenia do zgłoszenia."""
    keep = ("type", "mode", "title", "prompt", "prompt_sub", "options", "answer", "word", "solution", "pairs",
            "bank", "why")
    out = {k: ex[k] for k in keep if k in ex and ex[k] not in (None, "", [])}
    choice = getattr(widget, "choice", None) if widget is not None else None
    if choice is not None:
        out["wybrano"] = choice
    return out
