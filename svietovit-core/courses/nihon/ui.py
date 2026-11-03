"""Interfejs kursu w aplikacji Śviętovit (uruchamiany z main.py w katalogu głównym)."""
import os
import random

from kivy.utils import platform  # noqa: F401
from courses.common import HubButton, ReportFlag, enlarge_options, exercise_report
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc

from . import engine as E
from .audio import generate_sounds
from .content import UNITS, TRACKS, CHATS, CHAT_EXTRA

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
LabelBase.register(name="Roboto", fn_regular=os.path.join(FONTS, "NihonSerif-Regular.ttf"),
                   fn_bold=os.path.join(FONTS, "NihonSerif-Bold.ttf"))
# Tekst kursu: ten sam krój co interfejs (Noto Serif CJK + łacina z FreeSerif).
LabelBase.register(name="Old_nihon", fn_regular=os.path.join(FONTS, "NihonSerif-Regular.ttf"),
                   fn_bold=os.path.join(FONTS, "NihonSerif-Bold.ttf"))

# ---------------------------------------------------------------------------
# Wygląd
# ---------------------------------------------------------------------------
# Paleta: papier hanji, błękit i czerwień taegeuk, czerń tuszu.
WHITE = hexc("#FBF9F3")
BG = hexc("#EEF0EA")
TEXT = hexc("#15181C")
INK = hexc("#15181C")
MUTED = hexc("#7D838A")
LINE = hexc("#CDD3D6")
GREEN, GREEN_D, GREEN_L = hexc("#2F7A45"), hexc("#235C34"), hexc("#DCEBDF")
BLUE, BLUE_D, BLUE_L = hexc("#B3261E"), hexc("#8C1C16"), hexc("#E1E8F0")
RED, RED_D, RED_L = hexc("#B3261E"), hexc("#8C1C16"), hexc("#F6DEDB")
GOLD, GOLD_D = hexc("#D9A514"), hexc("#A67D0C")
ORANGE = hexc("#B5562A")
PURPLE, PURPLE_L = hexc("#5E2750"), hexc("#ECE0E6")
YELLOW_L = hexc("#F1E8D2")
GRAY_BTN, GRAY_BTN_D = hexc("#E2DDD2"), hexc("#CBC4B6")

PRAISE = ["잘했어요!", "Brawo!", "좋아요!", "Dobrze!", "대박!", "Właśnie tak!"]


def darker(c, f=0.82):
    return [c[0] * f, c[1] * f, c[2] * f, 1]


def esc(t):
    return t.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def old(text, color=True):
    """Tekst kursu."""
    if color:
        body = "".join(esc(c) for c in text)
    else:
        body = esc(text)
    return "[font=Old_nihon]%s[/font]" % body


def old_tokens(tokens, color=True):
    return old(E.join(tokens), color)


def paint(widget, color, radius=dp(4), border=None, border_w=dp(1.5)):
    def redraw(*_):
        widget.canvas.before.clear()
        with widget.canvas.before:
            x, y = widget.pos
            w, h = widget.size
            if border:
                Color(*border)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[radius])
                Color(*color)
                RoundedRectangle(pos=(x + border_w, y + border_w), size=(w - 2 * border_w, h - 2 * border_w),
                                 radius=[max(0, radius - border_w)])
            else:
                Color(*color)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[radius])
    widget.bind(pos=redraw, size=redraw)
    redraw()


class L(Label):
    def __init__(self, text="", size=16, color=TEXT, bold=False, halign="left", wrap=True, **kw):
        kw.setdefault("markup", True)
        super().__init__(text=text, font_size=sp(size), color=color, bold=bold, halign=halign,
                         valign="middle", **kw)
        if wrap:
            self.size_hint_y = None
            self.bind(width=self._w, texture_size=self._h)
            self._w()

    def _w(self, *_):
        self.text_size = (self.width, None)

    def _h(self, *_):
        self.height = self.texture_size[1]


class Btn(ButtonBehavior, Label):
    fill = ListProperty(GREEN)
    shade = ListProperty(GREEN_D)
    edge = ListProperty([0, 0, 0, 0])
    depth = NumericProperty(dp(3))
    radius = NumericProperty(dp(4))

    def __init__(self, text="", fill=GREEN, shade=None, fg=WHITE, size=17, bold=True, edge=None,
                 wrap=True, **kw):
        kw.setdefault("markup", True)
        super().__init__(text=text, font_size=sp(size), color=fg, bold=bold, halign="center",
                         valign="middle", **kw)
        self.fill = fill
        self.shade = shade or darker(fill)
        if edge:
            self.edge = edge
        self.base_colors = (self.fill, self.shade, self.edge, self.color)
        self.bind(pos=self._draw, size=self._draw, state=self._draw, fill=self._draw, shade=self._draw,
                  edge=self._draw, disabled=self._draw)
        if wrap:
            self.bind(size=lambda *a: setattr(self, "text_size", (self.width - dp(20), None)))
        self._draw()

    def _draw(self, *_):
        self.canvas.before.clear()
        d = self.depth
        p = d - dp(1) if self.state == "down" else 0
        fill, shade, edge = self.fill, self.shade, self.edge
        if self.disabled:
            fill, shade, edge = GRAY_BTN, GRAY_BTN_D, [0, 0, 0, 0]
        x, y = self.pos
        w, h = self.size
        r = [self.radius]
        with self.canvas.before:
            Color(*shade)
            RoundedRectangle(pos=(x, y), size=(w, h - d), radius=r)
            by = y + d - p
            if edge[3] > 0:
                Color(*edge)
                RoundedRectangle(pos=(x, by), size=(w, h - d), radius=r)
                Color(*fill)
                RoundedRectangle(pos=(x + dp(1.5), by + dp(1.5)), size=(w - dp(3), h - d - dp(3)),
                                 radius=[max(0, self.radius - dp(1.5))])
            else:
                Color(*fill)
                RoundedRectangle(pos=(x, by), size=(w, h - d), radius=r)
        v = d - 2 * p
        self.padding = [dp(4), max(0, -v), dp(4), max(0, v)]
        if self.disabled:
            self.disabled_color = MUTED

    def style(self, fill, shade=None, edge=None, fg=None):
        self.fill = fill
        self.shade = shade or darker(fill)
        self.edge = edge or [0, 0, 0, 0]
        if fg:
            self.color = fg

    def reset_style(self):
        self.fill, self.shade, self.edge, self.color = self.base_colors


def option_btn(text, **kw):
    b = Btn(text, fill=WHITE, shade=LINE, edge=LINE, fg=TEXT, bold=False, **kw)
    b.base_colors = (WHITE, LINE, LINE, TEXT)
    return b


def select_style(b, on):
    if on:
        b.style(BLUE_L, INK, INK, INK)
    else:
        b.reset_style()


def spacer(h):
    return Widget(size_hint_y=None, height=h)


def toast(text, color=TEXT, duration=1.8):
    lbl = Label(text=text, color=WHITE, font_size=sp(15), bold=True, size_hint=(None, None),
                halign="center", markup=True)
    lbl.text_size = (min(Window.width - dp(60), dp(320)), None)
    lbl.texture_update()
    lbl.size = (lbl.texture_size[0] + dp(32), lbl.texture_size[1] + dp(22))
    paint(lbl, color, radius=dp(14))
    lbl.pos = ((Window.width - lbl.width) / 2, Window.height * 0.80)
    lbl.opacity = 0
    Window.add_widget(lbl)
    anim = Animation(opacity=1, d=0.15) + Animation(d=duration) + Animation(opacity=0, d=0.3)
    anim.bind(on_complete=lambda *a: Window.remove_widget(lbl))
    anim.start(lbl)


# ---------------------------------------------------------------------------
# Małe widżety
# ---------------------------------------------------------------------------
class XPBar(Widget):
    value = NumericProperty(0)
    color = ListProperty(GREEN)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw, value=self._draw, color=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        cy = y + h / 2
        t = max(dp(3), h * 0.45)
        with self.canvas:
            Color(*LINE)
            Rectangle(pos=(x, cy - dp(0.6)), size=(w, dp(1.2)))
            v = max(0, min(1, self.value))
            if v > 0:
                fw = max(t, w * v)
                Color(*self.color)
                Rectangle(pos=(x, cy - t / 2), size=(fw, t))
                Color(*RED)
                Ellipse(pos=(x + fw - t, cy - t), size=(t * 2, t * 2))

    def animate_to(self, v):
        Animation(value=v, d=0.35, t="out_quad").start(self)


class Stat(BoxLayout):
    def __init__(self, icon, color, **kw):
        super().__init__(orientation="horizontal", size_hint=(None, 1), width=dp(58), spacing=dp(4), **kw)
        self.icon = Label(text=icon, color=color, font_size=sp(22), bold=True, size_hint_x=None, width=dp(26))
        self.num = Label(text="0", color=color, font_size=sp(17), bold=True, halign="left", valign="middle")
        self.num.bind(size=lambda *a: setattr(self.num, "text_size", self.num.size))
        self.add_widget(self.icon)
        self.add_widget(self.num)

    def set(self, v, color=None):
        self.num.text = str(v)
        if color:
            self.num.color = self.icon.color = color


class TopBar(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(56), padding=[dp(16), 0],
                         spacing=dp(6), **kw)
        self.app = app
        self.title = L("", size=19, bold=True, wrap=False)
        self.title.bind(size=lambda *a: setattr(self.title, "text_size", self.title.size))
        self.streak = Stat("☀", ORANGE)
        self.gems = Stat("◆", GOLD_D)
        self.hearts = Stat("♥", RED)
        for w in (HubButton(app, MUTED), self.title, self.streak, self.gems, self.hearts):
            self.add_widget(w)
        with self.canvas.after:
            Color(*RED)
            self._line = Rectangle()
            Color(*INK)
            self._line2 = Rectangle()
        self.bind(pos=self._l, size=self._l)

    def _l(self, *_):
        self._line.pos = (self.x + dp(12), self.y + dp(3))
        self._line.size = (self.width - dp(24), dp(1.2))
        self._line2.pos = (self.x + dp(12), self.y)
        self._line2.size = (self.width - dp(24), dp(0.6))

    def refresh(self, title=""):
        st = self.app.state
        self.title.text = title or "[b][color=B3261E]日本語[/color][/b]"
        self.streak.set(st.data["streak"], ORANGE if st.data["last_goal_day"] == st.today().isoformat() else MUTED)
        self.gems.set(st.data["gems"])
        self.hearts.set(st.hearts())


