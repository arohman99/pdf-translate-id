#!/usr/bin/env python3
"""split_dispatch.py — Bagi chunk 'body'+'notes_biblio' menjadi N task seimbang.

Masalah yang dipecahkan: dispatch per-range tetap (chunk 1-10, 11-20...) membuat
gelombang menunggu agent terlambat (critical path = chunk terlambat). Dengan
membagi berdasarkan BOBOT kata, tiap task dapat bekerja setara -> load balancing.

Usage:
  python3 split_dispatch.py <temp_dir> --agents 10
Output:
  <temp_dir>/dispatch_plan.json  -> daftar task, tiap task = daftar chunk
  cetak ringkasan + prompt siap pakai per task (disimpan juga ke dispatch_plan.json)
"""
import json
import os
import re
import sys


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('usage: split_dispatch.py <temp_dir> --agents N')
        return 2
    temp_dir = os.path.abspath(args[0])
    agents = 10
    if '--agents' in args:
        agents = int(args[args.index('--agents') + 1])

    cls_path = os.path.join(temp_dir, 'classification.json')
    if not os.path.exists(cls_path):
        print('ERROR: jalankan preclassify.py dulu')
        return 1
    cls = json.load(open(cls_path, encoding='utf-8'))

    # ambil hanya chunk yang butuh LLM, urut, dengan bobot kata
    items = []
    for f, meta in cls['categories'].items():
        if meta['category'] == 'skip_verbatim':
            continue
        words = cls['stats'][f]['words']
        # notes_biblio lebih berat per kata (hati-hati markup) -> bobot 1.4x
        weight = words * (1.4 if meta['category'] == 'notes_biblio' else 1.0)
        items.append((f, words, weight))
    items.sort(key=lambda x: x[0])

    total = sum(w for _, _, w in items)
    target = total / agents

    # greedy: isi task berurutan sampai mendekati target (urut chunk = urutan baca tetap terjaga per task)
    tasks = [[] for _ in range(agents)]
    loads = [0.0] * agents
    ti = 0
    for f, words, weight in items:
        # pindah task berikutnya kalau task ini sudah >= target dan masih ada sisa task
        if loads[ti] >= target and ti < agents - 1:
            ti += 1
        tasks[ti].append(f)
        loads[ti] += weight

    plan = {
        'version': 1,
        'agents': agents,
        'total_chunks': len(items),
        'total_words': sum(w for _, w, _ in items),
        'tasks': [
            {'task': i + 1, 'chunks': t, 'words': sum(w for f, w, _ in items if f in t)}
            for i, t in enumerate(tasks)
        ],
    }
    out = os.path.join(temp_dir, 'dispatch_plan.json')
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(plan, fh, indent=1, ensure_ascii=False)

    print(f'total LLM chunks: {len(items)} | agents: {agents}')
    for t in plan['tasks']:
        first, last = t['chunks'][0], t['chunks'][-1]
        print(f"  task {t['task']:>2}: {len(t['chunks']):>2} chunk ({first}..{last}) ~{t['words']} kata")
    print(f'written: {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
