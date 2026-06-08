#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KỊCH BẢN 2 — Tác động của hệ số học lambda (Learning Rate).

So sánh sự tăng trưởng hàm mục tiêu (số lớp xếp được tốt nhất) theo vòng lặp
ứng với lambda in {0.1, 0.5, 0.9}. Mỗi cấu hình lấy trung bình trên nhiều seed.
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
LAMBDAS = [0.1, 0.5, 0.9]
COLORS = {0.1: "#1f77b4", 0.5: "#d62728", 0.9: "#2ca02c"}


def main():
    plt = common.setup_matplotlib()
    N, M, classes, rooms = common.load_instance(INSTANCE)

    fig, ax = plt.subplots()
    summary = {"instance": INSTANCE, "N": N, "M": M, "results": {}}

    for lam in LAMBDAS:
        curves = []
        for sd in SEEDS:
            greedy = solve_with_greedy(N, M, classes, rooms)
            h = run_instrumented_alns(N, M, classes, rooms, greedy,
                                      max_iters=MAX_ITERS, lam=lam, T0=10.0,
                                      cooling=0.98, seed=sd)
            curves.append(np.array(h["score_best"]))
        L = min(len(c) for c in curves)
        arr = np.array([c[:L] for c in curves])
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)
        it = np.arange(1, L + 1)
        ax.plot(it, mean, color=COLORS[lam], label=f"$\\lambda={lam}$")
        ax.fill_between(it, mean - std, mean + std, color=COLORS[lam], alpha=0.15)
        summary["results"][str(lam)] = {
            "final_mean": float(mean[-1]), "final_std": float(std[-1]),
            "greedy_start": int(curves[0][0]),
        }

    ax.set_xlabel("Số vòng lặp (iteration)")
    ax.set_ylabel("Hàm mục tiêu tốt nhất (số lớp xếp được)")
    ax.set_title("Kịch bản 2 — Tăng trưởng hàm mục tiêu theo hệ số học $\\lambda$")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "s2_lambda_convergence.png"))
    plt.close(fig)

    with open(os.path.join(common.DATA_DIR, "s2_lambda.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