class NavItem(ButtonBehavior, BoxLayout):
    def __init__(self, icon, name, on, **kw):
        super().__init__(orientation="vertical", spacing=dp(2), padding=[0, dp(4)], **kw)
        self.on = on
        self.glyph = Label(text=icon, font_size=sp(15 if len(icon) > 1 else 20), bold=True,
                           color=WHITE if on else MUTED)
        self.name = Label(text=name, font_size=sp(10), bold=on, color=RED if on else MUTED,
                          size_hint_y=None, height=dp(14))
        self.add_widget(self.glyph)
        self.add_widget(self.name)
        self._trig = Clock.create_trigger(self._draw)
        self.bind(pos=lambda *a: self._trig(), size=lambda *a: self._trig())
        self.glyph.bind(pos=lambda *a: self._trig(), size=lambda *a: self._trig())

    def _draw(self, *_):
        self.canvas.before.clear()
        if not self.on:
            return
        g = self.glyph
        s = min(g.height, dp(38))
        with self.canvas.before:
            Color(*GOLD)
            Ellipse(pos=(g.center_x - s / 2 - dp(2), g.center_y - s / 2 - dp(2)), size=(s + dp(4), s + dp(4)))
            Color(*RED)
            Ellipse(pos=(g.center_x - s / 2, g.center_y - s / 2), size=(s, s))


class NavBar(BoxLayout):
    def __init__(self, app, active, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(64), padding=[dp(8), dp(6)],
                         spacing=dp(4), **kw)
        items = [("日", "Nauka", "home"), ("は", "Cząstki", "sounds"), ("話", "Czat", "chats"),
                 ("復", "Powtórz", "practice"), ("私", "Profil", "profile")]
        for icon, name, key in items:
            b = NavItem(icon, name, key == active)
            b.bind(on_release=lambda _b, k=key: app.nav(k))
            self.add_widget(b)
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle()
            Color(*INK)
            self._line = Rectangle()
            Color(*RED)
            self._line2 = Rectangle()
        self.bind(pos=self._l, size=self._l)

    def _l(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        self._line.pos = (self.x + dp(12), self.top - dp(1.2))
        self._line.size = (self.width - dp(24), dp(0.6))
        self._line2.pos = (self.x + dp(12), self.top - dp(4.5))
        self._line2.size = (self.width - dp(24), dp(1.2))


# ---------------------------------------------------------------------------
# Ekran główny
# ---------------------------------------------------------------------------
class UnitNode(ButtonBehavior, Widget):
    """Dział jako moneta: brązowa ze czerwonym środkiem, gdy zdobyta."""

    def __init__(self, app, idx, **kw):
        super().__init__(size_hint=(None, None), size=(dp(84), dp(84)), **kw)
        self.app, self.idx = app, idx
        self._trig = Clock.create_trigger(self._draw)
        self.bind(pos=lambda *a: self._trig(), size=lambda *a: self._trig(), state=self._draw)
        icon = UNITS[idx]["icon"]
        self.icon = Label(text=icon, bold=True, font_size=sp(26 if len(icon) <= 2 else 20))
        self.add_widget(self.icon)
        self._draw()

    def _draw(self, *_):
        st = self.app.state
        u = UNITS[self.idx]
        unlocked = st.unlocked(self.idx)
        crowns, lessons = st.crowns(u["id"]), st.lessons(u["id"])
        cx, cy = self.center
        r = dp(33)
        p = dp(2) if self.state == "down" else 0
        cy -= p
        self.canvas.before.clear()
        with self.canvas.before:
            if not unlocked:
                Color(*LINE)
                Line(circle=(cx, cy, r), width=dp(1.1), dash_length=5, dash_offset=4)
                ink = MUTED
            elif crowns >= 1:
                Color(*GOLD)
                Ellipse(pos=(cx - r - dp(3), cy - r - dp(3)), size=(2 * r + dp(6), 2 * r + dp(6)))
                Color(*(GOLD_D if crowns >= E.MAX_CROWNS else RED))
                Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                Color(*GOLD)
                Line(circle=(cx, cy, r - dp(5)), width=dp(0.9))
                for k in range(16):
                    import math
                    a = math.radians(k * 22.5)
                    Ellipse(pos=(cx + math.cos(a) * (r - dp(5)) - dp(1.6), cy + math.sin(a) * (r - dp(5)) - dp(1.6)),
                            size=(dp(3.2), dp(3.2)))
                ink = WHITE
            else:
                Color(*WHITE)
                Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                Color(*RED)
                Line(circle=(cx, cy, r), width=dp(1.8))
                Line(circle=(cx, cy, r - dp(4)), width=dp(0.7))
                ink = RED
            if unlocked and crowns < E.MAX_CROWNS:
                for k in range(E.LESSONS_PER_LEVEL):
                    Color(*(RED if k < lessons else LINE))
                    Rectangle(pos=(cx - dp(16) + k * dp(12), cy - r - dp(12)), size=(dp(8), dp(3)))
        self.icon.color = ink
        self.icon.center = (cx, cy)


class HomeScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="home", **kw)
        self.app = app
        root = BoxLayout(orientation="vertical")
        paint(root, BG, radius=0)
        self.topbar = TopBar(app)
        root.add_widget(self.topbar)
        goal = BoxLayout(size_hint_y=None, height=dp(40), padding=[dp(16), dp(8)], spacing=dp(10))
        self.goal_lbl = L("", size=13, color=MUTED, bold=True, wrap=False, size_hint_x=None, width=dp(140))
        self.goal_lbl.bind(size=lambda *a: setattr(self.goal_lbl, "text_size", self.goal_lbl.size))
        self.goal_bar = XPBar(color=GOLD, size_hint_y=None, height=dp(14))
        gb = BoxLayout(padding=[0, dp(5)])
        gb.add_widget(self.goal_bar)
        goal.add_widget(self.goal_lbl)
        goal.add_widget(gb)
        root.add_widget(goal)
        self.scroll = ScrollView(do_scroll_x=False, bar_width=0)
        self.path = BoxLayout(orientation="vertical", size_hint_y=None, padding=[0, dp(10), 0, dp(30)])
        self.path.bind(minimum_height=self.path.setter("height"))
        self.scroll.add_widget(self.path)
        root.add_widget(self.scroll)
        root.add_widget(NavBar(app, "home"))
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        st = self.app.state
        self.topbar.refresh("")
        xp, goal = st.xp_today(), st.data["daily_goal"]
        self.goal_lbl.text = "Cel dnia  %d/%d XP" % (min(xp, goal), goal)
        self.goal_bar.value = min(1, xp / goal)
        self.path.clear_widgets()
        current = next((i for i, u in enumerate(UNITS) if st.unlocked(i) and st.crowns(u["id"]) == 0), None)
        for i, u in enumerate(UNITS):
            if i == 0 or u["track"] != UNITS[i - 1]["track"]:
                txt = "[color=A67C2E]·[/color]  [b]%s[/b]  [color=A67C2E]·[/color]" % TRACKS[u["track"]]
                if not st.unlocked(i):
                    txt += "\n[size=%d][color=8D877C]Odblokujesz po dziale: %s[/color][/size]" % (sp(12), st.unlock_reason(i))
                box = BoxLayout(size_hint_y=None, height=dp(70), padding=[dp(20), dp(14), dp(20), dp(6)])
                box.add_widget(L(txt, size=15, halign="center"))

                def rule(b, *_a):
                    b.canvas.before.clear()
                    with b.canvas.before:
                        Color(*RED)
                        Rectangle(pos=(b.x + dp(50), b.y + dp(4)), size=(b.width - dp(100), dp(1.2)))
                        Color(*GOLD)
                        Rectangle(pos=(b.x + dp(70), b.y + dp(1)), size=(b.width - dp(140), dp(0.6)))
                rtrig = Clock.create_trigger(lambda dt, b=box: rule(b))
                box.bind(pos=lambda *a, t=rtrig: t(), size=lambda *a, t=rtrig: t())
                self.path.add_widget(box)
            row = ButtonRow(size_hint_y=None, height=dp(108), padding=[dp(22), dp(8), dp(18), dp(8)], spacing=dp(16))
            node = UnitNode(self.app, i)
            row.add_widget(AnchorBox(node))
            crowns, unlocked = st.crowns(u["id"]), st.unlocked(i)
            marks = "".join("●" if k < crowns else "○" for k in range(E.MAX_CROWNS))
            info = "[b]%s[/b]\n[size=%d][color=%s]%s[/color][/size]" % (
                u["title"], sp(12), "9E2B25" if unlocked else "8D877C", marks if unlocked else "zamknięty")
            if st.cracked(i):
                info += "\n[size=%d][color=9E2B25]warto powtórzyć[/color][/size]" % sp(12)
            elif i == current:
                info += "\n[size=%d][color=4F6B3A]▸ zacznij tutaj[/color][/size]" % sp(12)
            lbl = Label(text=info, markup=True, color=TEXT if unlocked else MUTED, font_size=sp(17),
                        halign="left", valign="middle")
            lbl.bind(size=lambda l_, *_a: setattr(l_, "text_size", l_.size))
            row.add_widget(lbl)
            row.bind(on_release=lambda r, i=i: self.app.open_unit(i))
            if i == current:
                anim = Animation(opacity=0.6, d=0.9) + Animation(opacity=1, d=0.9)
                anim.repeat = True
                anim.start(node)

            def leader(r, *_a):
                r.canvas.before.clear()
                with r.canvas.before:
                    Color(*LINE)
                    Rectangle(pos=(r.x + dp(22), r.y), size=(r.width - dp(44), dp(0.8)))
            ltrig = Clock.create_trigger(lambda dt, r=row: leader(r))
            row.bind(pos=lambda *a, t=ltrig: t(), size=lambda *a, t=ltrig: t())
            self.path.add_widget(row)
        box = BoxLayout(size_hint_y=None, height=dp(70), padding=[dp(20), dp(10)])
        box.add_widget(L("Kolejne działy wkrótce.\nNie przerywaj serii!", size=14, color=MUTED, halign="center"))
        self.path.add_widget(box)


# ---------------------------------------------------------------------------
# Ćwiczenia
# ---------------------------------------------------------------------------
class TapLabel(ButtonBehavior, L):
    def __init__(self, text="", **kw):
        super().__init__(text=text, **kw)


class Exercise(BoxLayout):
    ready = BooleanProperty(False)
    graded = True
    scrollable = True
    button_text = "SPRAWDŹ"

    def __init__(self, app, ex, screen, **kw):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=dp(14),
                         padding=[dp(18), dp(8), dp(18), dp(18)], **kw)
        self.bind(minimum_height=self.setter("height"))
        self.app, self.ex, self.screen = app, ex, screen
        if ex.get("title"):
            self.add_widget(L(ex["title"], size=21, bold=True))

    def check(self):
        return True, None

    def solution(self):
        return self.ex.get("solution", "")




