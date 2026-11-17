#!/usr/bin/env python3
"""Baut ein Anki-.apkg (Green Line 1) aus einer Vokabel-Textdatei – ohne genanki.
Format: '## Stapelpfad | Badge | Stil' und Zeilen 'en | de | hinweis | satz_en | satz_de | tipp | seite'."""
import json, sqlite3, zipfile, hashlib, time, sys, os, re, html

SRC, OUT = sys.argv[1], sys.argv[2]
ROOT = "Green Line 1"
MODEL_ID = 1731000000002
FIELDS = ["Deutsch", "Englisch", "Hinweis", "Satz_EN", "Satz_DE", "Tipp", "Einheit", "Seite", "Stil"]

HEAD = '<div class="card-wrap {{Stil}}">\n  <div class="badge">{{Einheit}}{{#Seite}} · S. {{Seite}}{{/Seite}}</div>\n'
QFMT = HEAD + """  <div class="prompt">Wie heißt das auf Englisch?</div>
  <div class="de">{{Deutsch}}</div>
  {{#Hinweis}}<div class="hint">{{Hinweis}}</div>{{/Hinweis}}
  <div class="type-box">{{type:Englisch}}</div>
</div>
<script>
(function(){var i=document.getElementById('typeans'); if(!i||i.tagName!=='INPUT')return;
 try{i.type='email';}catch(e){}
 i.setAttribute('inputmode','email'); i.setAttribute('autocapitalize','off'); i.setAttribute('autocorrect','off'); i.setAttribute('autocomplete','off'); i.setAttribute('spellcheck','false');
 i.placeholder='Englisch eintippen …';
 i.addEventListener('input',function(){var v=i.value.replace(/[\\u2018\\u2019\\u00B4`]/g,"'"); if(v!==i.value)i.value=v;});
 setTimeout(function(){i.focus();},60);})();
</script>"""
AFMT = HEAD + """  <div class="de">{{Deutsch}}</div>
  {{#Hinweis}}<div class="hint">{{Hinweis}}</div>{{/Hinweis}}
  <div class="type-box">{{type:Englisch}}</div>
  <div class="say en-word" onclick="glSpeak(this)"><span class="word">{{Englisch}}</span>{{tts en_GB:Englisch}}</div>
  {{#Satz_EN}}<div class="say sentence" onclick="glSpeak(this)"><div class="s-en">{{Satz_EN}}{{tts en_GB:Satz_EN}}</div><div class="s-de">{{Satz_DE}}</div></div>{{/Satz_EN}}
  {{#Tipp}}<div class="tip">💡 {{Tipp}}</div>{{/Tipp}}
  <div class="tap-tip">🔊 Wort oder Satz antippen zum Anhören</div>
</div>
<script>
function glSpeak(el){var b=el.querySelector('.replay-button, a.soundLink'); if(b) b.click();}
(function(){var t=document.querySelector('code#typeans'); if(!t)return;
 if(!t.querySelector('.typeGood,.typeBad') ) t.insertAdjacentHTML('beforebegin','<div class="notyped">✋ Nicht eingetippt</div>');
 else if(!t.querySelector('.typeBad,.typeMissed')) t.insertAdjacentHTML('beforebegin','<div class="yay">🎉 Richtig!</div>');})();
</script>"""

PAL = {"hello": ("#00a3a3", "#4fd1c5"), "checkin": ("#2f80ed", "#56ccf2"), "station1": ("#27ae60", "#6fcf97"),
       "station2": ("#8e44ad", "#bb6bd9"), "station3": ("#f2994a", "#f2c94c"), "story": ("#e84393", "#fd79a8"),
       "media": ("#eb5757", "#ff8a80")}
