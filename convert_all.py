#!/usr/bin/env python3
"""Batch convert tất cả file .ctt trong datasets/ sang format bài toán, lưu vào input_data/"""

import os
from ctt_to_input import convert

SRC_DIR = "datasets"
DST_DIR = "input_data"

os.makedirs(DST_DIR, exist_ok=True)

ctt_files = sorted(f for f in os.listdir(SRC_DIR) if f.endswith(".ctt"))

for fname in ctt_files:
    src = os.path.join(SRC_DIR, fname)
    dst = os.path.join(DST_DIR, fname.replace(".ctt", ".txt"))

    try:
        content = convert(src)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)

        first_line = content.splitlines()[0]
        N, M = first_line.split()
        print(f"OK  {fname:20s} -> {os.path.basename(dst)}  (N={N}, M={M})")
    except Exception as e:
        print(f"ERR {fname:20s} -> {e}")

print(f"\nĐã convert {len(ctt_files)} file vào '{DST_DIR}/'")