class IntroEx(Exercise):
    graded = False
    button_text = "DALEJ"

    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, dict(ex, title=None), screen, **kw)
        self.ready = True
        w = E.WORDS[ex["word"]]
        tag = "WYMOWA" if w["letter"] else "NOWE SŁOWO"
        self.add_widget(L("[b]%s[/b]" % tag, size=13, color=hexc("#5E2750")))
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(16), dp(20)], spacing=dp(6))
        card.bind(minimum_height=card.setter("height"))
        paint(card, WHITE, border=LINE, radius=dp(18))
        card.add_widget(L(old(w["form"]), size=88 if w["letter"] else 52, halign="center"))
        if not w["letter"] and app.state.data["settings"]["pron"]:
            card.add_widget(L("[i]czytaj: %s[/i]" % esc(w["tr"]), size=18, halign="center", color=MUTED))
        card.add_widget(L(w["pl"], size=19, halign="center"))
        self.add_widget(card)
        if w["cog"]:
            cg = BoxLayout(size_hint_y=None, padding=dp(12))
            cg.bind(minimum_height=cg.setter("height"))
            paint(cg, GREEN_L, radius=dp(14))
            cg.add_widget(L("[b]Znasz z polskiego:[/b]  %s" % w["cog"], size=16, color=GREEN_D))
            self.add_widget(cg)
        if w["hook"]:
            hk = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(14), spacing=dp(4))
            hk.bind(minimum_height=hk.setter("height"))
            paint(hk, YELLOW_L, radius=dp(14))
            hk.add_widget(L("[b]Zapamiętaj[/b]", size=13, color=hexc("#83611F")))
            hk.add_widget(L(self._hook_markup(w["hook"]), size=15))
            self.add_widget(hk)

    @staticmethod
    def _hook_markup(text):
        out, buf, in_old = "", "", False
        for c in text:
            is_old = ("Ѐ" <= c <= "ԯ") or ("Ꙁ" <= c <= "ꚟ") or c in E.GLAGOLITIC
            if is_old != in_old:
                out += old(buf, False) if in_old else esc(buf)
                buf, in_old = "", is_old
            buf += c
        out += old(buf, False) if in_old else esc(buf)
        return out


class InsightEx(Exercise):
    graded = False
    button_text = "ROZUMIEM"

    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, dict(ex, title=None), screen, **kw)
        self.ready = True
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(18), spacing=dp(10))
        card.bind(minimum_height=card.setter("height"))
        paint(card, PURPLE_L, radius=dp(18))
        card.add_widget(L("[b]WGLĄD[/b]", size=13, color=hexc("#5E2750")))
        card.add_widget(L(IntroEx._hook_markup(ex["title"]), size=22, bold=True))
        card.add_widget(L(IntroEx._hook_markup(ex["text"]), size=17))
        self.add_widget(card)
        self.add_widget(L("Nie ucz się tego na pamięć. Zauważ to, a potem użyj w kolejnych krokach.",
                          size=13, color=MUTED))


class ChoiceEx(Exercise):
    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, ex, screen, **kw)
        mode = ex["mode"]
        self.choice = None
        w = E.WORDS.get(ex.get("word")) if ex.get("word") else None
        if mode in ("meaning", "reading", "cognate"):
            big = w and w["letter"]
            self.add_widget(L(old(ex["prompt"]), size=80 if big else 46, halign="center"))
            if mode == "meaning" and w and not w["letter"] and self.app.state.data["settings"]["pron"]:
                self.add_widget(L("[i]%s[/i]" % esc(w["tr"]), size=17, color=MUTED, halign="center"))
        elif mode == "cloze":
            self.add_widget(L(old(ex["prompt"]), size=34, halign="center"))
            if ex.get("prompt_sub"):
                self.add_widget(L(ex["prompt_sub"], size=17, color=GREEN_D, halign="center", bold=True))
        elif mode == "form":
            bubble = BoxLayout(size_hint_y=None, padding=dp(14))
            bubble.bind(minimum_height=bubble.setter("height"))
            paint(bubble, WHITE, border=LINE)
            bubble.add_widget(L("„%s”" % ex["prompt"], size=20, bold=True, halign="center"))
            self.add_widget(bubble)
        elif mode == "sentence":
            self.add_widget(L(old_tokens(ex["words"]), size=30))
            self.add_widget(L("[i]%s[/i]" % esc(ex["prompt_sub"]), size=15, color=MUTED))
        opts = ex["options"]
        old_opts = mode in ("form", "cloze")
        long_text = mode in ("sentence", "meaning", "cognate", "reading") and any(len(o) > 12 for o in opts)
        grid = GridLayout(cols=1 if long_text else 2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        self.buttons = []
        for o in opts:
            if mode == "cloze":
                txt, h = "[size=%d]%s[/size]" % (sp(26), old("-" + o)), dp(68)
            elif old_opts:
                txt, h = "[size=%d]%s[/size]" % (sp(24 if len(o) <= 8 else 19), old(o)), dp(70)
            elif mode == "reading":
                txt, h = "[size=%d][i]%s[/i][/size]" % (sp(21), esc(o)), dp(64)
            else:
                txt, h = esc(o), dp(60)
            b = option_btn(txt, size=16, size_hint_y=None, height=h)
            b.value = o
            b.bind(on_release=self.pick)
            grid.add_widget(b)
            self.buttons.append(b)
        self.add_widget(grid)
        enlarge_options(self, grid, self.buttons)

    def pick(self, b):
        self.app.sfx("tap")
        for x in self.buttons:
            select_style(x, x is b)
        self.choice = b.value
        self.ready = True

    def check(self):
        ok = self.choice == self.ex["answer"]
        for b in self.buttons:
            if b.value == self.ex["answer"]:
                b.style(GREEN_L, GREEN, GREEN, GREEN_D)
            elif b.value == self.choice:
                b.style(RED_L, RED, RED, RED_D)
            b.unbind(on_release=self.pick)
        return ok, (None if ok else self.ex.get("why"))


class MatchEx(Exercise):
    button_text = "DALEJ"

    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, ex, screen, **kw)
        pairs = ex["pairs"]
        left, right = [p[0] for p in pairs], [p[1] for p in pairs]
        random.shuffle(left)
        random.shuffle(right)
        self.answer = dict(pairs)
        self.sel = {"l": None, "r": None}
        self.matched = self.mistakes = 0
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for a, b in zip(left, right):
            lb = option_btn("[size=%d]%s[/size]" % (sp(26 if len(a) <= 2 else 20), old(a)), size_hint_y=None,
                            height=dp(64))
            lb.value, lb.side = a, "l"
            rb = option_btn(esc(b), size=14, size_hint_y=None, height=dp(64))
            rb.value, rb.side = b, "r"
            for x in (lb, rb):
                x.bind(on_release=self.pick)
                grid.add_widget(x)
        self.add_widget(grid)

    def pick(self, b):
        if getattr(b, "done", False):
            return
        self.app.sfx("tap")
        prev = self.sel[b.side]
        if prev is not None:
            select_style(prev, False)
        self.sel[b.side] = b
        select_style(b, True)
        l, r = self.sel["l"], self.sel["r"]
        if l and r:
            if self.answer[l.value] == r.value:
                for x in (l, r):
                    x.done = True
                    x.style(GREEN_L, GREEN, GREEN, GREEN_D)
                    Clock.schedule_once(lambda dt, x=x: x.style(WHITE, LINE, LINE, LINE), 0.35)
                self.matched += 1
                if self.matched == len(self.answer):
                    self.ready = True
                    Clock.schedule_once(lambda dt: self.screen.auto_complete(self.mistakes == 0), 0.5)
            else:
                self.mistakes += 1
                self.app.sfx("wrong")
                for x in (l, r):
                    x.style(RED_L, RED, RED, RED_D)
                    Clock.schedule_once(lambda dt, x=x: x.reset_style(), 0.5)
            self.sel = {"l": None, "r": None}


def make_tile(tok, show_tr, handler):
    txt = "[size=%d]%s[/size]" % (sp(22), old(tok))
    if show_tr and E.token_tr(tok):
        txt += "\n[size=%d][color=8D877C][i]%s[/i][/color][/size]" % (sp(11), esc(E.token_tr(tok)))
    b = option_btn(txt, wrap=False, size_hint=(None, None), height=dp(58 if show_tr else 50))
    b.texture_update()
    b.width = max(dp(48), b.texture_size[0] + dp(26))
    b.value = tok
    b.bind(on_release=handler)
    return b


class BuildEx(Exercise):
    def __init__(self, app, ex, screen, show_tr=True, **kw):
        super().__init__(app, ex, screen, **kw)
        self.show_tr = show_tr
        bubble = BoxLayout(size_hint_y=None, padding=dp(14))
        bubble.bind(minimum_height=bubble.setter("height"))
        paint(bubble, WHITE, border=LINE)
        bubble.add_widget(L("„%s”" % ex["prompt"], size=19, bold=True))
        self.add_widget(bubble)
        if ex.get("think"):
            tb = BoxLayout(size_hint_y=None, padding=dp(12))
            tb.bind(minimum_height=tb.setter("height"))
            paint(tb, PURPLE_L, radius=dp(12))
            tb.add_widget(L("[b][color=5E2750]Pomyśl:[/color][/b] " + IntroEx._hook_markup(ex["think"]), size=14))
            self.add_widget(tb)
        self.answer_area = StackLayout(size_hint_y=None, spacing=dp(8), padding=[0, dp(8)], height=dp(130))
        self.answer_area.bind(minimum_height=self._fit, pos=self._lines, size=self._lines)
        self.add_widget(self.answer_area)
        self.bank = StackLayout(size_hint_y=None, spacing=dp(8))
        self.bank.bind(minimum_height=self.bank.setter("height"))
        self.add_widget(self.bank)
        for tok in ex["bank"]:
            self.bank.add_widget(make_tile(tok, show_tr, self.move))

    def _fit(self, *_):
        self.answer_area.height = max(dp(130), self.answer_area.minimum_height)

    def _lines(self, *_):
        a = self.answer_area
        a.canvas.before.clear()
        with a.canvas.before:
            Color(*LINE)
            y = a.top - dp(70)
            while y > a.y:
                Rectangle(pos=(a.x, y), size=(a.width, dp(2)))
                y -= dp(64)

    def move(self, b):
        self.app.sfx("tap")
        if b.parent is self.answer_area:
            self.answer_area.remove_widget(b)
            ph = b.home
            idx = self.bank.children.index(ph)
            self.bank.remove_widget(ph)
            self.bank.add_widget(b, index=idx)
        else:
            idx = self.bank.children.index(b)
            ph = Widget(size_hint=(None, None), size=b.size)
            paint(ph, LINE, radius=dp(12))
            self.bank.remove_widget(b)
            self.bank.add_widget(ph, index=idx)
            b.home = ph
            self.answer_area.add_widget(b)
        self.ready = bool(self.given())

    def given(self):
        return [w.value for w in reversed(self.answer_area.children)]

    def check(self):
        g = self.given()
        for w in self.walk():
            if isinstance(w, Btn):
                w.unbind(on_release=self.move)
        if E.join(g) == E.join(self.ex["answer"]):
            return True, None
        return False, E.explain_mistake(g, self.ex["answer"], self.ex.get("traps"))

    def solution(self):
        text, pr = old_tokens(self.ex["answer"]), E.sentence_tr(self.ex["answer"])
        if E.plain(E.join(self.ex["answer"])).lower() == E.plain(pr).lower():
            return text
        return "%s\n[i]czytaj: %s[/i]" % (text, esc(pr))