CSS = """
.card { font-family: "Nunito","Segoe UI",Roboto,Arial,sans-serif; background:#eef4fb; color:#1d2a3a; margin:0; padding:12px; text-align:center; }
.card-wrap { --c1:#2f80ed; --c2:#56ccf2; max-width:560px; margin:0 auto; background:#fff; border-radius:22px;
  box-shadow:0 6px 18px rgba(30,60,120,.15); padding:18px 16px 20px; border-top:10px solid var(--c1); }
.badge { display:inline-block; background:linear-gradient(90deg,var(--c1),var(--c2)); color:#fff; font-weight:700;
  font-size:14px; padding:4px 14px; border-radius:999px; }
.prompt { margin-top:14px; font-size:15px; color:#6b7a90; }
.de { font-size:30px; font-weight:800; margin:8px 0 4px; }
.hint { font-size:15px; color:#8a6d00; background:#fff3c4; display:inline-block; padding:3px 10px; border-radius:10px; margin-top:4px; }
.type-box { margin-top:16px; }
input#typeans { width:90%; box-sizing:border-box; font-size:24px; padding:12px; border:3px solid var(--c2); border-radius:14px; text-align:center; outline:none; }
input#typeans:focus { border-color:var(--c1); box-shadow:0 0 0 4px rgba(0,0,0,.08); }
code#typeans { display:block; font-family:inherit; font-size:22px; background:#f6f8fb; padding:10px; border-radius:12px; white-space:pre-wrap; }
.typeGood { background:#c8f7d4; color:#0a6b2a; } .typeBad { background:#ffd0d0; color:#a40000; } .typeMissed { background:#e6e6e6; color:#555; }
.yay { color:#0a6b2a; font-weight:800; font-size:18px; margin-bottom:6px; }
.notyped { color:#a40000; font-weight:800; font-size:16px; margin-bottom:6px; }
.say { cursor:pointer; -webkit-tap-highlight-color:transparent; transition:transform .1s; }
.say:active { transform:scale(.97); }
.en-word { margin:16px auto 10px; padding:12px; border-radius:16px; background:linear-gradient(90deg,var(--c1),var(--c2)); color:#fff; }
.en-word .word { font-size:32px; font-weight:800; margin-right:6px; }
.sentence { text-align:left; margin:10px 0; padding:12px 14px; border-radius:14px; background:#f3f7ff; border-left:6px solid var(--c2); }
.s-en { font-size:20px; font-weight:700; }
.s-de { font-size:15px; color:#6b7a90; margin-top:4px; }
.tip { text-align:left; margin-top:10px; padding:10px 12px; border-radius:12px; background:#fff3c4; color:#5c4800; font-size:15px; }
.replay-button svg { width:30px; height:30px; vertical-align:middle; }
.en-word .replay-button svg circle { fill:#fff; stroke:#fff; } .en-word .replay-button svg path { fill:var(--c1); stroke:none; }
.sentence .replay-button svg circle { fill:var(--c1); stroke:var(--c1); } .sentence .replay-button svg path { fill:#fff; stroke:none; }
.tap-tip { margin-top:12px; font-size:13px; color:#9aa8bb; }
.nightMode .card-wrap, .night_mode .card-wrap { background:#1f2530; color:#e8eef7; box-shadow:none; }
.nightMode .sentence, .night_mode .sentence, .nightMode code#typeans, .night_mode code#typeans { background:#283142; }
.nightMode input#typeans, .night_mode input#typeans { background:#283142; color:#e8eef7; }
.nightMode .tip, .night_mode .tip { background:#3d3520; color:#ffe9a8; }
"""
for k, (a, b) in PAL.items():
    CSS += f".card-wrap.{k} {{ --c1:{a}; --c2:{b}; }}\n"

def did_for(name):
    return int(hashlib.sha1(name.encode()).hexdigest()[:10], 16) % (1 << 40) + 1_000_000_000

def parse(path):
    notes, sec = [], None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("# "): continue
        if line.startswith("## "):
            p = [x.strip() for x in line[3:].split("|")]
            sec = {"deck": f"{ROOT}::{p[0]}", "badge": p[1], "stil": p[2]}; continue
        p = [x.strip() for x in line.split("|")]
        assert len(p) == 7, f"Spaltenfehler: {line}"
        en = re.sub(r"[.!…]+$", "", p[0]).strip()
        notes.append({"en": en, "de": p[1], "hint": p[2], "s_en": p[3], "s_de": p[4], "tip": p[5], "page": p[6], **sec})
    return notes

