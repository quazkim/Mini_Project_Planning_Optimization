#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KỊCH BẢN 3 — Biến thiên nhiệt độ T và hệ số làm mát alpha.

Đồ thị kép (dual-axis): hội tụ hàm mục tiêu (trục trái) đối chiếu quá trình
tụt nhiệt T (trục phải) cho alpha in {0.90, 0.98}. So sánh "nguội nhanh" (chết
yểu ở cực đại cục bộ) với "nguội chậm" (đủ thời gian khám phá).
"""

from __future__ import annotations

import json
import os

import numpy as np

import common
from instrumented_alns import run_instrumented_alns
from solver.algorithms.greedy import solve_with_greedy

INSTANCE = "test09"
MAX_ITERS = 500
SEEDS = [1, 7, 13, 21, 42]
ALPHAS = [0.90, 0.98]
OBJ_COLOR = {0.90: "#d62728", 0.98: "#1f77b4"}
T_COLOR = {0.90: "#ff9896", 0.98: "#aec7e8"}


def _avg_run(N, M, classes, rooms, alpha):
    obj_curves, T_curves = [], []
    for sd in SEEDS:
        greedy = solve_with_greedy(N, M, classes, rooms)
        h = run_instrumented_alns(N, M, classes, rooms, greedy,
                                  max_iters=MAX_ITERS, lam=0.5, T0=10.0,
                                  cooling=alpha, seed=sd)
        obj_curves.append(np.array(h["score_best"]))
        T_curves.append(np.array(h["T"]))
    L = min(len(c) for c in obj_curves)
    obj = np.array([c[:L] for c in obj_curves]).mean(axis=0)
    T = np.array([c[:L] for c in T_curves]).mean(axis=0)
    return np.arange(1, L + 1), obj, T


def main():
    plt = common.setup_matplotlib()
    N, M, classes, rooms = common.load_instance(INSTANCE)

    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    summary = {"instance": INSTANCE, "N": N, "M": M, "results": {}}

    for alpha in ALPHAS:
        it, obj, T = _avg_run(N, M, classes, rooms, alpha)
        ax.plot(it, obj, color=OBJ_COLOR[alpha], label=f"Mục tiêu, $\\alpha={alpha}$")
        ax2.plot(it, T, color=T_COLOR[alpha], linestyle="--",
                 label=f"Nhiệt độ T, $\\alpha={alpha}$")
        summary["results"][str(alpha)] = {
            "final_obj": float(obj[-1]),
            "T_at_iter50": float(T[min(49, len(T) - 1)]),
            "T_final": float(T[-1]),
        }

    ax.set_xlabel("Số vòng lặp (iteration)")
    ax.set_ylabel("Hàm mục tiêu tốt nhất (số lớp)")
    ax2.set_ylabel("Nhiệt độ T (thang Boltzmann)")
    ax.set_title("Kịch bản 3 — Hội tụ mục tiêu đối chiếu tụt nhiệt T theo $\\alpha$")

    # Gộp legend hai trục.
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="center right", fontsize=8.5)
    ax.set_xlim(1, len(it))
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "s3_temperature_dualaxis.png"))
    plt.close(fig)

    with open(os.path.join(common.DATA_DIR, "s3_temperature.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
