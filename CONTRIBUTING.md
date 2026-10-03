# Contributor notes

## Code conventions

- Scripts are stdlib-only Python (no pip dependencies outside the toolchain binaries).
  If you need a package, argue for it in the PR — the portability budget is small.
- Every script is runnable standalone with `--help`; no hidden global state.
- Fail closed on corruption: if output can't be verified, leave the old file in place
  and exit non-zero. Silent partial writes are the worst failure class here.

## PR checklist

- [ ] Tested on a real book (state pages/chunks/words in the PR body)
- [ ] `pdf_qa.py` output included (before/after if fixing a defect)
- [ ] No breaking changes to the manifest.json / classification.json schemas —
      bump the `version` field instead and handle both
- [ ] Docs updated (`docs/qa-playbook.md` for new defect classes, `docs/style-guide.md`
      for terminology decisions — term changes need a rationale, "sounds better" is fine
      but say so)
- [ ] No book content, API keys, or personal paths in committed files
      (`.gitignore` covers `runs/`, `*.epub`, `*.pdf`, scratch dirs)

## Non-goals

- No GUI. This is a pipeline for people comfortable with a terminal.
- No scraping/DRM circumvention. Bring books you legitimately own.
- No model-specific code in the deterministic scripts — translation is the agent's job;
  these scripts only manage structure, state, and QA.