def main():
    notes = parse(SRC)
    now = int(time.time())
    names = set()
    for n in notes:
        parts = n["deck"].split("::")
        for i in range(1, len(parts) + 1): names.add("::".join(parts[:i]))
    def deck(name, did):
        return {"id": did, "name": name, "mod": now, "usn": -1, "collapsed": False, "browserCollapsed": False,
                "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0], "dyn": 0, "conf": 1,
                "desc": "", "extendNew": 10, "extendRev": 50}
    decks = {"1": deck("Default", 1)}
    for nm in names: decks[str(did_for(nm))] = deck(nm, did_for(nm))
    decks[str(did_for(ROOT))]["desc"] = "Vokabeln aus Green Line 1 (Ausgabe 2021). Deutsch lesen → Englisch eintippen."
    model = {"id": MODEL_ID, "name": "Green Line – Deutsch → Englisch (tippen)", "type": 0, "mod": now, "usn": -1,
             "sortf": 1, "did": did_for(ROOT), "tags": [], "vers": [], "latexPre": "", "latexPost": "", "latexsvg": False,
             "req": [[0, "all", [0]]], "css": CSS,
             "flds": [{"name": f, "ord": i, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []} for i, f in enumerate(FIELDS)],
             "tmpls": [{"name": "Deutsch → Englisch", "ord": 0, "qfmt": QFMT, "afmt": AFMT, "did": None, "bqfmt": "", "bafmt": ""}]}
    dconf = {"1": {"id": 1, "name": "Default", "mod": 0, "usn": 0, "maxTaken": 60, "autoplay": True, "timer": 0, "replayq": True, "dyn": False,
             "new": {"bury": True, "delays": [1, 10], "initialFactor": 2500, "ints": [1, 4, 7], "order": 1, "perDay": 20, "separate": True},
             "rev": {"bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1, "maxIvl": 36500, "minSpace": 1, "perDay": 200},
             "lapse": {"delays": [10], "leechAction": 0, "leechFails": 8, "minInt": 1, "mult": 0}}}
    conf = {"activeDecks": [1], "curDeck": 1, "newSpread": 0, "collapseTime": 1200, "timeLim": 0, "estTimes": True,
            "dueCounts": True, "curModel": None, "nextPos": 1, "sortType": "noteFld", "sortBackwards": False, "addToCur": True}
    tmp = OUT + ".anki2"
    if os.path.exists(tmp): os.remove(tmp)
    db = sqlite3.connect(tmp); c = db.cursor()
    c.executescript("""
    CREATE TABLE col (id integer primary key, crt integer not null, mod integer not null, scm integer not null, ver integer not null, dty integer not null, usn integer not null, ls integer not null, conf text not null, models text not null, decks text not null, dconf text not null, tags text not null);
    CREATE TABLE notes (id integer primary key, guid text not null, mid integer not null, mod integer not null, usn integer not null, tags text not null, flds text not null, sfld integer not null, csum integer not null, flags integer not null, data text not null);
    CREATE TABLE cards (id integer primary key, nid integer not null, did integer not null, ord integer not null, mod integer not null, usn integer not null, type integer not null, queue integer not null, due integer not null, ivl integer not null, factor integer not null, reps integer not null, lapses integer not null, left integer not null, odue integer not null, odid integer not null, flags integer not null, data text not null);
    CREATE TABLE revlog (id integer primary key, cid integer not null, usn integer not null, ease integer not null, ivl integer not null, lastIvl integer not null, factor integer not null, time integer not null, type integer not null);
    CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
    CREATE INDEX ix_notes_usn on notes (usn); CREATE INDEX ix_cards_usn on cards (usn); CREATE INDEX ix_revlog_usn on revlog (usn);
    CREATE INDEX ix_cards_nid on cards (nid); CREATE INDEX ix_cards_sched on cards (did, queue, due); CREATE INDEX ix_revlog_cid on revlog (cid); CREATE INDEX ix_notes_csum on notes (csum);
    """)
    c.execute("INSERT INTO col VALUES (1,?,?,?,11,0,0,0,?,?,?,?,?)", (now - now % 86400, now * 1000, now * 1000,
              json.dumps(conf), json.dumps({str(MODEL_ID): model}), json.dumps(decks), json.dumps(dconf), "{}"))
    base, seen = now * 1000, set()
    for i, n in enumerate(notes):
        e = lambda s: html.escape(s, quote=False)
        vals = [e(n["de"]), e(n["en"]), e(n["hint"]), e(n["s_en"]), e(n["s_de"]), e(n["tip"]), e(n["badge"]), n["page"], n["stil"]]
        key = f"GL1|{n['deck']}|{n['en']}|{n['de']}"
        assert key not in seen, key; seen.add(key)
        guid = hashlib.sha1(key.encode()).hexdigest()[:10]
        sub = n["deck"].split("::")[1:]
        tags = " ".join(["GL1"] + [re.sub(r"[^a-z0-9]+", "", "_".join(sub[:k+1]).lower().replace(" ", "")) for k in range(len(sub))])
        sf = n["de"]; csum = int(hashlib.sha1(sf.encode()).hexdigest()[:8], 16)
        c.execute("INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,0,'')", (base + i, guid, MODEL_ID, now, -1, f" {tags} ", "\x1f".join(vals), sf, csum))
        c.execute("INSERT INTO cards VALUES (?,?,?,0,?,-1,0,0,?,0,0,0,0,0,0,0,0,'')", (base + i, base + i, did_for(n["deck"]), now, i + 1))
    db.commit(); db.close()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, "collection.anki2"); z.writestr("media", "{}")
    os.remove(tmp)
    from collections import Counter
    for d, k in sorted(Counter(n["deck"] for n in notes).items()): print(f"{k:4d}  {d}")
    print(f"{len(notes)} Karten -> {OUT}")

main()
