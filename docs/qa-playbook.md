# QA Playbook

Every defect class observed across three full-book production runs (~1,100 output pages),
with reproduction, detection, and fix. Run `pdf_qa.py render <temp_dir> --iteration N` on
every build; treat this document as the triage manual for its findings.

## Finding classes

### md_leak (markdown printed as literal text)

**Symptom**: `**PERNYATAAN MISI*` appears in the PDF. Detected by pdf_qa as
`md_leak:bold_asterisks` on a rendered page.

**Root causes seen**:

1. **Fixed-column table shifted.** A pandoc fixed-column table whose rows drifted by a few
   spaces fails to parse; pandoc emits the rows as plain text, asterisks included. The table
   looked aligned in the source chunk but used two different space-counts per column.
2. **Bold span broken across a blank line.** `**pola pikir\n\n*craftsmen***` — the `**`
   opener is separated from its closer by a paragraph break; pandoc renders everything
   literally.

**Fix**: convert the table to a pipe table (`| A | B |` rows) — pipe tables tolerate
whitespace drift. For broken bold spans, merge the span onto one line. Both fixes are
content-level (edit the specific `output_chunkNNNN.md`), then:
`pdf_qa.py clean <temp_dir>` and rebuild — the build is mtime-based and will not pick up
content fixes without the clean step for template-only changes, but a newer chunk triggers
re-merge automatically.

### overlong_token

**Symptom**: flagged on endnote/bibliography pages containing bare URLs
(`www.youtube.com/watch?time_continue=...`). Usually **benign** — CSS `overflow-wrap`
handles most; check the rendered page once to confirm nothing bleeds past the margin.
If a URL does overflow, wrap it in a zero-width-space-permitted span or shorten the line.

### near_blank

**Symptom**: page renders with text_len < 20. In practice these are:

- Section-divider pages (part openers, chapter title pages) — **benign by design** in most
  trade books. Expected count: one per chapter/part. A near_blank page count wildly
  inconsistent with the chapter count is a real problem (usually a dropped image or a
  failed chapter break).
- Cover/legal pages with only an image or ISBN line — benign.

**Triage rule**: compare the near_blank page list against the book's divider pages. Only
investigate pages that are *not* dividers.

### Image reference drift

**Symptom**: build warning `missing ![](path)` or build succeeds but images silently vanish
(PDF size drops by an order of magnitude — a 2.9 MB book became 604 KB once because the
`images/` directory didn't survive a temp-dir copy).

**Fix**: always verify image parity before QA:

```bash
grep -h '^!\[\]' chunk*.md | sort -u | wc -l
grep -h '^!\[\]' output_chunk*.md | sort -u | wc -l
```

When copying/deriving a temp directory, `cp -r` the images too. A >50% PDF size drop versus
the previous build is an automatic red flag.

### Escaped-dollar artifacts

**Symptom**: `\$6,000` printed literally. Calibre escapes `$` as `\$` during PDF→Markdown
conversion; pandoc then eats the `$` but prints the backslash.

**Fix**: global sweep over output chunks:
`sed -i 's/\\\\\$/\$/g' output_chunk*.md` (verify with `grep -c '\\\$'`). Cheaper than
fixing at build time and it is idempotent.

### Duplicated source fragments

**Symptom**: "(January 2020). (January 2020)." — the duplication existed in the source
chunk (conversion artifact), not a translation error.

**Fix**: dedup in the specific chunk; check the corresponding `chunkNNNN.md` to confirm the
source was the culprit before blaming the agent.

### Seam word duplication (chunk boundary artifact)

**Symptom**: the last words of one chunk's translation repeat at the head of the next —
"... grows the compounding effect" | "The compounding effect of tiny habits ...". Unlike
the class above, the source chunks are clean: parallel agents translate each chunk with
fresh context and the overlap is introduced at the seam. Cost-of-defect class: like
terminology drift — silent, cumulative, invisible to rendered-page QA (each page looks fine).

**Detection**: `python3 scripts/check_seams.py <temp_dir>` before merge. It reports
`ARTIFACT` (agent error) vs `SOURCE-DUP` (conversion artifact — route to the class above).
Report-only by design; fix is a content edit to the head of the later `output_chunkNNNN.md`.

### Word-count drift (agent paraphrased away or invented content)

**Symptom**: a translated chunk lands far below or above its source word count —
summarization, truncation, or hallucinated content that byte-size checks miss (paraphrase
keeps byte length similar).

**Detection**: automatic — `manifest.py validate_for_merge` warns when an output is <50% or
>200% of its source words (chunks under ~50 source words are exempt: structural chunks
legitimately shrink). Warning only; a legit dialogue-heavy or table-heavy chunk can trip it,
so read the chunk before re-dispatching.

### Running-header capture bug

**Symptom**: every page's running header shows one stale word ("Untuk" — the dedication
page's title) for hundreds of pages. Root cause: chapter titles in this book were styled
as **bold paragraphs**, not headings, so the CSS `string(chapter-title)` never updated.

**Fix**: if your book's headings are broken in the same way, either disable the running
header (`@top-center { content: none; }` in `template_print.html`) or fix the headings in
the chunks before build. The header-on-every-page defect is a template concern, not content.

### Heredoc write failures (agent-side, not build-side)

Agents writing translations through `wsl.exe … << 'EOF'` occasionally hit parse errors and
write truncated files. The reliable pattern: write the file to a Windows scratch directory,
then `cp` into the WSL filesystem. Verify with `head -3` + `wc -w` on the WSL side after
every write. (Relevant for Windows+WSL2 hosts.)

## Build-order rules

1. Never trust a build whose PDF size moved >50% in either direction.
2. Never run merge with missing `output_chunk*.md` — manifest validation blocks it; do not
   bypass.
3. After template edits: `pdf_qa.py clean` before rebuild.
4. After content edits to a chunk: rebuild re-merges automatically (mtime check).
5. Sample at least 3 random pages with `pdftotext` for a language sanity read — programmatic
   checks catch structure, not prose quality.

## Cost-of-defect ranking (where to spend attention)

1. md_leak — ships visible garbage; blocks release.
2. Image drift — silent (no error), destroys the book's value; caught only by size checks.
3. Terminology drift — silent, cumulative across chunks; caught only by glossary governance.
4. overlong_token / near_blank — usually benign; triage, don't fix reflexively.
