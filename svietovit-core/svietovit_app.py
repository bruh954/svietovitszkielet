"""Śviętovit: sześć kursów języków w jednej aplikacji na Androida (Kivy).

Na komputerze:  python main.py
Na Androida:    buildozer android debug   (zob. README.md)
"""
import datetime as dt
import importlib
import json
import math
import os
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.config import Config
from kivy.utils import platform

Config.set("kivy", "exit_on_escape", "0")
if platform not in ("android", "ios"):
    Config.set("graphics", "width", "412")
    Config.set("graphics", "height", "860")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc

from courses import common as C

HERE = os.path.dirname(os.path.abspath(__file__))

# Paleta Arkony: noc, dębowe drewno, złoto, kość.
NIGHT = hexc("#16171B")
CARD = hexc("#212228")
CARD_P = hexc("#2A2B32")
BONE = hexc("#EDE5D3")
MUTED = hexc("#8E8878")
GOLD = hexc("#C9A24A")
GOLD_D = hexc("#8D7233")
RULE = hexc("#34353C")

LANGS = ("pl", "en")
TXT = {
    "pl": {"motto": "szkoła języków dawnych i dalekich", "xp": "XP łącznie", "streak": "najdłuższa seria",
           "levels": "poziomy", "new": "nowy", "learn_in": "Uczę się po",
           "foot": "W każdym kursie mrugające ꙮ na górze wraca tutaj.",
           "reports": "Zgłoszone błędy: %d", "copy": "SKOPIUJ", "clear": "WYCZYŚĆ",
           "copied": "Skopiowano. Wklej zgłoszenia w rozmowie z Claude'em.",
           "rep_title": "Zgłoś błąd w ćwiczeniu", "rep_hint": "Opis (nie musisz nic pisać)", "rep_send": "ZAPISZ",
           "rep_cancel": "ANULUJ", "rep_saved": "Dziękuję! Zgłoszenie zapisane. Skopiujesz je na ekranie głównym.",
           "how": "Chorągiewka na pasku lekcji zapisuje zgłoszenie błędu."},
    "en": {"motto": "a school of ancient and faraway languages", "xp": "total XP", "streak": "best streak",
           "levels": "levels", "new": "new", "learn_in": "I learn in",
           "foot": "In every course, the blinking ꙮ at the top brings you back here.",
           "reports": "Reported mistakes: %d", "copy": "COPY", "clear": "CLEAR",
           "copied": "Copied. Paste the reports into your chat with Claude.",
           "rep_title": "Report a mistake in this exercise", "rep_hint": "Description (optional)", "rep_send": "SAVE",
           "rep_cancel": "CANCEL", "rep_saved": "Thank you! Report saved. You can copy it on the main screen.",
           "how": "The flag on the lesson bar saves a mistake report."},
}


def _f(course, *parts):
    return os.path.join(HERE, "courses", course, "fonts", *parts)


def _serif(course):
    return (_f(course, "UI-Serif.ttf"), _f(course, "UI-SerifBold.ttf"))


