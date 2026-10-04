#!/usr/bin/env python3
"""check_seams.py — detect duplicated words at chunk boundaries (translation artifacts).

Why: parallel agents translate chunk N and N+1 with fresh contexts, so the seam
between them can repeat words ("... the compounding effect" | "The compounding
effect of habits ..."). Borrowed from a production format-preserving PDF
translation pipeline where line seams were the top residual artifact class.

Report-only by design (CONTRIBUTING: silent partial writes are the worst
failure class — a human or the orchestrating agent decides what to edit).
Exit code 0 unless a fatal error; findings are findings, not failures
(same contract as preclassify.py). Cross-checks the SOURCE chunks: when the
source duplicates too, it is a conversion artifact ("Duplicated source
fragments" in docs/qa-playbook.md), not agent error.

Usage:
  python3 check_seams.py <temp_dir>   # compare output_chunkNNNN.md seams
  python3 check_seams.py --selftest   # run built-in checks, no files needed
"""
import os
import re
import sys

# ponytail: Latin-script word regex (EN->ID pair); extend for other scripts
# if this pipeline grows beyond them.
_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def words(text):
    return _WORD_RE.findall(text.lower())


def seam_overlap(tail_words, head_words, max_k=3):
    """Largest k in (max_k..1] where the tail's last k words equal the head's first k."""
    for k in range(max_k, 0, -1):
        if len(tail_words) >= k and len(head_words) >= k and tail_words[-k:] == head_words[:k]:
            return k
    return 0


def classify_seam(a_out, b_out, a_src, b_src):
    """Return (overlap, verdict) where verdict is 'artifact' | 'source' | None."""
    k = seam_overlap(words(a_out), words(b_out))
    if not k:
        return 0, None
    src_dup = seam_overlap(words(a_src), words(b_src), max_k=k) == k
    return k, ('source' if src_dup else 'artifact')


def _chunk_key(name):
    m = re.match(r'^chunk(\d+)\.md$', name)
    return (int(m.group(1)) if m else 0, name)


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def _selftest():
    # clean seam: no false positive
    assert classify_seam('end of chapter one', 'chapter two begins',
                         'end of chapter one', 'chapter two begins') == (0, None)
    # 2-word artifact, source clean
    assert classify_seam('effect of money', 'of money grows',
                         'effect of money', 'money grows') == (2, 'artifact')
    # 3-word artifact
    assert classify_seam('the compounding effect', 'the compounding effect compounds',
                         'the compounding effect', 'effect compounds') == (3, 'artifact')
    # same overlap but the source duplicates too -> conversion artifact
    assert classify_seam('effect of money', 'of money grows',
                         'effect of money', 'of money grows') == (2, 'source')
    print('selftest OK (4 cases)')


def main():
    if '--selftest' in sys.argv:
        _selftest()
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print('usage: check_seams.py <temp_dir> | --selftest')
        return 2
    temp_dir = os.path.abspath(args[0])
    if not os.path.isdir(temp_dir):
        print(f'ERROR: not a directory: {temp_dir}')
        return 1
    chunks = sorted(
        (f for f in os.listdir(temp_dir) if re.match(r'^chunk\d+\.md$', f)),
        key=_chunk_key,
    )
    if not chunks:
        print(f'ERROR: no chunk*.md in {temp_dir}')
        return 1

    checked = skipped = artifacts = sources = 0
    for i in range(len(chunks) - 1):
        a_src = os.path.join(temp_dir, chunks[i])
        b_src = os.path.join(temp_dir, chunks[i + 1])
        a_out = os.path.join(temp_dir, 'output_' + chunks[i])
        b_out = os.path.join(temp_dir, 'output_' + chunks[i + 1])
        if not (os.path.exists(a_out) and os.path.exists(b_out)):
            skipped += 1
            continue
        checked += 1
        k, verdict = classify_seam(_read(a_out), _read(b_out), _read(a_src), _read(b_src))
        if not verdict:
            continue
        pair = f'{chunks[i]} -> {chunks[i + 1]}'
        if verdict == 'artifact':
            artifacts += 1
            ta, tb = ' '.join(words(_read(a_out))[-3:]), ' '.join(words(_read(b_out))[:3])
            print(f'ARTIFACT {pair}: tail "...{ta}" | head "{tb}..." (overlap {k})')
        else:
            sources += 1
            print(f'SOURCE-DUP {pair}: overlap {k}, source chunks duplicate too '
                  f'(conversion artifact, see qa-playbook "Duplicated source fragments")')

    print(f'chunks: {len(chunks)} | seams checked: {checked} | '
          f'skipped (missing output): {skipped}')
    print(f'agent artifacts: {artifacts} | source duplicates: {sources}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
