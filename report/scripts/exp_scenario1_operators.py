#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KỊCH BẢN 1 — Sự tiến hóa của xác suất chọn toán tử (Adaptive Selection).

Chạy ALNS có ghi vết trên một instance bottleneck (test09: N=200, M=5) và vẽ:
  - Miền xác suất (stacked area) của 3 toán tử Destroy theo vòng lặp.
  - Miền xác suất của 3 toán tử Repair theo vòng lặp.
Lấy trung bình trên nhiều seed để đường biểu diễn ổn định, phản ánh xu hướng học.
"""

from __future__ import annotations

import json
import os

import numpy as np

import common
from instrumented_alns import (
    DESTROY_NAMES,
    REPAIR_NAMES,
    run_instrumented_alns,
)
from solver.algorithms.greedy import solve_with_greedy

INSTANCE = "test09"
MAX_ITERS = 500
SEEDS = [1, 7, 13, 21, 42]


def main():
    plt = common.setup_matplotlib()
    N, M, classes, rooms = common.load_instance(INSTANCE)

    prob_d_runs, prob_r_runs = [], []
    for sd in SEEDS:
        greedy = solve_with_greedy(N, M, classes, rooms)
        h = run_instrumented_alns(N, M, classes, rooms, greedy,
                                  max_iters=MAX_ITERS, lam=0.5, T0=10.0,
                                  cooling=0.98, seed=sd)
        prob_d_runs.append(np.array(h["prob_d"]))   # (iters, 3)
        prob_r_runs.append(np.array(h["prob_r"]))

    L = min(len(r) for r in prob_d_runs)
    prob_d = np.mean([r[:L] for r in prob_d_runs], axis=0)  # (L, 3)
    prob_r = np.mean([r[:L] for r in prob_r_runs], axis=0)
    it = np.arange(1, L + 1)

    # --- Hình 1a: Destroy operators ---
    fig, ax = plt.subplots()
    ax.stackplot(it, prob_d[:, 0], prob_d[:, 1], prob_d[:, 2],
                 labels=DESTROY_NAMES, colors=common.PALETTE["destroy"], alpha=0.85)
    ax.set_xlim(1, L)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Số vòng lặp (iteration)")
    ax.set_ylabel("Xác suất được chọn")
    ax.set_title("Kịch bản 1 — Tiến hóa xác suất 3 toán tử Phá hủy (Destroy)")
    ax.legend(loc="upper center", ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "s1_destroy_probability.png"))
    plt.close(fig)

    # --- Hình 1b: Repair operators ---
    fig, ax = plt.subplots()
    ax.stackplot(it, prob_r[:, 0], prob_r[:, 1], prob_r[:, 2],
                 labels=REPAIR_NAMES, colors=common.PALETTE["repair"], alpha=0.85)
    ax.set_xlim(1, L)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Số vòng lặp (iteration)")
    ax.set_ylabel("Xác suất được chọn")
    ax.set_title("Kịch bản 1 — Tiến hóa xác suất 3 toán tử Sửa chữa (Repair)")
    ax.legend(loc="upper center", ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "s1_repair_probability.png"))
    plt.close(fig)

    # Lưu xác suất cuối kỳ để trích dẫn trong báo cáo.
    summary = {
        "instance": INSTANCE, "N": N, "M": M, "iters": int(L),
        "destroy_final": dict(zip(DESTROY_NAMES, prob_d[-1].round(3).tolist())),
        "repair_final": dict(zip(REPAIR_NAMES, prob_r[-1].round(3).tolist())),
        "destroy_start": dict(zip(DESTROY_NAMES, prob_d[0].round(3).tolist())),
        "repair_start": dict(zip(REPAIR_NAMES, prob_r[0].round(3).tolist())),
    }
    with open(os.path.join(common.DATA_DIR, "s1_operators.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