# Nazwy języków w nich samych. Każdy kurs ma własny krój podstawowy („Roboto”), podmieniany przy wejściu.
COURSES = [
    dict(id="hanzi_hero", cls="HanziHeroApp", src="en", native="中文", native_font=_f("hanzi_hero", "HanziSerif-Regular.ttf"),
         sub={"pl": "znaki, tony, idiomy, chiński klasyczny", "en": "characters, tones, idioms, Classical Chinese"},
         glyph="汉", size=34, paper="#F2EADB", accent="#B8352A", save="progress.json",
         roboto=(_f("hanzi_hero", "HanziSerif-Regular.ttf"), _f("hanzi_hero", "HanziSerif-Bold.ttf"))),
    dict(id="glagol", cls="GlagolApp", src="pl", native="Словѣньскъ ѩзыкъ", native_font=_f("glagol", "Old-Regular.ttf"),
         sub={"pl": "cyrylica i głagolica, Ewangelia", "en": "Cyrillic and Glagolitic, the Gospel"},
         glyph="Ⰳ", size=36, paper="#EFE2C6", accent="#A8321E", save="postep.json", roboto=_serif("glagol")),
    dict(id="ave", cls="AveApp", src="pl", native="Lingua Latina", native_font=_f("ave", "UI-Serif.ttf"),
         sub={"pl": "trzy wymowy, końcówki, sentencje", "en": "three pronunciations, endings, sayings"},
         glyph="A", size=36, paper="#ECE8DF", accent="#9E2B25", save="postep.json", roboto=_serif("ave")),
    dict(id="logos", cls="LogosApp", src="pl", native="Ἑλληνικὴ γλῶσσα", native_font=_f("logos", "UI-Serif.ttf"),
         sub={"pl": "pismo politoniczne, maksymy, Ewangelia", "en": "polytonic script, maxims, the Gospel"},
         glyph="Λ", size=36, paper="#F1E2CC", accent="#B5532D", save="postep.json", roboto=_serif("logos")),
    dict(id="abba", cls="AbbaApp", src="pl", native="ܠܫܢܐ ܐܪܡܝܐ", native_font=_f("abba", "Syr.ttf"),
         sub={"pl": "pismo syryjskie, Peszitta, Daniel", "en": "Syriac script, Peshitta, Daniel"},
         glyph="ܐ", size=36, paper="#EEE3CF", accent="#1F7A78", save="postep.json", roboto=_serif("abba")),
    dict(id="kaszeby", cls="KaszebyApp", src="pl", native="Kaszëbsczi jãzëk", native_font=_f("kaszeby", "UI-Serif.ttf"),
         sub={"pl": "nowe litery, kaszubienie, rozmowy", "en": "new letters, sound rules, conversations"},
         glyph="Ò", size=36, paper="#EEF0EA", accent="#1C4F8A", save="postep.json", roboto=_serif("kaszeby")),
    dict(id="hangeul", cls="HangeulApp", src="pl", native="한국어", native_font=_f("hangeul", "HangeulSerif-Regular.ttf"),
         sub={"pl": "hangul, słowa, rozmowy", "en": "Hangul, words, conversations"},
         glyph="한", size=36, paper="#F2EEE4", accent="#1C4F8A", save="postep.json",
         roboto=(_f("hangeul", "HangeulSerif-Regular.ttf"), _f("hangeul", "HangeulSerif-Bold.ttf"))),
    dict(id="han", cls="HanApp", src="pl", native="汉字", native_font=_f("han", "HanSerif-Regular.ttf"),
         sub={"pl": "kreski, składniki, pierwsze znaki", "en": "strokes, components, first characters"},
         glyph="字", size=36, paper="#F0E6D8", accent="#8C3B1E", save="postep.json",
         roboto=(_f("han", "HanSerif-Regular.ttf"), _f("han", "HanSerif-Bold.ttf"))),
    dict(id="kana", cls="KanaApp", src="pl", native="かな・漢字", native_font=_f("kana", "KanaSerif-Regular.ttf"),
         sub={"pl": "hiragana, katakana, kanji", "en": "hiragana, katakana, kanji"},
         glyph="あ", size=36, paper="#F4E8EA", accent="#A83257", save="postep.json",
         roboto=(_f("kana", "KanaSerif-Regular.ttf"), _f("kana", "KanaSerif-Bold.ttf"))),
    dict(id="nihon", cls="NihonApp", src="pl", native="日本語", native_font=_f("nihon", "NihonSerif-Regular.ttf"),
         sub={"pl": "słowa, zdania, rozmowy", "en": "words, sentences, conversations"},
         glyph="日", size=36, paper="#F3EAE4", accent="#B3261E", save="postep.json",
         roboto=(_f("nihon", "NihonSerif-Regular.ttf"), _f("nihon", "NihonSerif-Bold.ttf"))),
]
COURSES = [c for c in COURSES if c["id"] == "nihon"]  # wersja szkieletowa: jeden kurs
BY_ID = {c["id"]: c for c in COURSES}



