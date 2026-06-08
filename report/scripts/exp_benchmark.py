#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHẦN 8 — Benchmark đối sánh CÔNG BẰNG: Greedy / Local Search / ALNS / CP-SAT.

Giao thức đánh giá công bằng (mục 8.1):
  - Ngân sách thời gian CHUNG ``TIME_LIMIT`` giây cho LS, ALNS và CP-SAT.
  - Bộ ``SEEDS`` cố định cho mọi thuật toán ngẫu nhiên (LS, ALNS) -> tái lập.
  - Mỗi instance nạp lại sạch trước mỗi lần chạy (không nhiễm trạng thái).
  - Ghi nhật ký môi trường (CPU/Python/OS) vào data/bench_env.json.
  - Thống kê (min, max, avg, std) trên các seed.
Ngoài bản LS chạy đủ ngân sách, ta ghi thêm ``ls_fast`` (LS hội tụ tự nhiên) để
minh chứng đặc tính "tức thời" của tầng Local Search.
"""

from __future__ import annotations

import json
import os
import platform
import random
import statistics as st
import time
from typing import Dict, List

import numpy as np

import common
from solver.algorithms.greedy import solve_with_greedy
from solver.algorithms.local_search import optimize_with_local_search
from solver.algorithms.alns import optimize_with_alns
from solver.algorithms.cp_sat import solve_with_cp_sat
from ortools.sat.python import cp_model

# --- Giao thức công bằng ---
TIME_LIMIT = 30.0            # ngân sách chung (giây) cho LS, ALNS, CP-SAT
SEEDS = [1, 7, 13, 21, 42]   # bộ seed cố định cho thuật toán ngẫu nhiên
BIG_ITERS = 10**9            # để time-limit là tiêu chí dừng thực sự
REPS = {"small": 3, "medium": 3, "large": 2}


def _stats(vals: List[float]) -> Dict[str, float]:
    return {
        "min": min(vals), "max": max(vals),
        "avg": st.mean(vals), "std": (st.pstdev(vals) if len(vals) > 1 else 0.0),
    }


def _log_env():
    env = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "ortools": _ortools_version(),
        "time_limit_s": TIME_LIMIT,
        "seeds": SEEDS,
        "reps": REPS,
    }
    with open(os.path.join(common.DATA_DIR, "bench_env.json"), "w") as f:
        json.dump(env, f, indent=2)
    return env


def _ortools_version():
    try:
        import ortools
        return ortools.__version__
    except Exception:
        return "n/a"


def bench_instance(name: str, size: str) -> dict:
    reps = REPS[size]
    rec = {"instance": name}
    N, M, classes, rooms = common.load_instance(name)
    rec["N"], rec["M"] = N, M

    # --- Greedy (tất định) ---
    t0 = time.time()
    g = solve_with_greedy(N, M, classes, rooms)
    rec["greedy"] = {"Q": len(g), "time": time.time() - t0}

    # --- Local Search: bản "tức thời" (hội tụ tự nhiên) ---
    lsf_q, lsf_t = [], []
    for k in range(reps):
        random.seed(SEEDS[k])
        N, M, classes, rooms = common.load_instance(name)
        gg = solve_with_greedy(N, M, classes, rooms)
        t0 = time.time()
        res = optimize_with_local_search(N, M, classes, rooms, gg, max_iters=2000)
        lsf_t.append(time.time() - t0)
        lsf_q.append(len(res))
    rec["ls_fast"] = {**_stats(lsf_q), "time": st.mean(lsf_t)}

    # --- Local Search: cùng ngân sách TIME_LIMIT (công bằng) ---
    ls_q, ls_t = [], []
    for k in range(reps):
        random.seed(SEEDS[k])
        N, M, classes, rooms = common.load_instance(name)
        gg = solve_with_greedy(N, M, classes, rooms)
        t0 = time.time()
        res = optimize_with_local_search(N, M, classes, rooms, gg,
                                         max_iters=BIG_ITERS, time_limit=TIME_LIMIT)
        ls_t.append(time.time() - t0)
        ls_q.append(len(res))
    rec["ls"] = {**_stats(ls_q), "time": st.mean(ls_t)}

    # --- ALNS: cùng ngân sách TIME_LIMIT ---
    al_q, al_t = [], []
    for k in range(reps):
        random.seed(SEEDS[k])
        N, M, classes, rooms = common.load_instance(name)
        gg = solve_with_greedy(N, M, classes, rooms)
        t0 = time.time()
        res = optimize_with_alns(N, M, classes, rooms, gg,
                                 max_iters=BIG_ITERS, time_limit=TIME_LIMIT)
        al_t.append(time.time() - t0)
        al_q.append(len(res))
    rec["alns"] = {**_stats(al_q), "time": st.mean(al_t)}

    # --- CP-SAT: cùng ngân sách TIME_LIMIT (gold standard / so sánh Exact) ---
    N, M, classes, rooms = common.load_instance(name)
    t0 = time.time()
    status, res = solve_with_cp_sat(N, M, classes, rooms, time_limit=TIME_LIMIT)
    rec["cpsat"] = {
        "Q": len(res), "time": time.time() - t0,
        "optimal": status == cp_model.OPTIMAL,
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else
                  ("FEASIBLE" if status == cp_model.FEASIBLE else "NONE"),
    }
    return rec


def main():
    plt = common.setup_matplotlib()
    env = _log_env()
    print("ENV:", env)
    all_rows = {}
    for size, names in common.INSTANCES.items():
        all_rows[size] = []
        for nm in names:
            print(f"[{size}] {nm} ...", flush=True)
            rec = bench_instance(nm, size)
            all_rows[size].append(rec)
            line = (f"   {nm:10s} N={rec['N']:4d} greedy={rec['greedy']['Q']:4d} "
                    f"LSfast={rec['ls_fast']['avg']:.1f} LS={rec['ls']['avg']:.1f} "
                    f"ALNS={rec['alns']['avg']:.1f} "
                    f"CPSAT={rec['cpsat']['Q']}({rec['cpsat']['status']})")
            print(line, flush=True)

    with open(os.path.join(common.DATA_DIR, "benchmark.json"), "w") as f:
        json.dump(all_rows, f, indent=2)

    _plot_small_quality(plt, all_rows["small"])
    _plot_large_gain(plt, all_rows["large"])
    _plot_runtime(plt, all_rows)
    print("benchmark done")


def _plot_small_quality(plt, rows):
    labels = [r["instance"] for r in rows]
    x = np.arange(len(labels))
    w = 0.25
    opt = [r["cpsat"]["Q"] for r in rows]
    pg = [100.0 * r["greedy"]["Q"] / o if o else 0 for r, o in zip(rows, opt)]
    pl = [100.0 * r["ls"]["avg"] / o if o else 0 for r, o in zip(rows, opt)]
    pa = [100.0 * r["alns"]["avg"] / o if o else 0 for r, o in zip(rows, opt)]
    fig, ax = plt.subplots()
    ax.bar(x - w, pg, w, label="Greedy", color=common.PALETTE["method"]["Greedy"])
    ax.bar(x, pl, w, label="Local Search", color=common.PALETTE["method"]["Local Search"])
    ax.bar(x + w, pa, w, label="ALNS", color=common.PALETTE["method"]["ALNS"])
    ax.axhline(100, color="#2ca02c", ls="--", lw=1.2, label="CP-SAT (tối ưu = 100%)")
    ax.set_ylim(min(pg + pl + pa) - 3, 102)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("% so với nghiệm tối ưu CP-SAT")
    ax.set_title("Chất lượng nghiệm nhóm nhỏ (chuẩn 100% = CP-SAT)")
    ax.legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "bench_small_quality.png"))
    plt.close(fig)


def _plot_large_gain(plt, rows):
    labels = [f"{r['instance']}\n(N={r['N']})" for r in rows]
    x = np.arange(len(labels))
    w = 0.25
    g = [r["greedy"]["Q"] for r in rows]
    l = [r["ls"]["avg"] for r in rows]
    a = [r["alns"]["avg"] for r in rows]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.bar(x - w, g, w, label="Greedy", color=common.PALETTE["method"]["Greedy"])
    ax.bar(x, l, w, label="Local Search", color=common.PALETTE["method"]["Local Search"])
    ax.bar(x + w, a, w, label="ALNS", color=common.PALETTE["method"]["ALNS"])
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Số lớp xếp được (trung bình)")
    ax.set_title("Số lớp xếp được trên nhóm dữ liệu lớn")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "bench_large_gain.png"))
    plt.close(fig)


def _plot_runtime(plt, all_rows):
    names, lsf_t, al_t = [], [], []
    for size in ["small", "medium", "large"]:
        for r in all_rows[size]:
            names.append(r["instance"])
            lsf_t.append(max(r["ls_fast"]["time"], 1e-5))
            al_t.append(max(r["alns"]["time"], 1e-5))
    x = np.arange(len(names))
    w = 0.4
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.bar(x - w / 2, lsf_t, w, label="Local Search (hội tụ)", color=common.PALETTE["method"]["Local Search"])
    ax.bar(x + w / 2, al_t, w, label=f"ALNS (ngân sách {TIME_LIMIT:.0f}s)", color=common.PALETTE["method"]["ALNS"])
    ax.set_yscale("log")
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Thời gian chạy (giây, log)")
    ax.set_title("Thời gian tính toán: Local Search (tức thời) vs ALNS (batch)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "bench_runtime.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
