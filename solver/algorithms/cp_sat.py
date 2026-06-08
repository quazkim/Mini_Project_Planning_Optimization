#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Thuật toán chính xác bằng CP-SAT (OR-Tools).

- Mô hình hóa bằng OptionalIntervalVar + AddNoOverlap cho phòng và giáo viên.
- Mục tiêu: tối đa số lớp được xếp.
- Warm-start: chạy Greedy trước để cung cấp hint, giúp CP-SAT có nghiệm hợp lệ
  ngay lập tức và chỉ cần cải thiện thêm trong thời gian giới hạn ngắn.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from ..config import TOTAL_SLOTS
from ..models import ClassDTO, RoomDTO
from ..utils import allowed_starts_for_duration, debug, reset_assignments
from .greedy import solve_with_greedy


def solve_with_cp_sat(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    time_limit: float = 2.0,
) -> Tuple[int, List[ClassDTO]]:
    """Giải bằng CP-SAT.

    time_limit (giây): trần thời gian solver. Mặc định 2.0s (an toàn cho judge);
    benchmark có thể nâng lên để so sánh công bằng.

    Returns:
      - status (cp_model.OPTIMAL/FEASIBLE/INFEASIBLE/...).
      - assigned_list: danh sách lớp được xếp.
    """
    try:
        from ortools.sat.python import cp_model
    except Exception as e:  # pragma: no cover
        raise ImportError("ortools is required for CP-SAT solver") from e

    if N <= 0 or M <= 0:
        return 0, []

    reset_assignments(classes)

    # --- Warm-start: chạy Greedy trước để thu hint (room + slot) cho CP-SAT ---
    debug("[CP-SAT] Chạy Greedy để tạo warm-start hints...")
    _greedy_hints = solve_with_greedy(N, M, classes, rooms)
    _hint_room: Dict[int, int] = {}    # class_id -> room_id
    _hint_start: Dict[int, int] = {}   # class_id -> start slot (0-based)
    for _ch in _greedy_hints:
        _hint_room[_ch.class_id] = _ch.assigned_room       # type: ignore[assignment]
        _hint_start[_ch.class_id] = _ch.assigned_slot - 1  # chuyển về 0-based
    debug(f"[CP-SAT] Warm-start Q={len(_greedy_hints)}, chuẩn bị inject {len(_hint_room)} hints...")
    reset_assignments(classes)  # Dọn sạch để CP-SAT ghi đè kết quả riêng của nó

    model = cp_model.CpModel()

    # a_i: lớp i có được xếp không.
    a: Dict[int, "cp_model.IntVar"] = {}

    # Với mỗi (i, r) khả thi: presence b_ir, start s_ir, interval intv_ir.
    b: Dict[Tuple[int, int], "cp_model.IntVar"] = {}
    start: Dict[Tuple[int, int], "cp_model.IntVar"] = {}
    interval: Dict[Tuple[int, int], "cp_model.IntervalVar"] = {}

    room_caps = [0] * (M + 1)
    for r in range(1, M + 1):
        room_caps[r] = rooms[r].capacity  # type: ignore[union-attr]

    for i in range(1, N + 1):
        c = classes[i]
        if c is None:
            continue

        a_i = model.NewBoolVar(f"assigned_{i}")
        a[i] = a_i

        feasible_rooms: List[int] = [r for r in range(1, M + 1) if room_caps[r] >= c.s]
        if not feasible_rooms:
            model.Add(a_i == 0)
            continue

        allowed_starts = allowed_starts_for_duration(c.t)

        presences: List["cp_model.IntVar"] = []
        for r in feasible_rooms:
            b_ir = model.NewBoolVar(f"b_{i}_{r}")
            b[(i, r)] = b_ir
            presences.append(b_ir)

            s_ir = model.NewIntVar(0, TOTAL_SLOTS - 1, f"start_{i}_{r}")
            model.AddAllowedAssignments([s_ir], [[v] for v in allowed_starts])
            start[(i, r)] = s_ir

            e_ir = model.NewIntVar(0, TOTAL_SLOTS, f"end_{i}_{r}")
            model.Add(e_ir == s_ir + c.t)

            intv_ir = model.NewOptionalIntervalVar(s_ir, c.t, e_ir, b_ir, f"int_{i}_{r}")
            interval[(i, r)] = intv_ir

        # Đúng một phòng nếu được xếp, ngược lại không phòng nào.
        model.Add(sum(presences) == a_i)

    # Ràng buộc no-overlap cho phòng.
    for r in range(1, M + 1):
        intervals_r: List["cp_model.IntervalVar"] = []
        for i in range(1, N + 1):
            key = (i, r)
            if key in interval:
                intervals_r.append(interval[key])
        if intervals_r:
            model.AddNoOverlap(intervals_r)

    # Ràng buộc no-overlap cho giáo viên.
    teacher_to_intervals: Dict[int, List["cp_model.IntervalVar"]] = {}
    for i in range(1, N + 1):
        c = classes[i]
        if c is None:
            continue
        g = c.g
        if g not in teacher_to_intervals:
            teacher_to_intervals[g] = []
        for r in range(1, M + 1):
            key = (i, r)
            if key in interval:
                teacher_to_intervals[g].append(interval[key])

    for g, intvs in teacher_to_intervals.items():
        if intvs:
            model.AddNoOverlap(intvs)

    # Mục tiêu: tối đa số lớp được xếp.
    model.Maximize(sum(a.values()) if a else 0)

    # --- Inject warm-start hints vào model (gọi trước solver.Solve) ---
    for i, a_i in a.items():
        if i in _hint_room:
            model.AddHint(a_i, 1)
            r_h = _hint_room[i]
            for r in range(1, M + 1):
                if (i, r) in b:
                    model.AddHint(b[(i, r)], 1 if r == r_h else 0)
                if (i, r) in start and r == r_h:
                    model.AddHint(start[(i, r)], _hint_start[i])
        else:
            model.AddHint(a_i, 0)

    solver = cp_model.CpSolver()
    # Warm-start từ Greedy đã đảm bảo CP-SAT có nghiệm hợp lệ ngay lập tức;
    # mặc định 2s đủ để cải thiện thêm mà không bị judge kill (benchmark nâng cao hơn).
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = max(1, os.cpu_count() or 4)

    status = solver.Solve(model)

    assigned_list: List[ClassDTO] = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if status == cp_model.OPTIMAL:
            debug(f"[CP-SAT] OPTIMAL — Q={int(solver.ObjectiveValue())}")
        else:
            debug(
                f"[CP-SAT] FEASIBLE (timeout) — Q={int(solver.ObjectiveValue())}, "
                f"upper_bound={int(solver.BestObjectiveBound())}"
            )
        for i in range(1, N + 1):
            c = classes[i]
            if c is None or i not in a:
                continue
            if solver.Value(a[i]) == 0:
                continue

            chosen_room = None
            chosen_start = None
            for r in range(1, M + 1):
                key = (i, r)
                if key in b and solver.Value(b[key]) == 1:
                    chosen_room = r
                    chosen_start = int(solver.Value(start[key]))
                    break

            if chosen_room is None or chosen_start is None:
                continue

            c.assigned_room = chosen_room
            c.assigned_slot = chosen_start + 1  # 1-based output
            c.is_assigned = True
            assigned_list.append(c)

    return status, assigned_list