def use_roboto(regular, bold):
    LabelBase.register(name="Roboto", fn_regular=regular, fn_bold=bold)


def use_hub_fonts():
    use_roboto(C.SVIET_REG, C.SVIET_BOLD)


def T(text, size=15, color=BONE, bold=False, halign="left", **kw):
    lbl = Label(text=text, markup=True, font_size=sp(size), color=color, bold=bold, halign=halign,
                valign="middle", size_hint_y=None, **kw)

    def fit(*_):
        lbl.text_size = (lbl.width, None)
        lbl.texture_update()
        lbl.height = lbl.texture_size[1]
    lbl.bind(width=fit, text=fit)
    fit()
    return lbl


# ---------------------------------------------------------------------------
# Widżety ekranu wyboru
# ---------------------------------------------------------------------------
class Emblem(Widget):
    """Duże, mrugające ꙮ w złotym kręgu."""

    def __init__(self, **kw):
        super().__init__(size_hint_y=None, height=dp(176), **kw)
        self.oko = C.Oko(color=list(GOLD), size_hint=(None, None))
        self.add_widget(self.oko)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        cx, cy = self.center_x, self.center_y
        self.oko.size = (dp(104), dp(116))
        self.oko.center = (cx, cy)
        self.oko._draw()
        Clock.schedule_once(lambda dt: self.oko._draw(), 0)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*GOLD[:3], 0.08)
            Ellipse(pos=(cx - dp(80), cy - dp(80)), size=(dp(160), dp(160)))
            Color(*GOLD_D)
            Line(circle=(cx, cy, dp(80)), width=dp(1))
            Color(*GOLD)
            r = dp(80)
            for i in range(28):
                a = 2 * math.pi * i / 28
                s = dp(2.6) if i % 7 == 0 else dp(1.3)
                Ellipse(pos=(cx + r * math.cos(a) - s, cy + r * math.sin(a) - s), size=(2 * s, 2 * s))


class Stat(BoxLayout):
    def __init__(self, label, **kw):
        super().__init__(orientation="vertical", **kw)
        self.value = Label(text="0", font_size=sp(22), bold=True, color=BONE, size_hint_y=None, height=dp(28))
        self.add_widget(self.value)
        self.label = Label(text=label, font_size=sp(11), color=MUTED, size_hint_y=None, height=dp(16))
        self.add_widget(self.label)


class LangChip(ButtonBehavior, Label):
    def __init__(self, code, **kw):
        super().__init__(text=code.upper(), font_size=sp(13), bold=True, size_hint=(None, None),
                         size=(dp(42), dp(28)), **kw)
        self.code, self.on = code, False
        self.bind(pos=self._draw, size=self._draw, state=self._draw)

    def set_on(self, on):
        self.on = on
        self.color = NIGHT if on else MUTED
        self._draw()

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.on:
                Color(*GOLD)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            else:
                Color(*GOLD_D)
                Line(rounded_rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2, dp(14)), width=1)


