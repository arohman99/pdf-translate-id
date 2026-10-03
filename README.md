# pdf-translate-id

Battle-tested book-translation pipeline: **EPUB/PDF/DOCX → Markdown chunks → parallel LLM agents → print-quality PDF**.

Proven on 3 full commercial books (1,100+ output pages, ~160k words translated EN→ID), including
two 200-page titles with dense endnote/bibliography sections — with an audit trail of every
failure mode encountered and fixed along the way.

> Language pair in production: English → Indonesian. The pipeline is language-agnostic:
> prompts, glossary and style rules live in one style guide you edit for your own pair.

---

## Why another translator?

Existing tools fail in three predictable ways. Each one cost us real hours; each has a
concrete fix here.

| Failure mode | What happens | Fix in this repo |
|---|---|---|
| **Terminology drift** | 8 parallel agents each invent their own translation of "compounding" | `glossary.py` + frozen glossary table injected into every prompt |
| **Structural pages dropped** | Chapter dividers, copyright, acknowledgments silently skipped | `preclassify.py` routes structural chunks to one light batch instead of full LLM dispatch — *translated, never dropped* |
| **Markdown leaks into PDF** | `**PERNYATAAN MISI*` printed as literal text; fragile fixed-column tables collapse | `pdf_qa.py` renders pages and fails the build on leaks; pipeline includes a fixed-column → pipe-table converter path |

Plus two throughput problems nobody warns you about:

- **Fixed-range dispatch** (chunks 1–10, 11–20, …) makes every wave wait for the slowest agent.
  `split_dispatch.py` balances tasks by word count instead (measured: 1h04m → 35m on a mixed book).
- **Small chunks are overhead bombs.** 200 tiny chunks = 200×(read+write+verify) round-trips.
  The pipeline is chunk-size aware, and structural chunks never hit the LLM queue.

---

## Pipeline

```
EPUB/PDF/DOCX
   │  Calibre ebook-convert → HTMLZ → pandoc
   ▼
chunk*.md  (≈6000 chars, SHA-256 tracked in manifest.json)
   │
   ▼
preclassify.py ──► body          (full translation, parallel agents)
   │             ├─ notes_biblio (light pass: headings + narrative only; citations stay EN)
   │             └─ structural   (chapter titles/dividers → ONE batch file, one agent)
   ▼
split_dispatch.py ──► balanced task plan (~equal word-weight per agent)
   ▼
merge_and_build.py ──► output.md → HTML → WeasyPrint PDF (6×9 print template)
   ▼
pdf_qa.py ──► renders sample pages, flags md_leak / near_blank / overlong_token
   │          build fails on markdown leaks
   ▼
final PDF (+ DOCX/EPUB optional)
```

---

## Results (real runs)

| Book | Pages | Chunks | Time | Notes |
|---|---|---|---|---|
| The Psychology of Money | 242→345 | 55 | 28 min | baseline run |
| Essentialism | ~260→425 | 200 | 103 min | pre-optimization; endnote-heavy |
| So Good They Can't Ignore You | 184→373 | 115 | **45 min** | full optimized pipeline (V3) |

Quality gates enforced on every build:

- `0 markdown leaks` (rendered-page inspection)
- image reference parity source↔output
- terminology locked by a master glossary (user-approved, versioned)
- no silent structural-page drops

---

## Setup