class DrawPad(Widget):
    def __init__(self, char, **kw):
        super().__init__(**kw)
        self.strokes = []
        self.guide = Label(text=old(char, False), markup=True, color=(0, 0, 0, 0))
        self.model = Label(text=old(char, False), markup=True, color=(0, 0, 0, 0))
        self.add_widget(self.guide)
        self.bind(pos=self._bg, size=self._bg)
        self.on_change = None
        self.locked = False

    def _bg(self, *_):
        self.canvas.before.clear()
        x, y = self.pos
        s = self.width
        with self.canvas.before:
            Color(*WHITE)
            RoundedRectangle(pos=(x, y), size=(s, s), radius=[dp(16)])
            Color(*hexc("#C9BFA9"))
            Line(rounded_rectangle=(x, y, s, s, dp(16)), width=dp(1.5))
            for f in (0.25, 0.75):
                Line(points=[x, y + s * f, x + s, y + s * f], width=1, dash_length=8, dash_offset=6)
            Line(points=[x + s / 2, y, x + s / 2, y + s], width=1, dash_length=8, dash_offset=6)
        for lbl in (self.guide, self.model):
            lbl.font_size = s * 0.7
            lbl.size = (s, s)
            lbl.pos = (x, y)

    def show_guide(self, on):
        self.guide.color = (0, 0, 0, 0.12 if on else 0)

    def reveal(self):
        if self.model.parent is None:
            self.add_widget(self.model)
        self.model.color = list(RED[:3]) + [0.35]
        self.locked = True

    def clear(self):
        for g in self.strokes:
            self.canvas.remove(g)
        self.strokes = []
        if self.on_change:
            self.on_change()

    def on_touch_down(self, t):
        if self.locked or not self.collide_point(*t.pos):
            return False
        with self.canvas:
            Color(*TEXT)
            line = Line(points=[t.x, t.y], width=dp(5), cap="round", joint="round")
        self.strokes.append(line)
        t.ud["line"] = line
        t.grab(self)
        return True

    def on_touch_move(self, t):
        if t.grab_current is self and "line" in t.ud:
            t.ud["line"].points += [min(max(t.x, self.x), self.right), min(max(t.y, self.y), self.top)]
            return True

    def on_touch_up(self, t):
        if t.grab_current is self:
            t.ungrab(self)
            if self.on_change:
                self.on_change()
            return True


class DrawEx(Exercise):
    scrollable = False

    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, ex, screen, **kw)
        self.size_hint_y = 1
        self.unbind(minimum_height=self.setter("height"))
        w = E.WORDS[ex["word"]]
        self.add_widget(L("[b]%s[/b]   %s" % (esc(w["pl"]), IntroEx._hook_markup(w["hook"] or "")), size=15))
        holder = FloatLayout()
        self.pad = DrawPad(ex["answer"], size_hint=(None, None))
        holder.add_widget(self.pad)

        def fit(*_):
            s = min(holder.width, holder.height, dp(340))
            self.pad.size = (s, s)
            self.pad.center = holder.center
        holder.bind(pos=fit, size=fit)
        self.add_widget(holder)
        self.pad.on_change = lambda: setattr(self, "ready", bool(self.pad.strokes))
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        clr = option_btn("Wyczyść", size=15)
        clr.bind(on_release=lambda *a: self.pad.clear())
        self.hint_btn = option_btn("Pokaż wzór", size=15)
        self.hint_btn.bind(on_release=self.toggle_guide)
        row.add_widget(clr)
        row.add_widget(self.hint_btn)
        self.add_widget(row)
        self.guide_on = False

    def toggle_guide(self, *_):
        self.guide_on = not self.guide_on
        self.pad.show_guide(self.guide_on)
        self.hint_btn.text = "Ukryj wzór" if self.guide_on else "Pokaż wzór"

    def check(self):
        self.pad.show_guide(False)
        self.pad.reveal()
        return "self", "Porównaj swoje pociągnięcia z czerwonym wzorem. Bądź uczciwy!"


class TypeEx(Exercise):
    def __init__(self, app, ex, screen, **kw):
        super().__init__(app, ex, screen, **kw)
        self.add_widget(L("„%s”" % ex["prompt"], size=28, bold=True, halign="center"))
        if ex.get("prompt_sub"):
            self.add_widget(L(ex["prompt_sub"], size=15, halign="center", color=GREEN_D))
        self.inp = TextInput(multiline=False, font_size=sp(22), size_hint_y=None, height=dp(56),
                             hint_text="po japońsku lub romaji…", padding=[dp(14), dp(14)], background_color=hexc("#E3DFD5"),
                             foreground_color=TEXT, write_tab=False)
        self.inp.bind(text=lambda *a: setattr(self, "ready", bool(self.inp.text.strip())))
        self.inp.bind(on_text_validate=lambda *a: screen.press_main())
        self.add_widget(self.inp)
        self.add_widget(L("Wpisz po japońsku (klawiatura 日本語) albo literami łacińskimi, np. arigatou.", size=13, color=MUTED))

    def _insert(self, ch):
        self.inp.insert_text(ch)
        self.inp.focus = True

    def check(self):
        res = E.check_typed(self.inp.text, self.ex["answer"])
        self.inp.readonly = True
        self.inp.focus = False
        if res == "close":
            return True, "Dobrze! Pełny zapis: %s" % self.ex["answer"]
        return res == "correct", None


EX_CLASSES = {"intro": IntroEx, "insight": InsightEx, "choice": ChoiceEx, "match": MatchEx,
              "build": BuildEx, "draw": DrawEx, "type": TypeEx}