class CourseCard(ButtonBehavior, BoxLayout):
    def __init__(self, info, lang, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(104),
                         padding=[dp(14), dp(14), dp(16), dp(14)], spacing=dp(14), **kw)
        self.info, self.lang = info, lang
        self.accent, self.paper = hexc(info["accent"]), hexc(info["paper"])
        self.seal = Label(text=info["glyph"], font_name=info["native_font"], font_size=sp(info["size"]),
                          color=self.accent, size_hint=(None, None), size=(dp(68), dp(68)))
        sb = BoxLayout(size_hint_x=None, width=dp(68))
        sb.add_widget(self.seal)
        self.add_widget(sb)
        col = BoxLayout(orientation="vertical", spacing=dp(4))
        self.title = T(info["native"], size=19, font_name=info["native_font"])
        self.subtitle = T(info["sub"][lang], size=12, color=MUTED)
        self.meta = T("", size=12, color=MUTED)
        col.add_widget(Widget())
        for w in (self.title, self.subtitle, self.meta):
            col.add_widget(w)
        col.add_widget(Widget())
        self.add_widget(col)
        self.arrow = Label(text="›", font_size=sp(30), color=MUTED, size_hint_x=None, width=dp(14))
        self.add_widget(self.arrow)
        self.progress = 0.0
        self._trig = Clock.create_trigger(self._draw)
        self.bind(pos=lambda *a: self._trig(), size=lambda *a: self._trig(), state=lambda *a: self._trig())
        sb.bind(pos=lambda *a: self._trig(), size=lambda *a: self._trig())

    def set_stats(self, crowns, total, xp, streak, last=False):
        self.progress = crowns / total if total else 0
        parts = []
        if xp:
            parts.append("[color=C9A24A]★[/color] %d XP" % xp)
        if streak:
            parts.append("[color=C9A24A]☀[/color] %d" % streak)
        parts.append("%d%%" % round(100 * self.progress) if xp else TXT[self.lang]["new"])
        self.meta.text = "  ·  ".join(parts)
        self.arrow.color = GOLD if last else MUTED
        self._trig()

    def _draw(self, *_):
        s = self.seal
        sx, sy = s.parent.center_x - dp(34), s.parent.center_y - dp(34)
        s.pos = (sx, sy)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*(CARD_P if self.state == "down" else CARD))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*self.paper)
            RoundedRectangle(pos=(sx, sy), size=(dp(68), dp(68)), radius=[dp(4)])
            Color(*self.accent)
            Line(rounded_rectangle=(sx + dp(4), sy + dp(4), dp(60), dp(60), dp(2)), width=dp(0.8))
            Color(*RULE)
            Rectangle(pos=(self.x + dp(96), self.y + dp(10)), size=(self.width - dp(126), dp(3)))
            Color(*self.accent[:3], 1)
            Rectangle(pos=(self.x + dp(96), self.y + dp(10)), size=((self.width - dp(126)) * self.progress, dp(3)))


class HubScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="hub", **kw)
        self.app = app
        self.build()

    def build(self):
        self.clear_widgets()
        app, lang = self.app, self.app.lang
        tx = TXT[lang]
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        col = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(16), dp(14), dp(16), dp(26)],
                        spacing=dp(10))
        col.bind(minimum_height=col.setter("height"))
        bar = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        bar.add_widget(Widget())
        bar.add_widget(Label(text=tx["learn_in"], font_size=sp(12), color=MUTED, size_hint_x=None, width=dp(86),
                             halign="right", valign="middle", text_size=(dp(86), dp(30))))
        self.chips = []
        for code in LANGS:
            chip = LangChip(code)
            chip.set_on(code == lang)
            chip.bind(on_release=lambda c: app.set_lang(c.code))
            self.chips.append(chip)
            bar.add_widget(chip)
        col.add_widget(bar)
        col.add_widget(Emblem())
        col.add_widget(T("[b]Śviętovit[/b]", size=34, halign="center"))
        col.add_widget(T(tx["motto"], size=14, color=MUTED, halign="center"))
        stats = BoxLayout(size_hint_y=None, height=dp(70), padding=[0, dp(14), 0, dp(6)])
        self.s_xp, self.s_streak, self.s_levels = Stat(tx["xp"]), Stat(tx["streak"]), Stat(tx["levels"])
        for w in (self.s_xp, self.s_streak, self.s_levels):
            stats.add_widget(w)
        col.add_widget(stats)
        col.add_widget(self._rule())
        self.cards = []
        for info in COURSES:
            card = CourseCard(info, lang)
            card.bind(on_release=lambda c: app.open_course(c.info["id"]))
            self.cards.append(card)
            col.add_widget(card)
        col.add_widget(Widget(size_hint_y=None, height=dp(8)))
        self.rep_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        self.rep_box.bind(minimum_height=self.rep_box.setter("height"))
        col.add_widget(self.rep_box)
        col.add_widget(T(tx["foot"].replace("ꙮ", "[font=Sviet]ꙮ[/font]"), size=12, color=MUTED, halign="center"))
        scroll.add_widget(col)
        self.add_widget(scroll)

    def _rule(self):
        w = Widget(size_hint_y=None, height=dp(18))

        def draw(*_):
            w.canvas.clear()
            with w.canvas:
                Color(*GOLD_D)
                Rectangle(pos=(w.x + dp(30), w.center_y), size=(w.width - dp(60), dp(0.8)))
                Color(*GOLD)
                for k in (-1, 0, 1):
                    Ellipse(pos=(w.center_x + k * dp(12) - dp(2.5), w.center_y - dp(2.1)), size=(dp(5), dp(5)))
        w.bind(pos=draw, size=draw)
        return w

    def refresh(self):
        xp_all = crowns_all = total_all = best = 0
        last = self.app.settings.get("last")
        for card in self.cards:
            cid = card.info["id"]
            st, E = self.app.course_state(cid)
            d = st.data
            total = len(E.UNITS) * E.MAX_CROWNS
            crowns = sum(min(E.MAX_CROWNS, st.crowns(u["id"])) for u in E.UNITS)
            streak = d["streak"] if d.get("last_goal_day") in (
                st.today().isoformat(), (st.today() - dt.timedelta(days=1)).isoformat()) else 0
            card.set_stats(crowns, total, d["xp_total"], streak, last == cid)
            xp_all += d["xp_total"]
            crowns_all += crowns
            total_all += total
            best = max(best, streak)
        self.s_xp.value.text = str(xp_all)
        self.s_streak.value.text = str(best)
        self.s_levels.value.text = "%d/%d" % (crowns_all, total_all)
        self.show_reports()

    def show_reports(self):
        tx = TXT[self.app.lang]
        reps = self.app.settings.get("reports", [])
        self.rep_box.clear_widgets()
        if not reps:
            self.rep_box.add_widget(T(tx["how"], size=12, color=MUTED, halign="center"))
            return
        self.rep_box.add_widget(T(tx["reports"] % len(reps), size=15, halign="center", bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10), padding=[dp(30), 0])
        for key, fn in (("copy", self.app.copy_reports), ("clear", self.app.clear_reports)):
            b = LangChip(tx[key])
            b.text = tx[key]
            b.size_hint = (1, 1)
            b.set_on(key == "copy")
            b.bind(on_release=lambda *a, f=fn: f())
            row.add_widget(b)
        self.rep_box.add_widget(row)


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------
class SvietovitApp(App):
    title = "Śviętovit"
    icon = "icon.png"

    def build(self):
        try:
            return self._build()
        except Exception:
            return crash_view(traceback.format_exc(), self)

    def _build(self):
        use_hub_fonts()
        Window.clearcolor = NIGHT
        Window.softinput_mode = "below_target"
        self.settings_path = os.path.join(self.user_data_dir, "svietovit.json")
        try:
            with open(self.settings_path, encoding="utf-8") as f:
                self.settings = json.load(f)
        except (OSError, ValueError):
            self.settings = {}
        self.lang = self.settings.get("lang", "pl")
        if self.lang not in LANGS:
            self.lang = "pl"
        self.engines, self.states, self.courses = {}, {}, {}
        self.active = None
        self.sm = ScreenManager(transition=FadeTransition(duration=0.18))
        self.hub = HubScreen(self)
        self.sm.add_widget(self.hub)
        self.hub.refresh()
        Window.bind(on_keyboard=self.on_key)
        return self.sm

    # -- dane kursów ---------------------------------------------------------
    def suffix(self, cid):
        return "" if BY_ID[cid]["src"] == self.lang else "_" + self.lang

    def data_dir(self, cid):
        d = os.path.join(self.user_data_dir, cid)
        os.makedirs(d, exist_ok=True)
        return d

    def course_state(self, cid):
        if cid not in self.engines:
            self.engines[cid] = importlib.import_module("courses.%s.engine%s" % (cid, self.suffix(cid)))
        E = self.engines[cid]
        if cid in self.courses:
            return self.courses[cid].state, E
        if cid not in self.states:
            self.states[cid] = E.State(os.path.join(self.data_dir(cid), BY_ID[cid]["save"]))
        return self.states[cid], E

    def save_settings(self):
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f)
        except OSError:
            pass

    # -- język nauki ---------------------------------------------------------
    def set_lang(self, lang):
        if lang == self.lang:
            return
        for cid, ctrl in list(self.courses.items()):
            ctrl.state.save()
            scr = self.sm.get_screen("c_" + cid)
            self.sm.remove_widget(scr)
        self.courses, self.engines, self.states = {}, {}, {}
        self.lang = self.settings["lang"] = lang
        self.save_settings()
        use_hub_fonts()
        self.hub.build()
        self.hub.refresh()

    # -- zgłoszenia błędów ---------------------------------------------------
    def report_mistake(self, ctrl, data):
        """Okienko z opcjonalnym opisem; zgłoszenie zapisuje się przyciskiem ZAPISZ (opis może zostać pusty)."""
        from kivy.uix.modalview import ModalView
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        tx = TXT[self.lang]
        cid = next((k for k, v in self.courses.items() if v is ctrl), self.active)
        data = dict(data, kurs=cid, jezyk=self.lang, czas=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
        mv = ModalView(size_hint=(0.9, None), height=dp(300), auto_dismiss=True, background_color=(0, 0, 0, 0.6))
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        with box.canvas.before:
            Color(*CARD)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(16)])
        box.bind(pos=lambda w, v: setattr(bg, "pos", v), size=lambda w, v: setattr(bg, "size", v))
        box.add_widget(T(tx["rep_title"], size=17, bold=True, halign="center"))
        ti = TextInput(hint_text=tx["rep_hint"], multiline=True, font_size=sp(15), write_tab=False,
                       background_color=(0.93, 0.9, 0.83, 1), foreground_color=(0.09, 0.09, 0.11, 1),
                       hint_text_color=(0.4, 0.4, 0.4, 1), padding=(dp(10), dp(10)))
        box.add_widget(ti)
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))

        def save(*_):
            note = ti.text.strip()
            if note:
                data["opis"] = note
            self.settings.setdefault("reports", []).append(data)
            self.save_settings()
            mv.dismiss()
            self.hub_note(tx["rep_saved"])

        for key, fn in (("rep_cancel", lambda *_: mv.dismiss()), ("rep_send", save)):
            b = Button(text=tx[key], font_size=sp(14), bold=True, background_normal="", background_down="",
                       background_color=GOLD if key == "rep_send" else CARD_P,
                       color=NIGHT if key == "rep_send" else BONE)
            b.bind(on_release=fn)
            row.add_widget(b)
        box.add_widget(row)
        mv.add_widget(box)
        mv.open()
        Clock.schedule_once(lambda dt_: setattr(ti, "focus", True), 0.2)

    def copy_reports(self):
        from kivy.core.clipboard import Clipboard
        reps = self.settings.get("reports", [])
        lines = ["Śviętovit: zgłoszone błędy (%d)" % len(reps)]
        for i, r in enumerate(reps, 1):
            lines.append("\n#%d %s" % (i, json.dumps(r, ensure_ascii=False, default=str)))
        Clipboard.copy("\n".join(lines))
        self.hub_note(TXT[self.lang]["copied"])

    def clear_reports(self):
        self.settings["reports"] = []
        self.save_settings()
        self.hub.show_reports()

    def hub_note(self, text):
        from kivy.animation import Animation
        lbl = Label(text=text, font_size=sp(14), color=NIGHT, size_hint=(None, None), halign="center")
        lbl.text_size = (min(Window.width - dp(60), dp(320)), None)
        lbl.texture_update()
        lbl.size = (lbl.texture_size[0] + dp(28), lbl.texture_size[1] + dp(18))
        with lbl.canvas.before:
            Color(*GOLD)
            rr = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[dp(12)])
        lbl.bind(pos=lambda *a: setattr(rr, "pos", lbl.pos))
        lbl.pos = ((Window.width - lbl.width) / 2, Window.height * 0.12)
        Window.add_widget(lbl)
        anim = Animation(d=2.6) + Animation(opacity=0, d=0.3)
        anim.bind(on_complete=lambda *a: Window.remove_widget(lbl))
        anim.start(lbl)

    # -- przełączanie --------------------------------------------------------
    def open_course(self, cid):
        info = BY_ID[cid]
        use_roboto(*info["roboto"])
        if cid not in self.courses:
            mod = importlib.import_module("courses.%s.ui%s" % (cid, self.suffix(cid)))
            use_roboto(*info["roboto"])
            ctrl = getattr(mod, info["cls"])(self, self.data_dir(cid))
            scr = Screen(name="c_" + cid)
            scr.add_widget(ctrl.build())
            self.sm.add_widget(scr)
            ctrl.module = mod
            self.courses[cid] = ctrl
        else:
            ctrl = self.courses[cid]
            Window.clearcolor = ctrl.module.BG
            if ctrl.sm.current == "home":
                ctrl.home.refresh()
        self.active = cid
        self.settings["last"] = cid
        self.save_settings()
        self.sm.current = "c_" + cid

    def show_hub(self):
        if self.active:
            self.courses[self.active].state.save()
        self.active = None
        use_hub_fonts()
        Window.clearcolor = NIGHT
        self.hub.refresh()
        self.sm.current = "hub"

    def on_key(self, window, key, *args):
        if self.active is None:
            return False
        ctrl = self.courses[self.active]
        if ctrl.on_key(window, key, *args):
            return True
        if key == 27:
            self.show_hub()
            return True
        return False

    def on_pause(self):
        for ctrl in getattr(self, "courses", {}).values():
            ctrl.state.save()
        return True

    def on_resume(self):
        if getattr(self, "active", 0) is None:
            self.hub.refresh()

    def on_stop(self):
        for ctrl in getattr(self, "courses", {}).values():
            ctrl.state.save()


