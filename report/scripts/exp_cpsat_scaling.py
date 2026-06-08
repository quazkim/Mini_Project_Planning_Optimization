#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHẦN 2.3 — Bùng nổ tổ hợp của CP-SAT khi N tăng.

Sinh các instance ngẫu nhiên với N tăng dần (mật độ tài nguyên cố định) và đo:
  - thời gian CP-SAT đạt OPTIMAL (hoặc chạm time-limit),
  - khoảng cách cận trên/cận dưới (gap) còn lại khi hết giờ,
  - số biến quyết định của mô hình (đại lượng đại diện kích thước không gian tìm kiếm).

Mô hình CP-SAT được xây lại tại đây (tái dùng cùng công thức Interval/NoOverlap
như solver) để có thể chỉnh time-limit và truy xuất bound/var-count.
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import List

import numpy as np

import common
from solver.config import TOTAL_SLOTS
from solver.models import ClassDTO, RoomDTO
from solver.utils import allowed_starts_for_duration
from solver.algorithms.greedy import solve_with_greedy

from ortools.sat.python import cp_model

TIME_LIMIT = 20.0
N_VALUES = [10, 25, 50, 75, 100, 150, 200, 300, 400, 500, 600]
RNG_SEED = 2024


def gen_instance(N, M, rng):
    # Tài nguyên khan hiếm: ít giáo viên (nhiều xung đột no-overlap) và phòng
    # sức chứa vừa phải -> bài toán thực sự khó, ép CP-SAT phải chứng minh tối ưu.
    n_teach = max(2, N // 20)
    classes: List = [None] * (N + 1)
    for i in range(1, N + 1):
        classes[i] = ClassDTO(i, rng.randint(1, 4), rng.randint(1, n_teach),
                              rng.randint(1, 220))
    rooms: List = [None] * (M + 1)
    for r in range(1, M + 1):
        rooms[r] = RoomDTO(r, rng.randint(120, 260))
    return classes, rooms


def build_and_solve(N, M, classes, rooms, time_limit):
    # Warm-start hint từ Greedy (giống solver).
    hints = solve_with_greedy(N, M, classes, rooms)
    hint_room = {c.class_id: c.assigned_room for c in hints}
    hint_start = {c.class_id: c.assigned_slot - 1 for c in hints}

    model = cp_model.CpModel()
    a, b, start, interval = {}, {}, {}, {}
    room_caps = [0] + [rooms[r].capacity for r in range(1, M + 1)]
    nvars = 0
    for i in range(1, N + 1):
        c = classes[i]
        a_i = model.NewBoolVar(f"a{i}"); a[i] = a_i; nvars += 1
        feas = [r for r in range(1, M + 1) if room_caps[r] >= c.s]
        if not feas:
            model.Add(a_i == 0); continue
        allowed = allowed_starts_for_duration(c.t)
        pres = []
        for r in feas:
            b_ir = model.NewBoolVar(f"b{i}_{r}"); b[(i, r)] = b_ir; pres.append(b_ir); nvars += 1
            s_ir = model.NewIntVar(0, TOTAL_SLOTS - 1, f"s{i}_{r}"); nvars += 1
            model.AddAllowedAssignments([s_ir], [[v] for v in allowed])
            start[(i, r)] = s_ir
            e_ir = model.NewIntVar(0, TOTAL_SLOTS, f"e{i}_{r}")
            model.Add(e_ir == s_ir + c.t)
            interval[(i, r)] = model.NewOptionalIntervalVar(s_ir, c.t, e_ir, b_ir, f"i{i}_{r}")
        model.Add(sum(pres) == a_i)

    for r in range(1, M + 1):
        ivs = [interval[(i, r)] for i in range(1, N + 1) if (i, r) in interval]
        if ivs:
            model.AddNoOverlap(ivs)
    t2i = {}
    for i in range(1, N + 1):
        g = classes[i].g
        for r in range(1, M + 1):
            if (i, r) in interval:
                t2i.setdefault(g, []).append(interval[(i, r)])
    for ivs in t2i.values():
        if ivs:
            model.AddNoOverlap(ivs)
    model.Maximize(sum(a.values()))

    for i, a_i in a.items():
        if i in hint_room:
            model.AddHint(a_i, 1)
            for r in range(1, M + 1):
                if (i, r) in b:
                    model.AddHint(b[(i, r)], 1 if r == hint_room[i] else 0)
                if (i, r) in start and r == hint_room[i]:
                    model.AddHint(start[(i, r)], hint_start[i])
        else:
            model.AddHint(a_i, 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = max(1, os.cpu_count() or 4)
    t0 = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - t0
    obj = int(solver.ObjectiveValue()) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0
    bound = solver.BestObjectiveBound()
    return {
        "status": solver.StatusName(status),
        "elapsed": elapsed,
        "objective": obj,
        "bound": bound,
        "gap": max(0.0, bound - obj),
        "nvars": nvars,
        "greedy": len(hints),
    }


def main():
    plt = common.setup_matplotlib()
    rng = random.Random(RNG_SEED)
    M = 8
    rows = []
    for N in N_VALUES:
        classes, rooms = gen_instance(N, M, rng)
        res = build_and_solve(N, M, classes, rooms, TIME_LIMIT)
        res["N"] = N
        rows.append(res)
        print(f"N={N:4d} status={res['status']:10s} t={res['elapsed']:6.2f}s "
              f"obj={res['objective']:4d} bound={res['bound']:.1f} gap={res['gap']:.1f} "
              f"vars={res['nvars']}", flush=True)

    with open(os.path.join(common.DATA_DIR, "cpsat_scaling.json"), "w") as f:
        json.dump(rows, f, indent=2)

    Ns = [r["N"] for r in rows]
    times = [r["elapsed"] for r in rows]
    gaps = [r["gap"] for r in rows]
    nvars = [r["nvars"] for r in rows]

    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    ax.plot(Ns, times, "o-", color="#d62728", label="Thời gian giải (s)")
    ax.axhline(TIME_LIMIT, color="#d62728", ls=":", lw=1.2, alpha=0.7,
               label=f"Time-limit = {TIME_LIMIT:.0f}s")
    ax2.plot(Ns, nvars, "s--", color="#1f77b4", label="Số biến quyết định")
    ax.set_xlabel("Số lớp N")
    ax.set_ylabel("Thời gian CP-SAT (giây)")
    ax2.set_ylabel("Số biến quyết định của mô hình")
    ax.set_title("Phần 2 — Tăng trưởng mô hình & thời gian CP-SAT theo N")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(common.FIG_DIR, "cpsat_scaling.png"))
    plt.close(fig)
    print("saved cpsat_scaling.png")


if __name__ == "__main__":
    main()
