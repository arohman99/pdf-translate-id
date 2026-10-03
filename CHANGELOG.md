# Changelog

## 1.0.0 — 2026-10-04

First public release. Battle-tested on three full commercial books (EN→ID):
1,100+ output pages, ~160k words, zero dropped structural pages.

### Added (on top of upstream translate-book)

- `preclassify.py`: chunk classifier (body / notes_biblio / structural) with a
  structural-batch mode — 12–38 structural chunks collapse into one light agent
  task instead of full LLM dispatches. Validated A/B against a 200-chunk book.
- `split_dispatch.py`: word-weight-balanced dispatch planning (notes_biblio
  weighted 1.4×). Removes the fixed-range dispatch problem where every wave
  waited on the slowest agent.
- EN→ID style guide with a frozen master glossary
  (`docs/style-guide.md`), distilled from professional localization guides
  and three production runs.
- QA playbook (`docs/qa-playbook.md`) documenting every defect class hit so
  far: markdown leaks from shifted fixed-column tables, image-reference
  drift, escaped-`$` conversion artifacts, running-header capture bugs,
  benign vs real near-blank pages.
- WSL2 host notes (`docs/wsl2-setup.md`).
- `--pdf-only` and the 6×9 print template inherited from upstream.

### Fixed (upstream defects encountered in production)

- Fixed-column table drift no longer silently produces markdown leaks in the
  final PDF (detection via rendered-page QA; fix path documented).
- Image-reference parity check (source vs output) added to the standard
  pre-build verification after a temp-dir copy dropped an entire images/
  directory and produced a figure-less book.

### Security

- No API keys or book content in the repo; `.gitignore` blocks runs/, ebooks,
  PDFs, and scratch directories by default.
