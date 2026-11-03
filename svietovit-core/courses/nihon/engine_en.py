"""[en — wygenerowane przez tools/i18n.py, nie edytuj] Logika kursu japońskiego (日本語): słowa, ćwiczenia, postęp, serie, XP. Czysty Python (bez Kivy)."""
import json

from courses import config
import os
import random
import time
import datetime as dt

from .content_en import UNITS, INSIGHTS, ENDINGS_INSIGHT, ENDINGS, CHATS, CHAT_EXTRA, PUNCT

SEP = " "

GLAGOLITIC = set()
UI_LANG = "en"
BLANK = "＿"

# ---------------------------------------------------------------------------
# Romaji (transkrypcja Hepburna): か → ka, し → shi, っ podwaja spółgłoskę, ー wydłuża samogłoskę (ō),
# ん przed samogłoską dostaje apostrof (しんいち → shin'ichi). Dwuznaki ou / oo zapisujemy tak,
# jak w kanie (ありがとう → arigatou), bo tak uczy się je czytać.
# ---------------------------------------------------------------------------
_BASE = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ゔ": "vu",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa",
}
_SMALL_Y = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
_SPECIAL = {
    "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo", "てぃ": "ti", "でぃ": "di", "とぅ": "tu", "どぅ": "du",
    "うぃ": "wi", "うぇ": "we", "うぉ": "wo", "しぇ": "she", "じぇ": "je", "ちぇ": "che", "つぁ": "tsa",
    "つぃ": "tsi", "つぇ": "tse", "つぉ": "tso", "ゔぁ": "va", "ゔぃ": "vi", "ゔぇ": "ve", "ゔぉ": "vo",
    "いぇ": "ye", "くぁ": "kwa", "ぐぁ": "gwa",
}
_MACRON = {"a": "ā", "i": "ī", "u": "ū", "e": "ē", "o": "ō"}
_UNMACRON = {v: k for k, v in _MACRON.items()}
_PUNCT_TR = {"。": ".", "、": ",", "？": "?", "！": "!", "「": "“", "」": "”", "・": " "}


def to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def is_kana(c):
    return "ぁ" <= to_hira(c) <= "ゖ" or c == "ー"


def _romaji_word(w):
    s = to_hira(w)
    out = []
    i, gem = 0, False
    while i < len(s):
        c = s[i]
        if c == "っ":
            gem = True
            i += 1
            continue
        if c == "ー":
            if out and out[-1][-1:] in _MACRON:
                out[-1] = out[-1][:-1] + _MACRON[out[-1][-1]]
            i += 1
            continue
        pair = s[i:i + 2]
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if pair in _SPECIAL:
            r, i = _SPECIAL[pair], i + 2
        elif c in _BASE and nxt in _SMALL_Y and _BASE[c].endswith("i") and c not in "ゃゅょ":
            b = _BASE[c]
            r = (b[:-1] if b in ("shi", "chi", "ji") else b[:-1] + "y") + _SMALL_Y[nxt]
            i += 2
        elif c in _BASE:
            r, i = _BASE[c], i + 1
            if c == "ん" and i < len(s) and s[i] in "あいうえおやゆよ":
                r = "n'"
        else:
            r, i = _PUNCT_TR.get(c, c), i + 1
        if gem:
            if r[:1].isalpha() and r[0] not in "aiueon":
                r = ("t" if r.startswith("ch") else r[0]) + r
            gem = False
        out.append(r)
    return "".join(out)


try:
    from .content import READINGS
except ImportError:  # kurs bez kanji
    READINGS = {}


def reading_of(text):
    """Zapis kaną: dla słów z kanji bierzemy czytanie z tabeli READINGS."""
    return READINGS.get(text, text)


def pron(text, style=None):
    """Romaji: ありがとう → arigatou, 日本語 → nihongo."""
    return " ".join(_romaji_word(reading_of(w)) for w in text.split())


def translit(text):
    return pron(text)


def plain(text):
    """Bez kresek długich samogłosek (do porównania zapisu i wymowy)."""
    return "".join(_UNMACRON.get(c, c) for c in text)