# ---------------------------------------------------------------------------
# Ekran lekcji
# ---------------------------------------------------------------------------
class LessonScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="lesson", **kw)
        self.app = app
        self.session = None
        root = BoxLayout(orientation="vertical")
        paint(root, BG, radius=0)
        top = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(10), dp(14), dp(16), dp(14)], spacing=dp(12))
        x = Btn("×", fill=WHITE, shade=WHITE, fg=MUTED, size=30, bold=False, size_hint_x=None, width=dp(40))
        x.depth = 0
        x.bind(on_release=lambda *a: self.ask_quit())
        self.bar = XPBar(size_hint_y=None, height=dp(16))
        bb = BoxLayout(padding=[0, dp(6)])
        bb.add_widget(self.bar)
        self.hearts = Stat("♥", RED)
        self.hearts.width = dp(56)
        flag = ReportFlag(MUTED, self.report_mistake)
        for w in (x, bb, flag, self.hearts):
            top.add_widget(w)
        root.add_widget(top)
        self.combo_lbl = L("", size=13, bold=True, color=ORANGE, halign="center")
        root.add_widget(self.combo_lbl)
        self.body = BoxLayout()
        root.add_widget(self.body)
        self.bottom = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(18), dp(14), dp(18), dp(18)],
                                spacing=dp(8))
        self.bottom.bind(minimum_height=self.bottom.setter("height"))
        self.fb_title = L("", size=20, bold=True)
        self.fb_text = L("", size=15)
        self.btn_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
        self.main_btn = Btn("SPRAWDŹ", size_hint_y=None, height=dp(54))
        self.main_btn.bind(on_release=lambda *a: self.press_main())
        self.btn_row.add_widget(self.main_btn)
        self.bottom.add_widget(self.btn_row)
        root.add_widget(self.bottom)
        self.add_widget(root)
        self._upd = None
        self.phase = "answer"

    def start(self, session, level=0):
        self.session = session
        self.level = level
        self.bar.value = 0
        self.combo_lbl.text = ""
        self.hearts.opacity = 1 if session.use_hearts else 0
        self.hearts.set(self.app.state.hearts())
        self.show_current()

    def show_current(self):
        ex = self.session.current
        self.phase = "answer"
        self.set_feedback(None)
        self.body.clear_widgets()
        cls = EX_CLASSES[ex["type"]]
        if cls is BuildEx:
            w = cls(self.app, ex, self, show_tr=self.level < 2 or ex.get("think") is not None)
        else:
            w = cls(self.app, ex, self)
        if ex.get("_retry"):
            w.add_widget(L("[color=9E2B25][b]Wcześniejszy błąd[/b][/color]", size=12), index=len(w.children))
        self.ex_widget = w
        if w.scrollable:
            sv = ScrollView(do_scroll_x=False, bar_width=dp(3))
            sv.add_widget(w)
            self.body.add_widget(sv)
        else:
            self.body.add_widget(w)
        if self.main_btn.parent is not self.btn_row:
            self.btn_row.clear_widgets()
            self.btn_row.add_widget(self.main_btn)
        self.main_btn.text = w.button_text
        self.main_btn.reset_style()
        self.main_btn.disabled = not w.ready or ex["type"] == "match"
        w.bind(ready=lambda inst, v: setattr(self.main_btn, "disabled", not v) if self.phase == "answer" else None)
        if ex["type"] == "match":
            self.main_btn.disabled = True

    def _bg(self, color, top_line):
        if self._upd:
            self.bottom.unbind(pos=self._upd, size=self._upd)
        self.bottom.canvas.before.clear()
        with self.bottom.canvas.before:
            Color(*LINE)
            r1 = Rectangle()
            Color(*color)
            r2 = Rectangle()

        def upd(*_):
            r1.pos, r1.size = (self.bottom.x, self.bottom.top - dp(2)), (self.bottom.width, dp(2) if top_line else 0)
            r2.pos, r2.size = self.bottom.pos, (self.bottom.width, self.bottom.height - (dp(2) if top_line else 0))
        self._upd = upd
        self.bottom.bind(pos=upd, size=upd)
        upd()

    def set_feedback(self, kind, title="", text=""):
        self.bottom.clear_widgets()
        if kind is None:
            self._bg(WHITE, True)
            self.bottom.add_widget(self.btn_row)
            return
        bg, fg = {"good": (GREEN_L, GREEN_D), "bad": (RED_L, RED_D), "self": (BLUE_L, BLUE_D)}[kind]
        self._bg(bg, False)
        self.fb_title.text, self.fb_title.color = title, fg
        self.fb_text.text, self.fb_text.color = text, fg
        self.bottom.add_widget(self.fb_title)
        if text:
            self.bottom.add_widget(self.fb_text)
        self.bottom.add_widget(self.btn_row)
        self.bottom.opacity = 0.4
        Animation(opacity=1, d=0.15).start(self.bottom)

    def press_main(self):
        if self.main_btn.disabled:
            return
        w = self.ex_widget
        if self.phase == "answer":
            if not w.graded:
                self.advance(None)
                return
            ok, why = w.check()
            if ok == "self":
                self.self_grade(why)
                return
            self.grade(ok, why)
        elif self.phase == "feedback":
            self.advance(self._last_ok)

    def auto_complete(self, ok):
        if self.phase != "answer" or not isinstance(self.ex_widget, MatchEx):
            return
        self.app.sfx("correct")
        self.phase = "feedback"
        self._last_ok = True
        self.set_feedback("good", random.choice(PRAISE) if ok else "Wszystko dopasowane!")
        self.main_btn.text = "DALEJ"
        self.main_btn.disabled = False
        self.main_btn.style(GREEN)

    def grade(self, ok, why):
        self.phase = "feedback"
        self._last_ok = ok
        if ok:
            self.app.sfx("correct")
            self.set_feedback("good", random.choice(PRAISE))
            self.main_btn.style(GREEN)
        else:
            self.app.sfx("wrong")
            sol = self.ex_widget.solution()
            sol_m = sol if sol.startswith("[") else IntroEx._hook_markup(sol)
            text = sol_m + (("\n\n[b]Pomyśl:[/b] " + IntroEx._hook_markup(why)) if why else "")
            self.set_feedback("bad", "Poprawna odpowiedź:", text)
            self.main_btn.style(RED)
            if self.session.use_hearts:
                self.app.state.lose_heart()
                self.hearts.set(self.app.state.hearts())
        self.main_btn.text = "DALEJ"
        self.main_btn.disabled = False

    def self_grade(self, why):
        self.phase = "self"
        self.set_feedback("self", "Jak ci poszło?", why)
        self.btn_row.clear_widgets()
        no = Btn("NIE CAŁKIEM", fill=RED, size_hint_y=None, height=dp(54))
        yes = Btn("UDAŁO SIĘ", fill=GREEN, size_hint_y=None, height=dp(54))
        no.bind(on_release=lambda *a: self._self_done(False))
        yes.bind(on_release=lambda *a: self._self_done(True))
        self.btn_row.add_widget(no)
        self.btn_row.add_widget(yes)

    def _self_done(self, ok):
        self.btn_row.clear_widgets()
        self.btn_row.add_widget(self.main_btn)
        self.app.sfx("correct" if ok else "wrong")
        self.advance(ok)

    def advance(self, ok):
        s = self.session
        milestone = s.answer(ok)
        self.bar.animate_to(s.progress)
        self.combo_lbl.text = ("☀ %d Z RZĘDU" % s.combo) if s.combo >= 3 else ""
        if milestone:
            self.app.sfx("streak")
            toast("☀ %d z rzędu!" % milestone, ORANGE)
        if s.use_hearts and self.app.state.hearts() <= 0 and not s.finished:
            self.app.state.save()
            self.out_of_hearts()
            return
        if s.finished:
            self.app.finish_session(s)
        else:
            self.show_current()

    def report_mistake(self):
        ex = self.session.current if self.session else None
        if ex is None:
            return
        self.app.hub.report_mistake(self.app, exercise_report(ex, getattr(self, "ex_widget", None)))

    def ask_quit(self):
        self.app.confirm("Zaczekaj, nie odchodź!", "Stracisz postęp w tej lekcji.", "UCZĘ SIĘ DALEJ",
                         "ZAKOŃCZ", on_no=self.app.go_home)

    def out_of_hearts(self, on_refill=None):
        st = self.app.state
        mv = ModalView(size_hint=(0.88, None), height=dp(390), auto_dismiss=False, background_color=(0, 0, 0, 0.5))
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
        paint(box, WHITE, radius=dp(20))
        box.add_widget(L("[color=9E2B25]♥[/color] 0", size=40, bold=True, halign="center"))
        box.add_widget(L("Skończyły ci się serca", size=20, bold=True, halign="center"))
        mins = st.seconds_to_next_heart() // 60 + 1
        box.add_widget(L("Zrób powtórkę, żeby odzyskać serce, albo poczekaj %d min." % mins, size=15,
                         color=MUTED, halign="center"))
        refill = Btn("UZUPEŁNIJ  ◆ %d" % E.REFILL_COST, fill=BLUE, size_hint_y=None, height=dp(52))
        refill.disabled = st.data["gems"] < E.REFILL_COST

        def do_refill(*_):
            if st.buy_refill():
                st.save()
                mv.dismiss()
                if on_refill:
                    on_refill()
                else:
                    self.hearts.set(st.hearts())
                    self.show_current()
        refill.bind(on_release=do_refill)
        prac = Btn("POWTÓRKA ZA SERCE", fill=GREEN, size_hint_y=None, height=dp(52))
        prac.bind(on_release=lambda *a: (mv.dismiss(), self.app.start_practice()))
        quit_ = Btn("WYJDŹ", fill=WHITE, shade=WHITE, fg=MUTED, size_hint_y=None, height=dp(44))
        quit_.bind(on_release=lambda *a: (mv.dismiss(), self.app.go_home()))
        for b in (refill, prac, quit_):
            box.add_widget(b)
        mv.add_widget(box)
        mv.open()


# ---------------------------------------------------------------------------
# Wyniki
# ---------------------------------------------------------------------------
class Initial(Widget):
    """Moneta: brązowy brzeg, czerwone pole, wybita litera."""
    scale = NumericProperty(1)

    def __init__(self, char, **kw):
        super().__init__(**kw)
        self.lbl = Label(text=char, font_size=sp(54), bold=True, color=WHITE)
        self.add_widget(self.lbl)
        self.bind(pos=self._draw, size=self._draw, scale=self._draw)

    def _draw(self, *_):
        import math
        from kivy.graphics import PushMatrix, PopMatrix, Scale
        self.canvas.before.clear()
        r = dp(50)
        cx, cy = self.center
        with self.canvas.before:
            PushMatrix()
            Scale(self.scale, self.scale, 1, origin=(cx, cy))
            Color(*GOLD)
            Ellipse(pos=(cx - r - dp(5), cy - r - dp(5)), size=(2 * r + dp(10), 2 * r + dp(10)))
            Color(*RED)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(*GOLD)
            Line(circle=(cx, cy, r - dp(7)), width=dp(1))
            for k in range(24):
                a = math.radians(k * 15)
                Ellipse(pos=(cx + math.cos(a) * (r - dp(7)) - dp(2), cy + math.sin(a) * (r - dp(7)) - dp(2)),
                        size=(dp(4), dp(4)))
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()
        self.lbl.center = (cx, cy)

    def stamp(self):
        self.scale, self.opacity = 1.6, 0
        Animation(scale=1, opacity=1, d=0.3, t="out_quad").start(self)


class ResultsScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="results", **kw)
        self.app = app

    def show(self, ev, session):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=[dp(22), dp(40), dp(22), dp(22)], spacing=dp(16))
        paint(root, BG, radius=0)
        big = Initial("V", size_hint_y=None, height=dp(126))
        root.add_widget(big)
        root.add_widget(L("[b][color=9E2B25]VICTORIA![/color][/b]", size=34, halign="center"))
        title = "Lekcja ukończona!" if session.kind == "lesson" else "Powtórka ukończona!"
        if ev["perfect"]:
            title = "Lekcja bez błędu!"
        root.add_widget(L(title, size=26, bold=True, halign="center", color=GOLD_D))
        tiles = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(10))
        self.xp_num = Label(text="0", font_size=sp(26), bold=True, color=GOLD_D)
        for name, val, col in (("XP", None, GOLD), ("TRAFNOŚĆ", "%d%%" % round(ev["accuracy"] * 100), GREEN),
                               ("SERIA", str(session.max_combo), ORANGE)):
            t = BoxLayout(orientation="vertical", padding=[dp(4), dp(4), dp(4), dp(10)])
            paint(t, col, radius=dp(16))
            t.add_widget(Label(text=name, font_size=sp(12), bold=True, color=WHITE, size_hint_y=None, height=dp(26)))
            inner = BoxLayout(padding=[dp(4), 0])
            paint(inner, WHITE, radius=dp(12))
            inner.add_widget(self.xp_num if val is None else
                             Label(text=val, font_size=sp(24), bold=True, color=darker(col)))
            t.add_widget(inner)
            tiles.add_widget(t)
        root.add_widget(tiles)
        lines = []
        if ev["combo_bonus"]:
            lines.append("☀ Premia za serię  +%d XP" % ev["combo_bonus"])
        if ev["perfect"]:
            lines.append("★ Bez błędów  +2 XP")
        lines.append("◆ +%d klejnotów" % ev["gems"])
        if ev.get("crown_up"):
            lines.append("[color=83611F][b]★ %s: poziom %d![/b][/color]" % (UNITS[session.unit_idx]["title"],
                                                                         ev["crown_up"]))
        for ui in ev.get("unlocked") or []:
            lines.append("[color=4F6B3A][b]Nowy dział: %s[/b][/color]" % UNITS[ui]["title"])
        for c in ev.get("chats") or []:
            lines.append("[color=2F3B45][b]Nowa rozmowa: %s[/b][/color]" % c)
        if ev.get("heart_back"):
            lines.append("[color=9E2B25]♥[/color] Odzyskane serce")
        st = self.app.state
        if ev["streak_extended"]:
            lines.append("[color=9E2B25][b]☀ Seria: %d dni! Cel dnia osiągnięty.[/b][/color]" % ev["streak"])
        elif st.data["daily_goal"] > st.xp_today():
            lines.append("[color=8D877C]Do celu dnia brakuje %d XP[/color]" % (st.data["daily_goal"] - st.xp_today()))
        for ln in lines:
            root.add_widget(L(ln, size=16, halign="center"))
        root.add_widget(Widget())
        b = Btn("DALEJ", size_hint_y=None, height=dp(54))
        b.bind(on_release=lambda *a: self.app.go_home())
        root.add_widget(b)
        self.add_widget(root)
        self._target, self._cur = ev["xp"], 0
        Clock.schedule_interval(self._tick, 0.05)
        big.stamp()
        if ev["streak_extended"]:
            Clock.schedule_once(lambda dt: self.app.sfx("streak"), 0.9)

    def _tick(self, dt):
        self._cur += 1
        self.xp_num.text = str(self._cur)
        return self._cur < self._target