def crash_view(tb, app=None):
    """Zamiast cichego zamknięcia pokazuje błąd na ekranie i zapisuje go do pliku crash.log."""
    try:
        base = app.user_data_dir if app is not None else os.getcwd()
        with open(os.path.join(base, "crash.log"), "a", encoding="utf-8") as fh:
            fh.write(dt.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n" + tb + "\n")
    except Exception:
        pass
    box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
    box.add_widget(Label(text="Śviętovit: błąd. Zrób zrzut ekranu i wyślij.", size_hint_y=None, height=dp(36),
                         color=(1, 0.8, 0.5, 1), font_size=sp(15)))
    sv = ScrollView()
    lbl = Label(text=tb[-3500:], font_size=sp(10), size_hint_y=None, halign="left", valign="top",
                color=(0.93, 0.9, 0.83, 1))
    lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    lbl.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
    sv.add_widget(lbl)
    box.add_widget(sv)
    return box


try:
    from kivy.base import ExceptionHandler, ExceptionManager

    class _Handler(ExceptionHandler):
        def handle_exception(self, inst):
            try:
                tb = "".join(traceback.format_exception(type(inst), inst, inst.__traceback__))
                app = App.get_running_app()
                base = app.user_data_dir if app else os.getcwd()
                with open(os.path.join(base, "crash.log"), "a", encoding="utf-8") as fh:
                    fh.write(dt.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n" + tb + "\n")
                if app is not None and getattr(app, "root", None) is not None:
                    app.root_window.remove_widget(app.root)
                    app.root_window.add_widget(crash_view(tb, app))
            except Exception:
                pass
            return ExceptionManager.PASS

    ExceptionManager.add_handler(_Handler())
except Exception:
    pass


if __name__ == "__main__":
    SvietovitApp().run()