_KUNREI = [("sha", "sya"), ("shu", "syu"), ("sho", "syo"), ("shi", "si"), ("cha", "tya"), ("chu", "tyu"),
           ("cho", "tyo"), ("chi", "ti"), ("tsu", "tu"), ("fu", "hu"), ("ja", "zya"), ("ju", "zyu"), ("jo", "zyo"),
           ("ji", "zi")]


def _norm_roman(t):
    """Porównywalna postać romaji: bez kresek, apostrofów, odmian kunrei i podwojonych samogłosek."""
    t = plain(t.lower())
    t = "".join(c for c in t if c.isalpha())
    for hep, kun in _KUNREI:
        t = t.replace(kun, hep)
    for a, b in (("ou", "o"), ("oo", "o"), ("uu", "u"), ("aa", "a"), ("ii", "i"), ("ei", "e"), ("ee", "e")):
        t = t.replace(a, b)
    return t


def check_typed(text, answer):
    """'correct' dla zapisu japońskiego albo romaji (z kreskami lub bez), 'wrong' w innym razie."""
    a = "".join(text.split())
    b = "".join(answer.split())
    if a == b or to_hira(a) == to_hira(b):
        return "correct"
    if _norm_roman(text) and _norm_roman(text) == _norm_roman(pron(answer)):
        return "correct"
    return "wrong"


_CONFUSE = [("shi", "chi"), ("chi", "shi"), ("tsu", "su"), ("su", "tsu"), ("fu", "hu"), ("ō", "o"), ("ū", "u"),
            ("ou", "o"), ("o", "ou"), ("kk", "k"), ("tt", "t"), ("ss", "s"), ("pp", "p"), ("ga", "ka"),
            ("ba", "pa"), ("da", "ta"), ("ze", "se"), ("gi", "ki"), ("bu", "pu"), ("ji", "shi"), ("ku", "gu"),
            ("ha", "ba"), ("ne", "me"), ("wa", "ra"), ("mu", "nu"), ("ro", "ru")]


def misreadings(r):
    """Typowe pomyłki w romaji: długie/krótkie samogłoski, pojedyncze/podwójne spółgłoski, dźwięczne/bezdźwięczne."""
    out = []
    for a, b in _CONFUSE:
        if a in r:
            x = r.replace(a, b, 1)
            if x != r and x not in out:
                out.append(x)
    return out


# ---------------------------------------------------------------------------
# Słowa
# ---------------------------------------------------------------------------
WORDS = {}
for _ui, _u in enumerate(UNITS):
    for _f, _pl, _cog, _hook in _u.get("words", []):
        if _f in WORDS:
            raise ValueError('Repeated word: ' + _f)
        if _f in READINGS and any("\u4e00" <= _c <= "\u9fff" for _c in _f):
            _hook = (_hook + " " if _hook else "") + "Kana: %s." % READINGS[_f]
        WORDS[_f] = {"id": _f, "form": _f, "tr": pron(_f), "pl": _pl, "cog": _cog, "hook": _hook,
                     "unit": _ui, "letter": False, "glag": False}


def token_tr(t):
    if t in PUNCT:
        return None
    return translit(t)


def token_meaning(t):
    if t in WORDS:
        return WORDS[t]["pl"]
    return CHAT_EXTRA.get(t)


def join(tokens):
    return "".join(tokens)


def sentence_tr(tokens):
    out = ""
    for t in tokens:
        if t in PUNCT:
            out += _PUNCT_TR.get(t, t)
        else:
            out += (" " if out and not out.endswith(" ") else "") + translit(t)
    return out


def prev_in_track(idx):
    tr = UNITS[idx]["track"]
    for j in range(idx - 1, -1, -1):
        if UNITS[j]["track"] == tr:
            return j
    return None


def unit_index(uid):
    for i, u in enumerate(UNITS):
        if u["id"] == uid:
            return i
    raise KeyError(uid)


def unit_items(unit_idx):
    u = UNITS[unit_idx]
    return ["lit:" + l[0] for l in u.get("letters", [])] + [w[0] for w in u.get("words", [])]