# ---------------------------------------------------------------------------
# Profil
# ---------------------------------------------------------------------------
class WeekChart(Widget):
    def __init__(self, data, goal, **kw):
        super().__init__(size_hint_y=None, height=dp(140), **kw)
        self.data, self.goal = data, goal
        self.labels = []
        for d, v in data:
            for txt in (d, str(v) if v else ""):
                lb = Label(text=txt, font_size=sp(11), color=MUTED, bold=True, size_hint=(None, None),
                           size=(dp(36), dp(16)))
                self.add_widget(lb)
                self.labels.append(lb)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        n = len(self.data)
        top = max([self.goal] + [v for _, v in self.data])
        bw = self.width / n
        base = self.y + dp(20)
        hmax = self.height - dp(40)
        with self.canvas.before:
            gy = base + hmax * self.goal / top
            Color(*GOLD)
            Line(points=[self.x, gy, self.right, gy], width=1, dash_length=6, dash_offset=4)
            for i, (_, v) in enumerate(self.data):
                h = max(dp(4), hmax * v / top)
                Color(*(GOLD if v >= self.goal else (BLUE if v else LINE)))
                RoundedRectangle(pos=(self.x + i * bw + bw * 0.22, base), size=(bw * 0.56, h), radius=[dp(6)])
                self.labels[2 * i].center = (self.x + i * bw + bw / 2, self.y + dp(8))
                self.labels[2 * i + 1].center = (self.x + i * bw + bw / 2, base + h + dp(9))


class ProfileScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="profile", **kw)
        self.app = app

    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        app, st = self.app, self.app.state
        d = st.data
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")
        paint(root, BG, radius=0)
        top = TopBar(app)
        top.refresh("Profil")
        root.add_widget(top)
        sv = ScrollView(do_scroll_x=False, bar_width=0)
        col = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(18), spacing=dp(14))
        col.bind(minimum_height=col.setter("height"))
        lvl, cur, need = st.level()
        col.add_widget(L("Poziom %d" % lvl, size=24, bold=True))
        col.add_widget(XPBar(color=PURPLE, size_hint_y=None, height=dp(14), value=cur / need))
        col.add_widget(L("%d / %d XP do poziomu %d" % (cur, need, lvl + 1), size=13, color=MUTED))
        stats = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(150))
        crowns = sum(st.crowns(u["id"]) for u in UNITS)
        n_words = len([h for h in st.learned_words() if not E.WORDS[h]["letter"]])
        n_letters = len([h for h in st.learned_words() if E.WORDS[h]["letter"]])
        for icon, colr, val, name in (("☀", ORANGE, d["streak"], "Dni serii (rekord %d)" % d["longest_streak"]),
                                      ("XP", GOLD_D, d["xp_total"], "Razem XP"),
                                      ("A", GREEN, n_words, "Słowa łacińskie"),
                                      ("★", GOLD, crowns, "Korony")):
            t = BoxLayout(padding=[dp(12), dp(6)], spacing=dp(8))
            paint(t, WHITE, border=LINE, radius=dp(14))
            t.add_widget(Label(text=icon, markup=True, color=colr, font_size=sp(20), bold=True, size_hint_x=None,
                               width=dp(32)))
            v = BoxLayout(orientation="vertical")
            for txt, sz, c2 in ((str(val), 19, TEXT), (name, 11, MUTED)):
                lb = L(txt, size=sz, bold=sz > 12, color=c2, wrap=False)
                lb.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
                v.add_widget(lb)
            t.add_widget(v)
            stats.add_widget(t)
        col.add_widget(stats)
        col.add_widget(L("Ten tydzień", size=18, bold=True))
        col.add_widget(WeekChart(st.week_xp(), d["daily_goal"]))
        col.add_widget(L("Cel dnia", size=18, bold=True))
        gg = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(120))
        for name, xp in E.GOALS:
            b = option_btn("%s  ·  %d XP" % (name, xp), size=14)
            if d["daily_goal"] == xp:
                select_style(b, True)
            b.bind(on_release=lambda _b, xp=xp: self.set_goal(xp))
            gg.add_widget(b)
        col.add_widget(gg)
        col.add_widget(L("Sklep  [color=83611F]◆ %d[/color]" % d["gems"], size=18, bold=True))
        col.add_widget(self.shop_item("Zamrożenie serii", "Chroni serię, gdy opuścisz dzień. Masz: %d/%d"
                                      % (d["freezes"], E.MAX_FREEZES), E.FREEZE_COST, self.buy_freeze,
                                      d["gems"] >= E.FREEZE_COST and d["freezes"] < E.MAX_FREEZES))
        col.add_widget(self.shop_item("Komplet serc", "Serca: %d/%d" % (st.hearts(), E.HEART_MAX), E.REFILL_COST,
                                      self.buy_refill, d["gems"] >= E.REFILL_COST and st.hearts() < E.HEART_MAX))
        col.add_widget(L("Klejnoty zdobywasz za lekcje. Lekcje bez błędu i nowe korony dają więcej.",
                         size=12, color=MUTED))
        col.add_widget(L("Ustawienia", size=18, bold=True))
        for key, label in (("sound", "Efekty dźwiękowe"), ("pron", "Wymowa pod słowami")):
            b = option_btn("%s: %s" % (label, "WŁ." if d["settings"][key] else "WYŁ."), size=15,
                           size_hint_y=None, height=dp(52))
            b.bind(on_release=lambda _b, key=key: self.toggle(key))
            col.add_widget(b)
        rst = Btn("Wyzeruj postęp", fill=WHITE, shade=LINE, edge=LINE, fg=RED, size=15, size_hint_y=None,
                  height=dp(52))
        rst.bind(on_release=lambda *a: app.confirm("Wyzerować wszystko?", "Stracisz XP, korony i serię.",
                                                    "ANULUJ", "WYZERUJ", on_no=self.do_reset))
        col.add_widget(rst)
        col.add_widget(L("日本語 · %d działów · %d słów" % (len(UNITS), len(E.WORDS)), size=11,
                         color=MUTED, halign="center"))
        sv.add_widget(col)
        root.add_widget(sv)
        root.add_widget(NavBar(app, "profile"))
        self.add_widget(root)

    def shop_item(self, title, sub, cost, fn, enabled):
        row = BoxLayout(size_hint_y=None, height=dp(72), padding=[dp(14), dp(8)], spacing=dp(10))
        paint(row, WHITE, border=LINE, radius=dp(14))
        v = BoxLayout(orientation="vertical")
        for txt, sz, c in (("[b]%s[/b]" % title, 15, TEXT), (sub, 12, MUTED)):
            lb = L(txt, size=sz, color=c, wrap=False)
            lb.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
            v.add_widget(lb)
        row.add_widget(v)
        btn = Btn("◆ %d" % cost, fill=BLUE, size=15, size_hint=(None, None), width=dp(86), height=dp(48))
        btn.disabled = not enabled
        btn.bind(on_release=lambda *a: fn())
        row.add_widget(btn)
        return row

    def set_goal(self, xp):
        self.app.state.data["daily_goal"] = xp
        self.app.state.save()
        self.build()

    def buy_freeze(self):
        if self.app.state.buy_freeze():
            self.app.state.save()
            toast("Zamrożenie serii aktywne!", BLUE)
        self.build()

    def buy_refill(self):
        if self.app.state.buy_refill():
            self.app.state.save()
            toast("Serca uzupełnione!", RED)
        self.build()

    def toggle(self, key):
        s = self.app.state.data["settings"]
        s[key] = not s[key]
        self.app.state.save()
        self.build()

    def do_reset(self):
        self.app.state.reset()
        self.app.go_home()


# ---------------------------------------------------------------------------
# Rozmowy
# ---------------------------------------------------------------------------
def fit_label(text, size, maxw, color=TEXT, bold=False):
    lb = Label(text=text, font_size=sp(size), color=color, bold=bold, markup=True, size_hint=(None, None),
               halign="left")
    lb.text_size = (maxw, None)
    lb.texture_update()
    w = min(maxw, lb.texture_size[0])
    lb.text_size = (w + 1, None)
    lb.texture_update()
    lb.size = lb.texture_size
    return lb


class Avatar(Label):
    def __init__(self, char, color, d=dp(40), **kw):
        super().__init__(text=old(char, False), markup=True, font_size=d * 0.55, color=WHITE, size_hint=(None, None),
                         size=(d, d), **kw)
        with self.canvas.before:
            Color(*color)
            self._e = Ellipse()
        self.bind(pos=self._u, size=self._u)

    def _u(self, *_):
        self._e.pos, self._e.size = self.pos, self.size


AVATAR_COLORS = [hexc("#7A5A3A"), hexc("#83611F"), hexc("#9E2B25"), hexc("#4F6B3A"), hexc("#5E2750"),
                 hexc("#9E2B25"), hexc("#6F695F")]


class ButtonRow(ButtonBehavior, BoxLayout):
    pass


class ChatListScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="chats", **kw)
        self.app = app

    def on_pre_enter(self, *_):
        app, st = self.app, self.app.state
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")
        paint(root, BG, radius=0)
        top = TopBar(app)
        top.refresh("Rozmowy")
        root.add_widget(top)
        sv = ScrollView(do_scroll_x=False, bar_width=0)
        col = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(16), spacing=dp(12))
        col.bind(minimum_height=col.setter("height"))
        col.add_widget(L("Rozmowy ze słowami, które już znasz. Dotknij wiadomości, żeby zobaczyć "
                         "tłumaczenie. Przy błędzie dostaniesz wyjaśnienie i spróbujesz jeszcze raz.",
                         size=14, color=MUTED))
        for k, c in enumerate(CHATS):
            ok = st.chat_unlocked(c)
            row = ButtonRow(size_hint_y=None, height=dp(78), padding=[dp(14), dp(10)], spacing=dp(12))
            paint(row, WHITE, border=LINE, radius=dp(16))
            row.add_widget(Avatar(c["avatar"], AVATAR_COLORS[k % len(AVATAR_COLORS)] if ok else GRAY_BTN_D, d=dp(50)))
            v = BoxLayout(orientation="vertical")
            req = UNITS[E.unit_index(c["requires"])]["title"]
            sub = "z: %s" % c["partner"] if ok else "Odblokujesz po dziale: %s" % req
            for txt, sz, colr in (("[b]%s[/b]" % c["title"], 16, TEXT if ok else MUTED), (sub, 12, MUTED)):
                lb = L(txt, size=sz, color=colr, wrap=False)
                lb.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
                v.add_widget(lb)
            row.add_widget(v)
            stars = st.chat_stars(c["id"])
            row.add_widget(Label(text="".join("★" if i < stars else "☆" for i in range(3)),
                                 color=GOLD_D if stars else LINE, font_size=sp(18), size_hint_x=None, width=dp(66)))
            row.bind(on_release=lambda _r, c=c, ok=ok: self.open(c, ok))
            col.add_widget(row)
        sv.add_widget(col)
        root.add_widget(sv)
        root.add_widget(NavBar(app, "chats"))
        self.add_widget(root)

    def open(self, chat, ok):
        if not ok:
            toast("Ukończ poziom 1 działu „%s”, żeby odblokować tę rozmowę."
                  % UNITS[E.unit_index(chat["requires"])]["title"])
            return
        self.app.sm.current = "chatroom"
        self.app.chatroom.start(chat)


