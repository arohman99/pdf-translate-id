# Style Guide: EN → Indonesian (natural register)

Distilled from the Microsoft Indonesian Localization Style Guide, KBBI V (2016), EYD 2016,
and three full-book production runs. If you fork this pipeline for another language pair,
keep the structure, replace the examples, and pin your own glossary **before** dispatching.

## The one-sentence principle

Write as if an Indonesian writer re-expressed the idea — not as if an English sentence got
dressed in Indonesian words. Read it back: if it sounds like a good local magazine, it ships;
if it sounds like translated English, rewrite the sentence order.

## Hard rules

### 1. Everyday short words over formal registers

| Avoid (stiff) | Use (natural) |
|---|---|
| membutuhkan / memerlukan | butuh / perlu |
| pemutakhiran / mutakhirkan | pembaruan / perbarui |
| disarankan | sebaiknya |
| bagaimana cara membuat | cara membuat |
| telepon seluler | ponsel |

### 2. Kill ceremony

English "please" in declarative sentences disappears in Indonesian. "Please try again" →
"Coba lagi." Filler adverbs (actually / basically / really) are dropped unless meaningful.

### 3. Restructure, don't mirror

- "It is about X" → "Intinya X" — not "Ini adalah tentang X"
- Passive English ("X was created by Y") → active Indonesian ("Y menciptakan X")
- One idea per sentence. Split long branching English sentences; conjunctions opening a
  sentence (Lalu, Namun, Jadi) are correct and keep the narrative rhythm alive.

### 4. Idioms: move the meaning, never the wording

- "rat race" → "kejar-kejaran rutin" (never "perlombaan tikus")
- "chew you up and spit you out" → "melahap lalu memuntahkan Anda"
- "doesn't read well on a résumé" → "tidak menjual di CV"

If a literal rendering produces a nonsense word — the "pemandi parkir" class of error
(valet mistranslated as "parking washer") — it is a build blocker. Known-dangerous pairs:

| Source | Wrong (literal) | Right |
|---|---|---|
| valet | pemandi parkir | juru parkir |
| janitor | penjaga | juru bersih |

### 5. Foreign terms in italics

*hedge fund*, *trade-off*, *career capital*, *passion hypothesis* stay in English italics.
A short gloss in parentheses is allowed once, at first mention in a chapter, only when a
general reader needs it. Do not invent Indonesian compounds for established terms.

### 6. Numbers & currency

Decimal comma (1,5 juta), thousands dots (US$12.000), en dash in ranges (2008–2013).
Pick one currency style per book (US$12.000 or 12.000 dolar AS) and keep it.

### 7. Pronouns — one choice per book

Narrator "saya", reader "Anda", dialogue "aku". Mixing Anda/kamu inside one book is a defect.

## Master glossary (frozen decisions)

Term decisions belong to the reader, not the translator — lock them before the first agent
runs. Current table:

| EN | ID final |
|---|---|
| passion hypothesis | *passion hypothesis* (no Indonesian rendering) |
| career capital | *career capital* |
| craftsman mindset | pola pikir *craftsmen* |
| compounding (interest / growth) | bunga majemuk / pertumbuhan majemuk |
| tail events | peristiwa ekor (*tail events*) — English gloss once, at first mention |
| room for error | ruang untuk kesalahan |
| margin of safety | margin keamanan |
| less but better | lebih sedikit, tetapi lebih baik |
| deliberate practice | praktik yang disengaja (*deliberate practice*) |
| dream job | pekerjaan impian |
| adjacent possible | *adjacent possible* (kemungkinan bersebelahan) |

## QA checklist (run on every build)

1. Read 2–3 random paragraphs aloud: does it sound native?
2. Regex-sweep stiff patterns: `melakukan <noun>`, `dalam rangka`, `berdasarkan hal tersebut`.
3. Regex-sweep English residue: `\b(with|and|of|the|was)\b` (proper nouns and citations exempt).
4. Decimal-comma / thousands-dot sweep: `\d\.\d` and `\d,\d`.
5. Pronoun consistency (no Anda/kamu mixing).
6. Glossary terms present and consistent.
7. Markdown leak check on rendered pages (pdf_qa.py) — must be zero.
