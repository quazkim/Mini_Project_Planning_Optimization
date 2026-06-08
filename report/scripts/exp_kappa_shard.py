#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Khảo sát κ = U·M cho 1 shard instance (chạy song song trên GitHub Actions).

Mỗi shard nhận một phần các instance (chia round-robin theo N giảm dần để cân tải),
chạy Greedy → Local Search → ALNS (cùng time-limit) và ghi lại:
  instance, N, M, greedy, U=N-greedy, kappa=U*M, ls, alns, delta=alns-ls, winner.
Không dùng CP-SAT nên không cần OR-Tools.

Biến môi trường:
  SHARD        : chỉ số shard (0..SHARD_TOTAL-1)
  SHARD_TOTAL  : tổng số shard
  KAPPA_TL     : time-limit (giây) cho mỗi thuật toán (mặc định 15)
  KAPPA_SEEDS  : danh sách seed, cách nhau dấu phẩy (mặc định "1,7")
"""

from __future__ import annotations

import glob
import json
import os
import random
import statistics as st
import sys

import common  # nạp project root vào sys.path
from solver.algorithms.greedy import solve_with_greedy
from solver.algorithms.local_search import optimize_with_local_search
from solver.algorithms.alns import optimize_with_alns

SHARD = int(os.environ.get("SHARD", sys.argv[1] if len(sys.argv) > 1 else 0))
TOTAL = int(os.environ.get("SHARD_TOTAL", sys.argv[2] if len(sys.argv) > 2 else 1))
TIME_LIMIT = float(os.environ.get("KAPPA_TL") or 15)
SEEDS = [int(x) for x in (os.environ.get("KAPPA_SEEDS") or "1,7").split(",")]
BIG = 10 ** 9


def _first_int(path: str) -> int:
    with open(path) as f:
        return int(f.read().split()[0])


def main():
    files = glob.glob(os.path.join(common.TEST_DIR, "*.txt"))
    names = [os.path.splitext(os.path.basename(p))[0] for p in files]
    # Sắp theo N giảm dần rồi chia round-robin -> cân tải giữa các shard.
    names.sort(key=lambda nm: -_first_int(os.path.join(common.TEST_DIR, nm + ".txt")))
    mine = [nm for i, nm in enumerate(names) if i % TOTAL == SHARD]
    print(f"[shard {SHARD}/{TOTAL}] {len(mine)} instance, TL={TIME_LIMIT}s, seeds={SEEDS}: {mine}",
          flush=True)

    rows = []
    for nm in mine:
        N, M, classes, rooms = common.load_instance(nm)
        g = solve_with_greedy(N, M, classes, rooms)
        U = N - len(g)
        ls_q, al_q = [], []
        for sd in SEEDS:
            random.seed(sd)
            N, M, classes, rooms = common.load_instance(nm)
            gg = solve_with_greedy(N, M, classes, rooms)
            ls_q.append(len(optimize_with_local_search(
                N, M, classes, rooms, gg, max_iters=BIG, time_limit=TIME_LIMIT)))
            random.seed(sd)
            N, M, classes, rooms = common.load_instance(nm)
            gg = solve_with_greedy(N, M, classes, rooms)
            al_q.append(len(optimize_with_alns(
                N, M, classes, rooms, gg, max_iters=BIG, time_limit=TIME_LIMIT)))
        lsa, ala = st.mean(ls_q), st.mean(al_q)
        delta = ala - lsa
        rows.append({
            "instance": nm, "N": N, "M": M, "greedy": len(g),
            "U": U, "kappa": U * M, "ls": lsa, "alns": ala,
            "delta": delta,
            "winner": "ALNS" if delta > 0 else ("LS" if delta < 0 else "tie"),
        })
        print(f"  {nm:10s} N={N:4d} M={M:3d} U={U:4d} kappa={U*M:6d} "
              f"LS={lsa:.1f} ALNS={ala:.1f} -> {rows[-1]['winner']}", flush=True)

    os.makedirs("kappa_out", exist_ok=True)
    out = os.path.join("kappa_out", f"kappa_shard_{SHARD}.json")
    with open(out, "w") as f:
        json.dump(rows, f, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