def unit_groups(unit_idx, n=3):
    items = unit_items(unit_idx)
    size = -(-len(items) // n)
    return [items[i:i + size] for i in range(0, len(items), size)]


def is_draw_letter(w):
    return len(w["form"]) == 1 and ord(w["form"]) >= 0x4E00


def endings_for(uid):
    return [e for e in ENDINGS if e[7] == uid]


# ---------------------------------------------------------------------------
# Wyjaśnianie błędów (wzorce z polskiego)
# ---------------------------------------------------------------------------
def explain_mistake(given, answer, traps=None):
    if not given:
        return None
    traps = traps or {}
    for t in given:
        if t in traps and t not in answer:
            return traps[t]
    g, a = list(given), list(answer)
    if sorted(g) == sorted(a):
        return 'Right words, different order. Look at the solution: the word order in these sentences is worth remembering.'
    missing = [t for t in a if t not in g]
    if missing:
        return 'Missing: %s (%s).' % (missing[0], WORDS.get(missing[0], {}).get("pl", ""))
    return None


# ---------------------------------------------------------------------------
# Generowanie ćwiczeń
# ---------------------------------------------------------------------------
class Gen:
    def __init__(self, known, rng=None):
        self.rng = rng or random.Random()
        self.known = [h for h in known if h in WORDS]

    def _pool(self, target, prefer=None, same_kind=True):
        r = self.rng
        kind = WORDS[target]["letter"], WORDS[target]["glag"], WORDS[target].get("num", False)

        def ok(h):
            return h != target and (not same_kind or (WORDS[h]["letter"], WORDS[h]["glag"], WORDS[h].get("num", False)) == kind)
        prefer = [h for h in (prefer or []) if ok(h)]
        rest = [h for h in self.known if ok(h) and h not in prefer]
        everything = [h for h in WORDS if ok(h) and h not in prefer and h not in rest]
        for x in (prefer, rest, everything):
            r.shuffle(x)
        return prefer + rest + everything

    def _distract(self, target, n, key, prefer=None, avoid=()):
        seen = {key(WORDS[target])} | set(avoid)
        out = []
        for h in self._pool(target, prefer):
            k = key(WORDS[h])
            if k in seen or not k or WORDS[h]["pl"] == WORDS[target]["pl"]:
                continue
            seen.add(k)
            out.append(h)
            if len(out) == n:
                break
        return out

    def _options(self, correct, others):
        opts = [correct] + others
        self.rng.shuffle(opts)
        return opts

    def intro(self, h):
        w = WORDS[h]
        return {"type": "intro", "word": h}

    def meaning(self, h, pool=None):
        w = WORDS[h]
        others = self._distract(h, 3, lambda x: x["pl"], pool)
        title = 'How does it sound?' if w["letter"] else 'What does it mean?'
        return {"type": "choice", "mode": "meaning", "word": h, "title": title,
                "prompt": w["form"], "options": self._options(w["pl"], [WORDS[o]["pl"] for o in others]),
                "answer": w["pl"], "solution": "%s (%s): %s" % (w["form"], w["tr"], w["pl"])}

    def form(self, h, pool=None):
        w = WORDS[h]
        others = self._distract(h, 3, lambda x: x["form"], pool)
        title = 'Which character is it?' if w["letter"] else 'Pick the right word'
        return {"type": "choice", "mode": "form", "word": h, "title": title,
                "prompt": w["pl"], "options": self._options(w["form"], [WORDS[o]["form"] for o in others]),
                "answer": w["form"], "solution": "%s (%s)" % (w["form"], w["tr"])}

    def reading(self, h, pool=None):
        """Jak to przeczytać? Dystraktory to typowe pomyłki w latynizacji."""
        w = WORDS[h]
        right = w["tr"]
        opts = [c for c in misreadings(right) if c != right][:3]
        for o in self._distract(h, 3, lambda x: x["tr"], pool, avoid=set(opts) | {right}):
            if len(opts) == 3:
                break
            opts.append(WORDS[o]["tr"])
        return {"type": "choice", "mode": "reading", "word": h, "title": 'How is it read?',
                "prompt": w["form"], "options": self._options(right, opts[:3]), "answer": right,
                "solution": '%s, read “%s” (%s)' % (w["form"], right, w["pl"])}

    def cognate(self, h, pool=None):
        w = WORDS[h]
        others = self._distract(h, 3, lambda x: x["cog"], pool)
        return {"type": "choice", "mode": "cognate", "word": h, "title": 'Which English word is related?',
                "prompt": w["form"], "options": self._options(w["cog"], [WORDS[o]["cog"] for o in others]),
                "answer": w["cog"], "solution": "%s → %s (%s)" % (w["form"], w["cog"], w["pl"])}

    def ending(self, e):
        """Uzupełnij zdanie."""
        before, stem, end, after, opts, cue, why, _ = e
        opts = list(opts)
        self.rng.shuffle(opts)
        return {"type": "choice", "mode": "cloze", "title": 'Fill in the ending',
                "prompt": before + stem + BLANK + after, "prompt_sub": cue, "options": opts, "answer": end,
                "solution": "%s%s%s%s" % (before, stem, end, after), "why": why}

    def match(self, words, field="pl"):
        seen, uniq = set(), []
        for h in list(words)[:5]:
            k = WORDS[h][field]
            if k not in seen:
                seen.add(k)
                uniq.append(h)
        return {"type": "match", "title": 'Match the pairs', "pairs": [(WORDS[h]["form"], WORDS[h][field]) for h in uniq],
                "words": uniq}

    def typing(self, h):
        w = WORDS[h]
        return {"type": "type", "word": h, "title": 'Write in Japanese', "prompt": w["pl"],
                "prompt_sub": 'related: %s' % w["cog"] if w["cog"] and w["cog"] != w["pl"] else "", "answer": w["form"],
                "solution": w["form"]}

    def draw(self, h):
        w = WORDS[h]
        return {"type": "draw", "word": h, "title": 'Write this character', "prompt": w["pl"], "prompt_sub": w["tr"],
                "answer": w["form"], "solution": w["form"]}

    def build(self, tokens, pl, traps=None, hint=None, title=None, insight=None):
        traps = traps or {}
        r = self.rng
        extra = [t for t in traps if t not in tokens and t in WORDS][:2]
        cands = [h for h in self.known if not WORDS[h]["letter"] and h not in tokens and h not in extra]
        r.shuffle(cands)
        while len(extra) < 3 and cands:
            extra.append(cands.pop())
        bank = list(tokens) + extra
        r.shuffle(bank)
        return {"type": "build", "title": title or 'Translate into Japanese', "prompt": pl, "bank": bank,
                "answer": list(tokens), "traps": traps, "think": hint, "insight": insight,
                "words": list(tokens), "solution": join(tokens) + "\n" + sentence_tr(tokens)}

    def sentence_meaning(self, tokens, pl, others):
        others = [e for e in others if e != pl]
        self.rng.shuffle(others)
        return {"type": "choice", "mode": "sentence", "title": 'What does it mean?', "prompt": join(tokens),
                "prompt_sub": sentence_tr(tokens), "options": self._options(pl, others[:3]), "answer": pl,
                "words": list(tokens), "solution": pl}

    def insight_card(self, ins):
        return {"type": "insight", "title": ins["title"], "text": ins["text"]}


def available_sentences(unit_idx, known_set):
    out = []
    for ui in range(unit_idx + 1):
        for tokens, pl, traps in UNITS[ui].get("sentences", []):
            if all(t in known_set or t in PUNCT for t in tokens):
                out.append((tokens, pl, traps, ui))
    return out


def all_sentence_pl():
    return [s[1] for u in UNITS for s in u.get("sentences", [])]


def insight_ready(ins, known_set):
    return all(t in known_set or t in PUNCT for _, toks, _ in ins["chain"] for t in toks)


def _traps_for(tokens):
    for u in UNITS:
        for toks, pl, traps in u.get("sentences", []):
            if toks == tokens:
                return traps
    return {}


def think_chain(gen, ins):
    out = [gen.insight_card(ins)]
    for k, (pl, toks, hint) in enumerate(ins["chain"]):
        out.append(gen.build(toks, pl, _traps_for(toks), hint=hint,
                             title='Think (%d/%d)' % (k + 1, len(ins["chain"])), insight=ins["title"]))
    return out


LESSON_LEN = 12
LESSONS_PER_LEVEL = 3
MAX_CROWNS = 5


def make_lesson(state, unit_idx, rng=None):
    rng = rng or random.Random()
    unit = UNITS[unit_idx]
    uid = unit["id"]
    level = state.crowns(uid)
    known_before = [h for h in WORDS if WORDS[h]["unit"] < unit_idx]
    items = unit_items(unit_idx)
    exercises = []
    if level == 0:
        groups = unit_groups(unit_idx)
        k = min(state.lessons(uid), len(groups) - 1)
        new = groups[k]
        pool = [h for g in groups[:k + 1] for h in g]
        known = known_before + pool
        gen = Gen(known, rng)
        for h in new:
            exercises.append(gen.intro(h))
            exercises.append(gen.meaning(h, pool) if rng.random() < 0.5 else gen.form(h, pool))
        known_set = set(known)
        for ins in INSIGHTS.get(uid, []):
            if uid + ":" + ins["title"] in state.data["insights_seen"]:
                continue
            if not ins["chain"] or insight_ready(ins, known_set):
                exercises.extend(think_chain(gen, ins))
        exercises.extend(_mixed(gen, pool, known_set, unit_idx, level, rng, max(4, LESSON_LEN - len(exercises))))
    else:
        known = known_before + items
        gen = Gen(known, rng)
        chains = [i for i in INSIGHTS.get(uid, []) if i["chain"]]
        if chains:
            ins = rng.choice(chains)
            pl, toks, hint = rng.choice(ins["chain"])
            exercises.append(gen.build(toks, pl, _traps_for(toks), hint=hint if level < 3 else None,
                                       title='Think', insight=ins["title"]))
        exercises.extend(_mixed(gen, items, set(known), unit_idx, level, rng, LESSON_LEN - len(exercises)))
    return exercises


def _mixed(gen, pool, known_set, unit_idx, level, rng, n):
    words = list(pool)
    rng.shuffle(words)
    letters = [h for h in pool if WORDS[h]["letter"]]
    drawable = [h for h in pool if is_draw_letter(WORDS[h])]
    vocab = [h for h in pool if not WORDS[h]["letter"]]
    cognates = [h for h in vocab if WORDS[h]["cog"] and WORDS[h]["cog"] != WORDS[h]["pl"]]
    units = sorted({WORDS[h]["unit"] for h in pool})
    drills = [e for u in units for e in endings_for(UNITS[u]["id"])]
    sentences = available_sentences(unit_idx, known_set)
    sentences = [s for s in sentences if s[3] == unit_idx] or sentences
    if not vocab:
        sentences = []
    others = all_sentence_pl()
    weights = {
        "meaning": 3 if level < 2 else 1,
        "form": 3 if level < 2 else 1,
        "reading": 2 if vocab else 0,
        "cognate": 2 if cognates else 0,
        "ending": (2 + level) if drills else 0,
        "build": (2 + level) if sentences else 0,
        "sentence": 2 if sentences else 0,
        "type": (1 + level // 2) if (level >= 1 and vocab) else 0,
        "draw": 1 if drawable else 0,
    }
    kinds = [k for k, v in weights.items() for _ in range(v)]
    out = []
    if len(words) >= 4:
        out.append(gen.match(words[:5], "pl"))
    i, last = 0, None
    while len(out) < n and kinds:
        kind = rng.choice(kinds)
        if kind == last and len(set(kinds)) > 1:
            continue
        last = kind
        h = words[i % len(words)]
        i += 1
        if kind == "meaning":
            out.append(gen.meaning(h, pool))
        elif kind == "form":
            out.append(gen.form(h, pool))
        elif kind == "reading":
            out.append(gen.reading(rng.choice(vocab), pool))
        elif kind == "cognate":
            out.append(gen.cognate(rng.choice(cognates), pool))
        elif kind == "ending":
            out.append(gen.ending(rng.choice(drills)))
        elif kind == "type":
            out.append(gen.typing(rng.choice(vocab)))
        elif kind == "draw":
            out.append(gen.draw(rng.choice(drawable)))
        else:
            toks, pl, traps, _ = rng.choice(sentences)
            out.append(gen.build(toks, pl, traps) if kind == "build" else gen.sentence_meaning(toks, pl, others))
    rng.shuffle(out)
    return out


def make_practice(state, rng=None, n=LESSON_LEN):
    rng = rng or random.Random()
    learned = state.learned_words()
    if not learned:
        return []
    learned.sort(key=lambda h: (state.strength(h), rng.random()))
    weak = learned[:max(6, n // 2)]
    gen = Gen(learned, rng)
    top = max(WORDS[h]["unit"] for h in learned)
    return _mixed(gen, weak, set(learned), top, 2, rng, n)[:n]


def make_sound_training(state, rng=None, n=14):
    """Zakładka „Końcówki”: ćwiczenia z końcówek z odblokowanych działów."""
    rng = rng or random.Random()
    open_units = {u["id"] for i, u in enumerate(UNITS) if state.unlocked(i)}
    drills = [e for e in ENDINGS if e[7] in open_units] or [e for e in ENDINGS if e[7] == ENDINGS[0][7]]
    gen = Gen(state.learned_words() or list(WORDS)[:20], rng)
    out = [{"type": "insight", "title": ENDINGS_INSIGHT["title"], "text": ENDINGS_INSIGHT["text"]}]
    while len(out) < n:
        out.append(gen.ending(rng.choice(drills)))
    return out


# ---------------------------------------------------------------------------
# Sesja
# ---------------------------------------------------------------------------
class Session:
    def __init__(self, exercises, kind="lesson", unit_idx=None, hearts=True):
        self.queue = list(exercises)
        self.kind, self.unit_idx, self.use_hearts = kind, unit_idx, hearts
        self.total = len(self.queue)
        self.done = self.graded = self.first_try_correct = self.mistakes = 0
        self.combo = self.max_combo = 0
        self.insights = set()
        self.word_results = []

    @property
    def current(self):
        return self.queue[0] if self.queue else None

    @property
    def progress(self):
        return self.done / max(1, self.total)

    @property
    def finished(self):
        return not self.queue

    def answer(self, correct):
        ex = self.queue.pop(0)
        retry = ex.get("_retry", False)
        if ex["type"] == "insight":
            self.insights.add(ex["title"])
        if correct is not None:
            for h in self._words(ex):
                self.word_results.append((h, bool(correct)))
        if correct is None or correct:
            self.done += 1
            if correct:
                if not retry:
                    self.graded += 1
                    self.first_try_correct += 1
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                if self.combo in (5, 10, 15, 20):
                    return self.combo
            return 0
        if not retry:
            self.graded += 1
        self.mistakes += 1
        self.combo = 0
        again = dict(ex)
        again["_retry"] = True
        self.queue.append(again)
        return 0

    @staticmethod
    def _words(ex):
        if ex["type"] == "match":
            return ex["words"]
        if ex.get("word"):
            return [ex["word"]]
        return [t for t in ex.get("words", []) if t in WORDS]

    @property
    def accuracy(self):
        return self.first_try_correct / max(1, self.graded)

    def xp(self):
        bonus = min(3, self.max_combo // 5)
        perfect = 2 if self.mistakes == 0 else 0
        return 10 + bonus + perfect, bonus, perfect


# ---------------------------------------------------------------------------
# Stan zapisywany na dysku
# ---------------------------------------------------------------------------
HEART_MAX = 5
HEART_REGEN_S = 30 * 60
SRS_DAYS = [0, 1, 2, 4, 8, 16, 32]
GOALS = [('Casual', 10), ('Regular', 20), ('Serious', 30), ('Insane', 50)]
FREEZE_COST = 30
REFILL_COST = 40
MAX_FREEZES = 2


def _default():
    return {"version": 1, "onboarded": False, "xp_total": 0, "xp_by_day": {}, "daily_goal": 20,
            "streak": 0, "last_goal_day": None, "longest_streak": 0, "freezes": 0, "gems": 20,
            "hearts": HEART_MAX, "hearts_ts": 0, "units": {}, "words": {}, "insights_seen": [],
            "settings": {"sound": True, "pron": True}, "chats": {}, "lessons_completed": 0}


class State:
    def __init__(self, path=None, now=None):
        self.path, self._now = path, now
        self.data = _default()
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    loaded = json.load(f)
                d = _default()
                d.update(loaded)
                d["settings"] = {**_default()["settings"], **loaded.get("settings", {})}
                self.data = d
            except (ValueError, OSError):
                pass

    def now(self):
        return self._now() if self._now else time.time()

    def today(self):
        return dt.date.fromtimestamp(self.now())

    def save(self):
        if not self.path:
            return
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    # -- działy --------------------------------------------------------------
    def _unit(self, uid):
        return self.data["units"].setdefault(uid, {"crowns": 0, "lessons": 0})

    def crowns(self, uid):
        return self._unit(uid)["crowns"]

    def lessons(self, uid):
        return self._unit(uid)["lessons"]

    def unlocked(self, unit_idx):
        if config.UNLOCK_ALL:
            return True
        if unit_idx == 0:
            return True
        prev = prev_in_track(unit_idx)
        if prev is not None:
            return self.crowns(UNITS[prev]["id"]) >= 1
        req = UNITS[unit_idx].get("requires")
        return req is None or self.crowns(req) >= 1

    def unlock_reason(self, unit_idx):
        prev = prev_in_track(unit_idx)
        if prev is None:
            prev = unit_index(UNITS[unit_idx]["requires"])
        return UNITS[prev]["title"]

    def unit_strength(self, unit_idx):
        seen = [h for h in unit_items(unit_idx) if h in self.data["words"]]
        if not seen:
            return 1.0
        return sum(self.strength(h) for h in seen) / len(seen)

    def cracked(self, unit_idx):
        return self.crowns(UNITS[unit_idx]["id"]) >= 1 and self.unit_strength(unit_idx) < 0.5

    # -- słowa -------------------------------------------------------------------
    def learned_words(self):
        return [h for h in self.data["words"] if h in WORDS]

    def record_word(self, h, correct):
        w = self.data["words"].setdefault(h, {"box": 0, "last": self.now(), "right": 0, "wrong": 0})
        if correct:
            w["box"] = min(len(SRS_DAYS) - 1, w["box"] + 1)
            w["right"] += 1
        else:
            w["box"] = max(0, w["box"] - 2)
            w["wrong"] += 1
        w["last"] = self.now()

    def strength(self, h):
        w = self.data["words"].get(h)
        if not w:
            return 0.0
        interval = SRS_DAYS[w["box"]] or 0.5
        age = (self.now() - w["last"]) / 86400.0
        base = min(1.0, 0.6 + 0.08 * w["box"]) if w["box"] else 0.45
        if age <= interval:
            return base
        return max(0.0, base - 0.5 * (age - interval) / (interval + 1))

    # -- serca -------------------------------------------------------------------
    def hearts(self):
        d = self.data
        if d["hearts"] < HEART_MAX:
            gained = int((self.now() - d["hearts_ts"]) // HEART_REGEN_S)
            if gained > 0:
                d["hearts"] = min(HEART_MAX, d["hearts"] + gained)
                d["hearts_ts"] += gained * HEART_REGEN_S
        return d["hearts"]

    def lose_heart(self):
        self.hearts()
        if self.data["hearts"] == HEART_MAX:
            self.data["hearts_ts"] = self.now()
        self.data["hearts"] = max(0, self.data["hearts"] - 1)

    def gain_heart(self):
        self.hearts()
        self.data["hearts"] = min(HEART_MAX, self.data["hearts"] + 1)

    def seconds_to_next_heart(self):
        if self.hearts() >= HEART_MAX:
            return 0
        return int(HEART_REGEN_S - (self.now() - self.data["hearts_ts"]))

    # -- XP i seria --------------------------------------------------------------
    def xp_today(self):
        return self.data["xp_by_day"].get(self.today().isoformat(), 0)

    def check_streak(self):
        d = self.data
        last = d["last_goal_day"]
        if not last or d["streak"] == 0:
            return None
        gap = (self.today() - dt.date.fromisoformat(last)).days
        if gap <= 1:
            return None
        missed = gap - 1
        if d["freezes"] >= missed:
            d["freezes"] -= missed
            d["last_goal_day"] = (self.today() - dt.timedelta(days=1)).isoformat()
            return "frozen"
        d["streak"] = 0
        return "lost"

    def add_xp(self, n):
        d = self.data
        today = self.today().isoformat()
        d["xp_total"] += n
        d["xp_by_day"][today] = d["xp_by_day"].get(today, 0) + n
        if d["xp_by_day"][today] >= d["daily_goal"] and d["last_goal_day"] != today:
            yesterday = (self.today() - dt.timedelta(days=1)).isoformat()
            d["streak"] = d["streak"] + 1 if d["last_goal_day"] == yesterday else 1
            d["last_goal_day"] = today
            d["longest_streak"] = max(d["longest_streak"], d["streak"])
            return True
        return False

    def level(self):
        xp, lvl, need = self.data["xp_total"], 1, 60
        while xp >= need:
            xp -= need
            lvl += 1
            need = int(need * 1.35)
        return lvl, xp, need

    def week_xp(self):
        names = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        t = self.today()
        days = [t - dt.timedelta(days=i) for i in range(6, -1, -1)]
        return [(names[d.weekday()], self.data["xp_by_day"].get(d.isoformat(), 0)) for d in days]

    def buy_freeze(self):
        d = self.data
        if d["gems"] >= FREEZE_COST and d["freezes"] < MAX_FREEZES:
            d["gems"] -= FREEZE_COST
            d["freezes"] += 1
            return True
        return False

    def buy_refill(self):
        d = self.data
        if d["gems"] >= REFILL_COST and self.hearts() < HEART_MAX:
            d["gems"] -= REFILL_COST
            d["hearts"] = HEART_MAX
            return True
        return False

    # -- rozmowy --------------------------------------------------------------
    def chat_unlocked(self, chat):
        if config.UNLOCK_ALL:
            return True
        return self.crowns(chat["requires"]) >= 1

    def chat_stars(self, cid):
        return self.data["chats"].get(cid, 0)

    def finish_chat(self, chat, mistakes):
        stars = 3 if mistakes == 0 else (2 if mistakes <= 2 else 1)
        d = self.data
        d["chats"][chat["id"]] = max(stars, d["chats"].get(chat["id"], 0))
        for turn in chat["turns"]:
            for t in turn["bot"]:
                if t in WORDS and t in d["words"]:
                    self.record_word(t, True)
        xp = 10 + (5 if mistakes == 0 else 0)
        gems = 3 if mistakes == 0 else 1
        d["gems"] += gems
        if self.hearts() < HEART_MAX:
            self.gain_heart()
        ext = self.add_xp(xp)
        self.save()
        return {"xp": xp, "gems": gems, "stars": stars, "streak_extended": ext, "streak": d["streak"]}

    # -- koniec lekcji ----------------------------------------------------------
    def finish(self, session):
        d = self.data
        for h, ok in session.word_results:
            self.record_word(h, ok)
        xp, combo_bonus, perfect = session.xp()
        gems = 2 + (3 if perfect else 0)
        ev = {"xp": xp, "combo_bonus": combo_bonus, "perfect": bool(perfect), "accuracy": session.accuracy,
              "crown_up": None, "unlocked": None, "heart_back": False}
        if session.kind == "lesson" and session.unit_idx is not None:
            before = [self.unlocked(i) for i in range(len(UNITS))]
            uid = UNITS[session.unit_idx]["id"]
            u = self._unit(uid)
            if u["crowns"] < MAX_CROWNS:
                u["lessons"] += 1
                if u["lessons"] >= LESSONS_PER_LEVEL:
                    u["crowns"] += 1
                    u["lessons"] = 0
                    gems += 10
                    ev["crown_up"] = u["crowns"]
                    new = [i for i in range(len(UNITS)) if self.unlocked(i) and not before[i]]
                    if new:
                        ev["unlocked"] = new
                    chats = [c["title"] for c in CHATS if c["requires"] == uid and u["crowns"] == 1]
                    if chats:
                        ev["chats"] = chats
            for t in session.insights:
                key = uid + ":" + t
                if key not in d["insights_seen"]:
                    d["insights_seen"].append(key)
        elif self.hearts() < HEART_MAX:
            self.gain_heart()
            ev["heart_back"] = True
        d["gems"] += gems
        ev["gems"] = gems
        d["lessons_completed"] += 1
        ev["streak_extended"] = self.add_xp(xp)
        ev["streak"] = d["streak"]
        self.save()
        return ev

    def reset(self):
        self.data = _default()
        self.data["onboarded"] = True
        self.save()