class ChatBubble(ButtonBehavior, BoxLayout):
    def __init__(self, tokens, meaning=None, mine=False, wrong=False, maxw=dp(260), **kw):
        super().__init__(orientation="vertical", size_hint=(None, None), padding=[dp(14), dp(10)], spacing=dp(3), **kw)
        self.meaning = meaning
        light = mine and not wrong
        self.labels = [fit_label(old_tokens(tokens, not light), 21, maxw, color=WHITE if light else TEXT),
                       fit_label("[i]%s[/i]" % esc(E.sentence_tr(tokens)), 12, maxw,
                                 color=WHITE if light else MUTED)]
        self.extra = None
        for lb in self.labels:
            self.add_widget(lb)
        self._resize()
        paint(self, (RED_L if wrong else BLUE) if mine else hexc("#E3DFD5"), radius=dp(18))

    def _resize(self):
        self.width = max(lb.width for lb in self.labels) + dp(28)
        self.height = sum(lb.height for lb in self.labels) + dp(20) + dp(3) * (len(self.labels) - 1)

    def on_release(self):
        if not self.meaning:
            return
        if self.extra is None:
            self.extra = fit_label(esc(self.meaning), 13, dp(260), color=hexc("#6F695F"))
            self.labels.append(self.extra)
            self.add_widget(self.extra)
        else:
            self.remove_widget(self.extra)
            self.labels.remove(self.extra)
            self.extra = None
        self._resize()


class AnchorBox(BoxLayout):
    def __init__(self, child, **kw):
        super().__init__(size_hint_x=None, width=child.width, **kw)
        self.fl = FloatLayout(size_hint=(None, None), size=child.size)
        self.fl.add_widget(child)
        self.child = child
        self.add_widget(self.fl)
        self.bind(pos=self._p)

    def _p(self, *_):
        self.fl.pos = self.pos
        self.child.pos = self.pos


class ChatRoomScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="chatroom", **kw)
        self.app = app
        root = BoxLayout(orientation="vertical")
        paint(root, BG, radius=0)
        top = BoxLayout(size_hint_y=None, height=dp(62), padding=[dp(8), dp(8), dp(16), dp(8)], spacing=dp(10))
        back = Btn("‹", fill=WHITE, shade=WHITE, fg=MUTED, size=34, size_hint_x=None, width=dp(40))
        back.depth = 0
        back.bind(on_release=lambda *a: setattr(app.sm, "current", "chats"))
        top.add_widget(back)
        self.avatar_box = BoxLayout(size_hint_x=None, width=dp(46), padding=[0, dp(2)])
        top.add_widget(self.avatar_box)
        self.name_lbl = L("", size=18, bold=True, wrap=False)
        self.name_lbl.bind(size=lambda *a: setattr(self.name_lbl, "text_size", self.name_lbl.size))
        top.add_widget(self.name_lbl)
        with top.canvas.after:
            Color(*LINE)
            ln = Rectangle()
        top.bind(pos=lambda *a: setattr(ln, "pos", top.pos), size=lambda *a: setattr(ln, "size", (top.width, dp(2))))
        root.add_widget(top)
        self.sv = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.log = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(12), spacing=dp(10))
        self.log.bind(minimum_height=self.log.setter("height"))
        self.sv.add_widget(self.log)
        root.add_widget(self.sv)
        self.reply = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(14), dp(12), dp(14), dp(16)],
                               spacing=dp(8))
        self.reply.bind(minimum_height=self.reply.setter("height"))
        with self.reply.canvas.before:
            Color(*hexc("#E3DFD5"))
            rbg = Rectangle()
            Color(*LINE)
            rln = Rectangle()

        def upd(*_):
            rbg.pos, rbg.size = self.reply.pos, self.reply.size
            rln.pos, rln.size = (self.reply.x, self.reply.top - dp(2)), (self.reply.width, dp(2))
        self.reply.bind(pos=upd, size=upd)
        root.add_widget(self.reply)
        self.add_widget(root)

    def start(self, chat):
        self.chat = chat
        self.turn = self.mistakes = self.attempts = 0
        self._excluded = set()
        self.color = AVATAR_COLORS[CHATS.index(chat) % len(AVATAR_COLORS)]
        self.avatar_box.clear_widgets()
        self.avatar_box.add_widget(Avatar(chat["avatar"], self.color, d=dp(42)))
        self.name_lbl.text = chat["partner"]
        self.log.clear_widgets()
        self.reply.clear_widgets()
        self.add_note("Dotknij wiadomości, żeby zobaczyć tłumaczenie.")
        self.bot_turn()

    def maxw(self):
        return min(dp(280), Window.width * 0.68)

    def scroll_end(self, *_):
        Clock.schedule_once(lambda dt: setattr(self.sv, "scroll_y", 0), 0.05)

    def add_row(self, widget, mine=False):
        row = BoxLayout(size_hint_y=None, spacing=dp(8))
        widget.bind(height=lambda w, h: setattr(row, "height", h))
        row.height = widget.height
        if mine:
            row.add_widget(Widget())
            row.add_widget(widget)
        else:
            row.add_widget(AnchorBox(Avatar(self.chat["avatar"], self.color, d=dp(32))))
            row.add_widget(widget)
            row.add_widget(Widget())
        self.log.add_widget(row)
        widget.opacity = 0
        Animation(opacity=1, d=0.2).start(widget)
        self.scroll_end()
        return row

    def add_note(self, text, color=MUTED, bg=None, prefix=""):
        box = BoxLayout(size_hint_y=None, padding=[dp(12), dp(8)])
        box.bind(minimum_height=box.setter("height"))
        if bg:
            paint(box, bg, radius=dp(12))
        box.add_widget(L(prefix + IntroEx._hook_markup(text), size=13, color=color, halign="center"))
        self.log.add_widget(box)
        self.scroll_end()

    def bot_turn(self):
        if self.turn >= len(self.chat["turns"]):
            self.finish()
            return
        t = self.chat["turns"][self.turn]
        self.reply.clear_widgets()
        typing = Label(text="...", font_size=sp(24), bold=True, color=MUTED, size_hint=(None, None), size=(dp(64), dp(40)))
        paint(typing, hexc("#E3DFD5"), radius=dp(18))
        row = self.add_row(typing)

        def show(dt):
            self.log.remove_widget(row)
            self.add_row(ChatBubble(t["bot"], t["en"], maxw=self.maxw()))
            if t.get("note"):
                self.add_note(t["note"])
            self.attempts = 0
            self.show_reply(t)
        Clock.schedule_once(show, 0.6 + 0.08 * len(t["bot"]))

    def show_reply(self, t):
        self.reply.clear_widgets()
        if "options" in t:
            self.reply.add_widget(L("[b]Wybierz odpowiedź[/b]", size=13, color=MUTED))
            opts = [o for o in t["options"] if tuple(o[0]) not in self._excluded]
            random.shuffle(opts)
            for toks, ok, why in opts:
                txt = "[size=%d]%s[/size]\n[size=%d][color=8D877C][i]%s[/i][/color][/size]" % (
                    sp(20), old_tokens(toks), sp(11), esc(E.sentence_tr(toks)))
                b = option_btn(txt, size_hint_y=None, height=dp(66))
                b.bind(on_release=lambda _b, o=(toks, ok, why): self.choose(*o))
                self.reply.add_widget(b)
        else:
            toks, pl = t["build"]
            self.reply.add_widget(L("[b]Powiedz:[/b] „%s”" % pl, size=15))
            self.answer = StackLayout(size_hint_y=None, spacing=dp(6), height=dp(58))
            self.answer.bind(minimum_height=lambda *a: setattr(self.answer, "height",
                                                               max(dp(58), self.answer.minimum_height)))
            paint(self.answer, WHITE, border=LINE, radius=dp(12))
            self.bank = StackLayout(size_hint_y=None, spacing=dp(6))
            self.bank.bind(minimum_height=self.bank.setter("height"))
            known = [h for h in self.app.state.learned_words() if not E.WORDS[h]["letter"] and h not in toks]
            random.shuffle(known)
            tiles = list(toks) + known[:2]
            random.shuffle(tiles)
            for tok in tiles:
                self.bank.add_widget(make_tile(tok, True, self._move))
            self.send_btn = Btn("WYŚLIJ", size_hint_y=None, height=dp(50))
            self.send_btn.bind(on_release=lambda *a: self.send(t))
            self.send_btn.disabled = True
            for w in (self.answer, self.bank, self.send_btn):
                self.reply.add_widget(w)

    def _move(self, b):
        self.app.sfx("tap")
        src, dst = (self.answer, self.bank) if b.parent is self.answer else (self.bank, self.answer)
        src.remove_widget(b)
        dst.add_widget(b)
        self.send_btn.disabled = not self.answer.children

    def send(self, t):
        given = [w.value for w in reversed(self.answer.children)]
        toks, _ = t["build"]
        ok = E.join(given) == E.join(toks)
        self.add_row(ChatBubble(given, mine=True, wrong=not ok, maxw=self.maxw()), mine=True)
        if ok:
            self.app.sfx("correct")
            self.next_turn()
            return
        self.app.sfx("wrong")
        self.mistakes += 1
        self.attempts += 1
        why = E.explain_mistake(given, toks) or "Nie całkiem. Sprawdź szyk."
        if self.attempts >= 2:
            why += "\nOdpowiedź: %s" % E.join(toks)
        self.confused(why)
        Clock.schedule_once(lambda dt: self.show_reply(t), 1.0)

    def choose(self, toks, ok, why):
        t = self.chat["turns"][self.turn]
        self.add_row(ChatBubble(toks, mine=True, wrong=not ok, maxw=self.maxw()), mine=True)
        self.reply.clear_widgets()
        if ok:
            self.app.sfx("correct")
            self.next_turn()
            return
        self.app.sfx("wrong")
        self.mistakes += 1
        self.confused(why)
        self._excluded.add(tuple(toks))
        Clock.schedule_once(lambda dt: self.show_reply(t), 1.0)

    def confused(self, why):
        self.add_row(ChatBubble(["?"], maxw=self.maxw()))
        self.add_note(why, color=TEXT, bg=PURPLE_L, prefix="[b][color=5E2750]Pomyśl:[/color][/b] ")

    def next_turn(self):
        self._excluded = set()
        self.turn += 1
        self.reply.clear_widgets()
        Clock.schedule_once(lambda dt: self.bot_turn(), 0.5)

    def finish(self):
        had_full = self.app.state.hearts() >= E.HEART_MAX
        ev = self.app.state.finish_chat(self.chat, self.mistakes)
        self.app.sfx("complete")
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(16), spacing=dp(6))
        card.bind(minimum_height=card.setter("height"))
        paint(card, YELLOW_L, radius=dp(16))
        card.add_widget(L("[b]Rozmowa ukończona![/b]", size=18, halign="center"))
        card.add_widget(L("[color=83611F]%s[/color]" % "".join("★" if i < ev["stars"] else "☆" for i in range(3)),
                          size=30, halign="center"))
        extra = "" if had_full else "  ·  [color=9E2B25]♥[/color] +1"
        card.add_widget(L("+%d XP  ·  ◆ +%d%s" % (ev["xp"], ev["gems"], extra), size=15, halign="center"))
        if ev["streak_extended"]:
            card.add_widget(L("[color=9E2B25][b]☀ Seria: %d dni![/b][/color]" % ev["streak"], size=15, halign="center"))
        self.log.add_widget(card)
        self.scroll_end()
        self.reply.clear_widgets()
        b = Btn("WRÓĆ DO ROZMÓW", size_hint_y=None, height=dp(52))
        b.bind(on_release=lambda *a: setattr(self.app.sm, "current", "chats"))
        again = Btn("JESZCZE RAZ", fill=WHITE, shade=LINE, edge=LINE, fg=BLUE, size_hint_y=None, height=dp(48))
        again.bind(on_release=lambda *a: self.start(self.chat))
        self.reply.add_widget(b)
        self.reply.add_widget(again)


