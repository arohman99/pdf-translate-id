#!/usr/bin/env python3
"""preclassify.py — Klasifikasi chunk SEBELUM dispatch LLM.

Tujuan: jangan buang token/waktu LLM untuk chunk yang tidak butuh LLM penuh.
Berbasis pola terbukti dari job Essentialism + Psikologi Uang + referensi
fredchu/book-translator (structural pages = deterministic contracts).

Kategori:
  skip_verbatim  — chunk struktural murni (judul bab/divider/TOC mini):
                   disalin 1:1 ke output_chunk*.md TANPA LLM.
                   Aman karena isinya marker markdown, bukan prosa.
  notes_biblio   — mayoritas sitasi bibliografi: LLM hanya translate heading +
                   kalimat naratif; sitasi tetap EN (konvensi sudah terbukti).
  body           — prosa utuh: terjemahan penuh dengan style guide.

Output: classification.json di temp dir + salinan otomatis untuk skip_verbatim.
Usage:
  python3 preclassify.py <temp_dir>            # klasifikasi + salin skip
  python3 preclassify.py <temp_dir> --dry-run  # hanya laporan
Exit code 0 selalu kecuali error fatal (fail-closed on crash, bukan on findings).
"""
import json
import os
import re
import shutil
import sys

MIN_BODY_WORDS = 60          # di bawah ini = struktur, bukan prosa
MIN_PROSE_CHARS = 150        # di bawah ini = hampir tak ada prosa (judul/divider)
NOTES_RATIO = 0.5            # >50% baris sitasi/URL = notes_biblio
MARKUP_DENSITY_THRESHOLD = 8 # rata-rata markup-anchor per 100 kata

CITE_PAT = re.compile(
    r'(https?://|www\.|\{\.hlink\}|\[\^\d+\^\]|Ibid\.|Press\s|University\s|'
    r'Retrieved|vol\.\s|\b19\d\d\b|\b20\d\d\b)'
)


def stats(text: str) -> dict:
    words = len(text.split())
    lines = [l for l in text.split('\n') if l.strip()]
    cite_lines = sum(1 for l in lines if CITE_PAT.search(l))
    markup = len(re.findall(r'(\[\^|\.hlink|\{\.|\\\[\]|!\[\])', text))
    # prosa = baris yang bukan heading/marker/gambar/tabel-bar
    prose_chars = sum(
        len(l) for l in lines
        if not l.strip().startswith(('#', '!', '|', '-', '>', '['))
        and not re.match(r'^\s*[-_=]{10,}\s*$', l)
    )
    return {
        'words': words,
        'lines': len(lines),
        'cite_lines': cite_lines,
        'cite_ratio': cite_lines / len(lines) if lines else 0,
        'markup_per_100w': markup / words * 100 if words else 0,
        'prose_chars': prose_chars,
    }


def classify(path: str) -> tuple[str, dict]:
    text = open(path, encoding='utf-8').read()
    s = stats(text)

    # 1) Struktural murni: kata sedikit DAN hampir tanpa prosa
    #    (prosa substantif walau pendek harus tetap diterjemahkan -> batch)
    if s['words'] <= MIN_BODY_WORDS and s['prose_chars'] < MIN_PROSE_CHARS:
        return 'skip_verbatim', s
    # 2) Notes/bibliografi: dominasi sitasi atau markup ekstrem
    if s['cite_ratio'] >= NOTES_RATIO or s['markup_per_100w'] > MARKUP_DENSITY_THRESHOLD * 3:
        return 'notes_biblio', s
    # 3) Prosa utuh
    return 'body', s


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    apply_file = None
    if '--apply' in sys.argv:
        i = sys.argv.index('--apply')
        apply_file = sys.argv[i + 1]
    if not args:
        print('usage: preclassify.py <temp_dir> [--dry-run] [--apply batch_translated.md]')
        return 2
    temp_dir = os.path.abspath(args[0])

    # MODE APPLY: terjemahan batch struktural -> tulis output_chunk*.md
    if apply_file:
        batch = open(apply_file, encoding='utf-8').read()
        blocks = re.split(r'^=== (chunk\d+)\s*===\s*$', batch, flags=re.M)
        applied = 0
        i = 1
        while i + 1 < len(blocks) + 1 and i + 1 <= len(blocks) - 1:
            name, content = blocks[i], blocks[i + 1]
            out_path = os.path.join(temp_dir, 'output_' + name + '.md')
            with open(out_path, 'w', encoding='utf-8') as fh:
                fh.write(content.strip() + '\n')
            applied += 1
            i += 2
        print(f'applied {applied} structural translations')
        return 0

    chunk_files = sorted(
        f for f in os.listdir(temp_dir)
        if re.match(r'^chunk\d+\.md$', f)
    )
    if not chunk_files:
        print(f'ERROR: tidak ada chunk*.md di {temp_dir}')
        return 1

    result = {'version': 2, 'categories': {}, 'stats': {}}
    counts = {'skip_verbatim': 0, 'notes_biblio': 0, 'body': 0}
    structural_batch = []   # kumpulkan untuk satu batch LLM ringan
    for f in chunk_files:
        cat, s = classify(os.path.join(temp_dir, f))
        out_name = 'output_' + f
        result['categories'][f] = {'category': cat, 'output': out_name}
        result['stats'][f] = s
        counts[cat] += 1
        if cat == 'skip_verbatim' and not dry:
            src = os.path.join(temp_dir, f)
            dst = os.path.join(temp_dir, out_name)
            if not os.path.exists(dst):          # idempotent, jangan timpa
                shutil.copyfile(src, dst)
            text = open(src, encoding='utf-8').read().strip()
            if text:
                structural_batch.append(f'=== {f[:-3]} ===\n{text}')

    out_path = os.path.join(temp_dir, 'classification.json')
    if not dry:
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(result, fh, indent=1, ensure_ascii=False)
        if structural_batch:
            batch_path = os.path.join(temp_dir, 'structural_batch.md')
            with open(batch_path, 'w', encoding='utf-8') as fh:
                fh.write(
                    '# TERJEMAHKAN ke Bahasa Indonesia (gaya natural, judul buku/istilah'
                    ' Essentialist tetap EN italic, angka tetap). Jangan menambah komentar.'
                    ' Pertahankan markup markdown persis.\n\n'
                    + '\n\n'.join(structural_batch)
                )

    print(f'chunks: {len(chunk_files)}')
    print(f'  body          : {counts["body"]}')
    print(f'  notes_biblio  : {counts["notes_biblio"]}')
    print(f'  structural    : {counts["skip_verbatim"]} (1 batch ringan, bukan {counts["skip_verbatim"]} dispatch)')
    print(f'LLM dispatch needed: gel 1={max(1,(counts["body"]+counts["notes_biblio"])//10)}'
          f' + 1 agent struktural')
    if not dry:
        print(f'written: {out_path}')
        if structural_batch:
            print(f'written: {os.path.join(temp_dir, "structural_batch.md")}')
        for f, meta in result['categories'].items():
            if meta['category'] == 'skip_verbatim':
                print(f'  structural: {f} ({result["stats"][f]["words"]} kata)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