Requirements: Python 3.10+, [Calibre](https://calibre-ebook.com/) (`ebook-convert`), `pandoc`,
and WeasyPrint (`pip install weasyprint`). On Windows, WSL2 is recommended for the toolchain
(all commands are plain bash + python; see `docs/wsl2-setup.md`).

```bash
# Ubuntu/WSL2
sudo apt install pandoc calibre
pip install weasyprint

# verify toolchain
which ebook-convert pandoc && python3 -c "import weasyprint"
```

Clone, then point the scripts at any input file:

```bash
git clone https://github.com/<you>/pdf-translate-id.git
cd pdf-translate-id
```

---

## Usage

The pipeline is agent-agnostic: steps 3–4 (translation) are executed by your AI coding agent
(Claude Code, Codex, or any orchestrator that can run bash), while all other steps are plain
deterministic Python you can run yourself.

```bash
# 1. chunk the book
python3 scripts/convert.py book.epub --olang id --temp-root ./runs

# 2. classify chunks (body / notes_biblio / structural)
python3 scripts/preclassify.py runs/book_temp

# 3. balance the dispatch plan
python3 scripts/split_dispatch.py runs/book_temp --agents 10
#    → runs/book_temp/dispatch_plan.json: chunk lists per agent

# 4. translate: run agents per dispatch_plan task.
#    Each agent: read chunkNNNN.md → translate → write output_chunkNNNN.md
#    Prompt template + style guide: docs/style-guide.md
#    Structural batch (runs/book_temp/structural_batch.md) → one agent, then:
python3 scripts/preclassify.py runs/book_temp --apply structural_translated.md

# 5. build + QA
python3 scripts/merge_and_build.py --temp-dir runs/book_temp \
    --title "Judul Buku" --author "Penulis" --pdf-only
python3 scripts/pdf_qa.py render runs/book_temp --iteration 1
#    fix any findings (see docs/qa-playbook.md), then rebuild
```

---

## The style guide (the part that actually matters)

Translation quality lives or dies on constraints, not on the model. `docs/style-guide.md`
contains the full rule set we converged on for EN→ID, distilled from professional
localization guides (Microsoft Indonesian Style Guide, KBBI V, EYD 2016):

- **Term governance**: a frozen master glossary. Term decisions belong to the reader, not the
  translator — and they are made *before* the first agent runs, not audited after.
- **Natural register over literal fidelity**: sentence restructuring rules, idiom handling
  (move the meaning, never the wording), short-word preferences.
- **Numeric conventions**: decimal commas, thousands dots, currency formats — regex-checkable.
- **Proven pitfalls**: the "pemandi parkir" class of errors (literal calques that produce
  nonsense words) with the corrected renderings.

If you translate into another language, keep the structure, swap the examples, and pin your
own glossary before dispatching a single agent.

---

## QA playbook

`docs/qa-playbook.md` documents every defect class we have hit so far, with reproduction and
fix: markdown leaks from shifted fixed-column tables, image-reference drift between
source/output, running-header capture bugs (chapter titles extracted as bold paragraphs),
escaped-`\$` artifacts from Calibre, overlong tokens in endnote URLs, and near-blank pages
that are actually section dividers (benign — know the difference before "fixing" them).

---

## Project structure

```
scripts/
  convert.py           EPUB/PDF/DOCX → HTMLZ → Markdown chunks (+ manifest, page-number LNDS filter)
  preclassify.py       chunk classifier: body / notes_biblio / structural (+ batch apply mode)
  split_dispatch.py    word-weight-balanced dispatch planner
  glossary.py          glossary v2: aliases, categories, frequency counting
  chunk_context.py     read-only neighbor excerpts for cross-chunk coherence
  merge_and_build.py   manifest-validated merge → HTML → WeasyPrint PDF
  pdf_qa.py            page render + programmatic findings (md_leak, near_blank, overlong_token)
  manifest.py          SHA-256 chunk tracking and merge validation
  run_state.py         resume state (skip already-translated chunks)
  template_print.html  6×9 print CSS (Navy/Gold, DejaVu Serif + Lato)
docs/
  style-guide.md       EN→ID register rules + master glossary
  qa-playbook.md       every defect class seen so far, with fixes
  wsl2-setup.md        Windows toolchain notes (Hyper-V, ext4 vhdx placement, sudo)
LICENSE                MIT (inherited from upstream)
```

---

## Attribution

Built on [trananhtung/translate-book](https://github.com/trananhtung/translate-book)
(fork of [deusyu/translate-book](https://github.com/deusyu/translate-book), itself inspired by
[wizlijun/claude_translater](https://github.com/wizlijun/claude_translater)). MIT license preserved.

Additions in this repo: chunk pre-classification, weight-balanced dispatch, structural batch
mode, master-glossary governance, EN→ID style guide, and the QA playbook distilled from three
full-book production runs.

---

## Roadmap

- [ ] Placeholder-mode translation (tags never reach the model → leaks impossible by construction)
- [ ] Judge pass: per-chapter re-read + polish agent (multi-pass self-correction)
- [ ] Bilingual side-by-side EPUB output (EN|ID interleaved paragraphs)
- [ ] `--dry-run` cost estimator (tokens + wall-clock, per dispatch plan)
- [ ] Language-pack presets beyond EN→ID

Contributions welcome — especially benchmark runs on other language pairs. Please include
page/chunk counts and QA output with PRs.