# ---------------------------------------------------------------------------
# Powitanie
# ---------------------------------------------------------------------------
class WelcomeScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="welcome", **kw)
        self.app = app
        self.goal = 20
        root = BoxLayout(orientation="vertical", padding=[dp(24), dp(44), dp(24), dp(24)], spacing=dp(14))
        paint(root, BG, radius=0)
        root.add_widget(Initial("日", size_hint_y=None, height=dp(126)))
        root.add_widget(L("日本語", size=30, bold=True, halign="center"))
        root.add_widget(L("Japoński ma prostą wymowę i logiczną gramatykę: czasownik na końcu, cząstki zamiast końcówek. Słowa, zdania i rozmowy od pierwszego dnia.",
                          size=16, color=MUTED, halign="center"))
        root.add_widget(spacer(dp(4)))
        root.add_widget(L("Wybierz cel dnia", size=18, bold=True))
        self.goal_btns = []
        for name, xp in E.GOALS:
            b = option_btn("[b]%s[/b]   %d XP dziennie" % (name, xp), size=16, size_hint_y=None, height=dp(54))
            b.xp = xp
            b.bind(on_release=self.pick)
            root.add_widget(b)
            self.goal_btns.append(b)
            if xp == self.goal:
                select_style(b, True)
        root.add_widget(Widget())
        go = Btn("ZACZYNAMY", size_hint_y=None, height=dp(56))
        go.bind(on_release=self.go)
        root.add_widget(go)
        self.add_widget(root)

    def pick(self, b):
        self.goal = b.xp
        for x in self.goal_btns:
            select_style(x, x is b)

    def go(self, *_):
        st = self.app.state
        st.data["daily_goal"] = self.goal
        st.data["onboarded"] = True
        st.save()
        self.app.go_home()


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------
class NihonApp(object):
    """Kurs uruchamiany wewnątrz Śviętovita (dawniej osobna aplikacja)."""

    def __init__(self, hub, data_dir):
        self.hub, self.user_data_dir = hub, data_dir

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        self.state = E.State(os.path.join(self.user_data_dir, "postep.json"))
        self.sounds = {}
        try:
            for k, p in generate_sounds(os.path.join(self.user_data_dir, "sounds")).items():
                s = SoundLoader.load(p)
                if s:
                    self.sounds[k] = s
        except Exception as e:  # pragma: no cover
            print("dźwięki niedostępne:", e)
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        self.home = HomeScreen(self)
        self.lesson = LessonScreen(self)
        self.results = ResultsScreen(self)
        self.profile = ProfileScreen(self)
        self.chats = ChatListScreen(self)
        self.chatroom = ChatRoomScreen(self)
        for s in (WelcomeScreen(self), self.home, self.lesson, self.results, self.profile, self.chats, self.chatroom):
            self.sm.add_widget(s)
        res = self.state.check_streak()
        self.state.save()
        self.sm.current = "home" if self.state.data["onboarded"] else "welcome"
        if res == "frozen":
            Clock.schedule_once(lambda dt: toast("Zamrożenie uratowało twoją serię!", BLUE, 3), 0.8)
        elif res == "lost":
            Clock.schedule_once(lambda dt: toast("Seria się skończyła. Zacznij nową dzisiaj!", ORANGE, 3), 0.8)
        return self.sm

    def sfx(self, name):
        if not self.state.data["settings"]["sound"]:
            return
        s = self.sounds.get(name)
        if s:
            s.stop()
            s.play()

    def confirm(self, title, text, yes, no, on_no):
        mv = ModalView(size_hint=(0.86, None), height=dp(270), background_color=(0, 0, 0, 0.5))
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
        paint(box, WHITE, radius=dp(20))
        box.add_widget(L(title, size=21, bold=True, halign="center"))
        box.add_widget(L(text, size=15, color=MUTED, halign="center"))
        box.add_widget(Widget())
        b1 = Btn(yes, fill=BLUE, size_hint_y=None, height=dp(52))
        b1.bind(on_release=lambda *a: mv.dismiss())
        b2 = Btn(no, fill=WHITE, shade=WHITE, fg=RED, size_hint_y=None, height=dp(44))
        b2.bind(on_release=lambda *a: (mv.dismiss(), on_no()))
        box.add_widget(b1)
        box.add_widget(b2)
        mv.add_widget(box)
        mv.open()

    def on_key(self, window, key, *args):
        if key == 27:
            cur = self.sm.current
            if cur == "lesson":
                self.lesson.ask_quit()
                return True
            if cur in ("profile", "results", "chats"):
                self.go_home()
                return True
            if cur == "chatroom":
                self.sm.current = "chats"
                return True
        return False

    def go_home(self):
        self.sm.current = "home"
        self.home.refresh()

    def nav(self, key):
        if key == "home":
            self.go_home()
        elif key == "profile":
            self.sm.current = "profile"
        elif key == "chats":
            self.sm.current = "chats"
        elif key == "sounds":
            self.sm.current = "lesson"
            self.lesson.start(E.Session(E.make_sound_training(self.state), "sounds", hearts=False), level=1)
        elif key == "practice":
            self.start_practice()

    def open_unit(self, idx):
        st = self.state
        u = UNITS[idx]
        if not st.unlocked(idx):
            toast("Ukończ poziom 1 działu „%s”, żeby to odblokować." % st.unlock_reason(idx))
            return
        crowns, lessons = st.crowns(u["id"]), st.lessons(u["id"])
        mv = ModalView(size_hint=(0.9, None), height=dp(430), background_color=(0.17, 0.12, 0.08, 0.45))
        box = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(10))
        paint(box, WHITE, radius=dp(3), border=GOLD, border_w=dp(2))
        head = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(14))
        ini = Label(text=old(u["icon"], False), markup=True, font_size=sp(30 if len(u["icon"]) == 1 else 18),
                    color=WHITE, size_hint=(None, None), size=(dp(60), dp(60)))
        paint(ini, RED, radius=dp(2), border=GOLD, border_w=dp(2))
        head.add_widget(ini)
        tl = L("[b]%s[/b]\n[size=%d][color=8D877C]%s[/color][/size]" % (
            u["title"], sp(13), "Wszystkie poziomy ukończone" if crowns >= E.MAX_CROWNS else
            "Poziom %d  ·  lekcja %d z %d" % (crowns + 1, lessons + 1, E.LESSONS_PER_LEVEL)), size=22, wrap=False)
        tl.bind(size=lambda *a: setattr(tl, "text_size", tl.size))
        head.add_widget(tl)
        box.add_widget(head)
        box.add_widget(L("[color=9E2B25]%s[/color]" % "".join("●" if i < crowns else "○" for i in range(E.MAX_CROWNS)),
                         size=18))
        preview = "  ".join(E.WORDS[h]["form"] for h in E.unit_items(idx))
        box.add_widget(L(old(preview), size=20))
        box.add_widget(Widget())
        go = Btn("START  +10 XP" if crowns < E.MAX_CROWNS else "POWTÓRKA  +10 XP", fill=RED,
                 size_hint_y=None, height=dp(54))
        go.bind(on_release=lambda *a: (mv.dismiss(), self.start_lesson(idx)))
        box.add_widget(go)
        mv.add_widget(box)
        mv.open()

    def start_lesson(self, idx):
        if self.state.hearts() <= 0:
            self.lesson.out_of_hearts(on_refill=lambda: self.start_lesson(idx))
            return
        s = E.Session(E.make_lesson(self.state, idx), "lesson", idx, hearts=True)
        self.sm.current = "lesson"
        self.lesson.start(s, level=self.state.crowns(UNITS[idx]["id"]))

    def start_practice(self):
        exs = E.make_practice(self.state)
        if not exs:
            toast("Ukończ pierwszą lekcję, żeby odblokować powtórkę.")
            return
        self.sm.current = "lesson"
        self.lesson.start(E.Session(exs, "practice", hearts=False), level=2)

    def finish_session(self, s):
        ev = self.state.finish(s)
        self.sfx("complete")
        self.results.show(ev, s)
        self.sm.current = "results"

    def on_pause(self):
        self.state.save()
        return True

    def on_stop(self):
        self.state.save()

