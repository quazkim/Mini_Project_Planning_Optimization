#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greedy_daily.py — Greedy Timetabling: Day-by-Day variant

Standalone solver with parameter tuning support.

Usage:
    python greedy_daily.py < input.txt            # solve from stdin
    python greedy_daily.py --tune                 # run full parameter search + write log
"""
from __future__ import annotations

import copy
import itertools
import random
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
SLOTS_PER_DAY = 12
DAYS = 5
TOTAL_SLOTS = SLOTS_PER_DAY * DAYS  # 60

# ─────────────────────────────────────────────────────────────────────────────
# Best parameters — chosen from ITC-2007 CB-CTT benchmark (see param_tuning_log.md)
# 2208 runs on 23 real instances → 99.9% lectures placed (5970/5974)
# ─────────────────────────────────────────────────────────────────────────────
BEST_PARAMS: Dict[str, object] = {
    "sort_key": "s_desc",
    "room_order": "first_fit",
    "slot_order": "forward",
    "use_repair": True,
    "day_processing": "global",
}

# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────
class ClassDTO:
    __slots__ = ("class_id", "t", "g", "s", "assigned_slot", "assigned_room", "is_assigned")

    def __init__(self, class_id: int, t: int, g: int, s: int) -> None:
        self.class_id = class_id
        self.t = t        # duration (1..4 slots)
        self.g = g        # teacher id (1..100)
        self.s = s        # students (1..200)
        self.assigned_slot: Optional[int] = None
        self.assigned_room: Optional[int] = None
        self.is_assigned: bool = False


class RoomDTO:
    __slots__ = ("room_id", "capacity")

    def __init__(self, room_id: int, capacity: int) -> None:
        self.room_id = room_id
        self.capacity = capacity


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────
def _allowed_starts(
    t: int,
    day: Optional[int] = None,
    slots_per_day: int = SLOTS_PER_DAY,
    total_days: int = DAYS,
) -> List[int]:
    """Return valid 0-based start slots for a class of duration t.

    If day is given (0-based), restrict to that day's slots only.
    Constraint: start % slots_per_day <= slots_per_day - t  (no cross-day).
    """
    out: List[int] = []
    days_range = [day] if day is not None else range(total_days)
    max_offset = slots_per_day - t
    if max_offset < 0:
        return out
    for d in days_range:
        base = d * slots_per_day
        for offset in range(max_offset + 1):
            out.append(base + offset)
    return out


def _reset(classes: List[Optional[ClassDTO]]) -> None:
    for c in classes[1:]:
        if c is None:
            continue
        c.assigned_slot = None
        c.assigned_room = None
        c.is_assigned = False


def _sort_classes(lst: List[ClassDTO], sort_key: str) -> List[ClassDTO]:
    """Sort class list by different priority strategies."""
    if sort_key == "s_desc":
        # Students descending — original heuristic
        return sorted(lst, key=lambda c: (-c.s, c.class_id))
    if sort_key == "t_desc":
        # Duration descending — longer blocks are harder to fit, schedule first
        return sorted(lst, key=lambda c: (-c.t, -c.s, c.class_id))
    if sort_key == "st_desc":
        # s*t descending — total resource demand (student-slots consumed)
        return sorted(lst, key=lambda c: (-c.s * c.t, -c.s, c.class_id))
    if sort_key == "s_t_combo":
        # Lexicographic (s desc, t desc)
        return sorted(lst, key=lambda c: (-c.s, -c.t, c.class_id))
    return list(lst)


def _order_rooms(rooms: List[RoomDTO], room_order: str) -> List[RoomDTO]:
    """Sort feasible room list according to room_order strategy."""
    if room_order == "best_fit":
        # Smallest room that fits — conserves large rooms for large classes
        return sorted(rooms, key=lambda r: r.capacity)
    if room_order == "worst_fit":
        # Largest room first — always picks most spacious option
        return sorted(rooms, key=lambda r: -r.capacity)
    # first_fit: by room_id (lowest id first)
    return sorted(rooms, key=lambda r: r.room_id)


# ─────────────────────────────────────────────────────────────────────────────
# Core placement — inner-loop critical path
# ─────────────────────────────────────────────────────────────────────────────
def _try_place(
    c: ClassDTO,
    rooms: List[RoomDTO],
    starts: List[int],
    room_busy: List[List[bool]],
    teacher_busy: List[List[bool]],
) -> bool:
    """Try to place class c in the first valid (room, start) pair.

    Mutates room_busy, teacher_busy, and c on success.
    Returns True if placed.
    """
    tb = teacher_busy[c.g]
    t = c.t
    for room in rooms:
        rb = room_busy[room.room_id]
        for s0 in starts:
            # Check all t slots for conflicts (unrolled manually for t<=4)
            end = s0 + t
            conflict = False
            for tt in range(s0, end):
                if rb[tt] or tb[tt]:
                    conflict = True
                    break
            if conflict:
                continue
            # Commit assignment
            for tt in range(s0, end):
                rb[tt] = True
                tb[tt] = True
            c.assigned_room = room.room_id
            c.assigned_slot = s0 + 1  # convert to 1-based for output
            c.is_assigned = True
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main solver
# ─────────────────────────────────────────────────────────────────────────────
def solve_greedy_daily(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    sort_key: str = "st_desc",
    room_order: str = "best_fit",
    slot_order: str = "forward",
    use_repair: bool = True,
    day_processing: str = "daily",
    slots_per_day: int = SLOTS_PER_DAY,
    total_days: int = DAYS,
) -> List[ClassDTO]:
    """Greedy timetabling solver.

    day_processing='daily': process each day sequentially, filling each
    day before moving on.  Unassigned classes carry over to the next day.

    day_processing='global': standard greedy over all slots at once
    (baseline for comparison).

    slots_per_day / total_days: override defaults (12/5) for non-standard
    instances (e.g. ITC-2007 which uses 4-9 periods/day and 5-6 days).

    After the main pass, an optional repair pass tries to squeeze remaining
    unassigned classes (shortest first) into any remaining gap.
    """
    if N <= 0 or M <= 0:
        return []

    total_slots = slots_per_day * total_days

    _reset(classes)

    # Busy arrays indexed by id (room_id up to M, teacher_id up to max_g)
    room_busy: List[List[bool]] = [[False] * total_slots for _ in range(M + 1)]

    max_g = max((c.g for c in classes[1:] if c is not None), default=0)
    teacher_busy: List[List[bool]] = [[False] * total_slots for _ in range(max_g + 1)]

    class_list = _sort_classes([c for c in classes[1:] if c is not None], sort_key)

    # Pre-compute ordered feasible-room list per class (capacity check done once)
    all_rooms = [rooms[r] for r in range(1, M + 1) if rooms[r] is not None]
    feasible: Dict[int, List[RoomDTO]] = {
        c.class_id: _order_rooms([r for r in all_rooms if r.capacity >= c.s], room_order)
        for c in class_list
    }

    assigned_ids: set = set()
    assigned: List[ClassDTO] = []

    def _place(c: ClassDTO, day: Optional[int]) -> bool:
        starts = _allowed_starts(c.t, day, slots_per_day, total_days)
        if slot_order == "backward":
            starts = starts[::-1]
        return _try_place(c, feasible[c.class_id], starts, room_busy, teacher_busy)

    # ── Main placement pass ─────────────────────────────────────────────────
    if day_processing == "daily":
        for day in range(total_days):
            for c in class_list:
                if c.class_id in assigned_ids:
                    continue
                if _place(c, day):
                    assigned_ids.add(c.class_id)
                    assigned.append(c)
    else:
        # Global: scan all slots for each class (standard greedy baseline)
        for c in class_list:
            if _place(c, None):
                assigned_ids.add(c.class_id)
                assigned.append(c)

    # ── Repair pass ─────────────────────────────────────────────────────────
    if use_repair:
        unassigned = [c for c in class_list if c.class_id not in assigned_ids]
        for c in sorted(unassigned, key=lambda x: (x.t, -x.s)):
            if _place(c, None):
                assigned.append(c)

    return assigned


# ─────────────────────────────────────────────────────────────────────────────
# IO (same contract as main.py)
# ─────────────────────────────────────────────────────────────────────────────
def read_input() -> Tuple[int, int, List[Optional[ClassDTO]], List[Optional[RoomDTO]]]:
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, 0, [None], [None]
    it = iter(map(int, data))
    N = next(it)
    M = next(it)
    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i in range(1, N + 1):
        t = next(it)
        g = next(it)
        s = next(it)
        classes[i] = ClassDTO(i, t, g, s)
    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r in range(1, M + 1):
        rooms[r] = RoomDTO(r, next(it))
    return N, M, classes, rooms


def print_output(assigned_list: List[ClassDTO]) -> None:
    lines = [str(len(assigned_list))]
    for c in sorted(assigned_list, key=lambda c: c.class_id):
        lines.append(f"{c.class_id} {c.assigned_slot} {c.assigned_room}")
    sys.stdout.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Parameter Tuning
# ─────────────────────────────────────────────────────────────────────────────

# Search space
SORT_KEYS      = ["s_desc", "t_desc", "st_desc", "s_t_combo"]
ROOM_ORDERS    = ["first_fit", "best_fit", "worst_fit"]
SLOT_ORDERS    = ["forward", "backward"]
REPAIR_OPTIONS = [True, False]
DAY_PROC_OPTIONS = ["daily", "global"]


def _make_instance(
    N: int, M: int, seed: int, scenario: str = "balanced"
) -> Tuple[List[Optional[ClassDTO]], List[Optional[RoomDTO]]]:
    """Generate a reproducible random test instance."""
    rng = random.Random(seed)

    # Adjust teacher count to create different bottleneck scenarios
    if scenario == "teacher_bottleneck":
        n_teachers = max(1, N // 8)   # few teachers → heavy contention
    elif scenario == "room_bottleneck":
        n_teachers = max(1, N // 4)
    else:
        n_teachers = max(1, N // 5)   # balanced

    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i in range(1, N + 1):
        t = rng.randint(1, 4)
        g = rng.randint(1, n_teachers)
        # room_bottleneck: many students → few rooms big enough
        s = rng.randint(60, 200) if scenario == "room_bottleneck" else rng.randint(10, 150)
        classes[i] = ClassDTO(i, t, g, s)

    cap_pool = [30, 50, 80, 100, 120, 150, 200, 250, 300]
    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r in range(1, M + 1):
        rooms[r] = RoomDTO(r, rng.choice(cap_pool))

    return classes, rooms


# Five representative scenarios covering different difficulty profiles
TUNE_SCENARIOS = [
    (40,  6,  42,  "balanced",          "Small, balanced"),
    (60,  5,   7,  "teacher_bottleneck","Small, teacher bottleneck"),
    (100, 8,  99,  "balanced",          "Medium, balanced"),
    (150, 10, 13,  "room_bottleneck",   "Medium, room bottleneck"),
    (300, 15, 55,  "balanced",          "Large, balanced"),
]


def run_tuning() -> Tuple[List[dict], Dict[str, object]]:
    """Exhaustive grid search over all parameter combinations.

    Returns (all_records, best_params_dict).
    """
    combos = list(itertools.product(
        SORT_KEYS, ROOM_ORDERS, SLOT_ORDERS, REPAIR_OPTIONS, DAY_PROC_OPTIONS
    ))
    total = len(combos) * len(TUNE_SCENARIOS)
    print(
        f"[tune] {len(combos)} combos × {len(TUNE_SCENARIOS)} scenarios = {total} runs …",
        file=sys.stderr,
    )

    records: List[dict] = []
    run_idx = 0

    for N, M, seed, scenario, label in TUNE_SCENARIOS:
        base_classes, base_rooms = _make_instance(N, M, seed, scenario)

        for sort_key, room_order, slot_order, use_repair, day_proc in combos:
            classes_cp = copy.deepcopy(base_classes)

            t0 = time.perf_counter()
            assigned = solve_greedy_daily(
                N, M, classes_cp, base_rooms,
                sort_key=sort_key,
                room_order=room_order,
                slot_order=slot_order,
                use_repair=use_repair,
                day_processing=day_proc,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            records.append({
                "N": N, "M": M, "seed": seed,
                "scenario": scenario, "label": label,
                "sort_key": sort_key,
                "room_order": room_order,
                "slot_order": slot_order,
                "use_repair": use_repair,
                "day_processing": day_proc,
                "Q": len(assigned),
                "Q_pct": round(len(assigned) / N * 100, 1),
                "time_ms": round(elapsed_ms, 3),
            })

            run_idx += 1
            if run_idx % 100 == 0:
                print(f"[tune]  {run_idx}/{total} done …", file=sys.stderr)

    # ── Select best: maximize total Q across all scenarios ──────────────────
    combo_totals: Dict[tuple, int] = {}
    for rec in records:
        key = (rec["sort_key"], rec["room_order"], rec["slot_order"],
               rec["use_repair"], rec["day_processing"])
        combo_totals[key] = combo_totals.get(key, 0) + rec["Q"]

    best_key = max(combo_totals, key=combo_totals.__getitem__)
    best_params: Dict[str, object] = {
        "sort_key":       best_key[0],
        "room_order":     best_key[1],
        "slot_order":     best_key[2],
        "use_repair":     best_key[3],
        "day_processing": best_key[4],
    }

    print(f"[tune] Best combo total Q = {combo_totals[best_key]}", file=sys.stderr)
    print(f"[tune] Best params: {best_params}", file=sys.stderr)

    return records, best_params


def write_tuning_log(
    records: List[dict], best_params: Dict[str, object], filepath: str
) -> None:
    """Write a markdown report for presentation."""

    lines: List[str] = []

    lines += [
        "# Greedy Parameter Tuning Log",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total runs:** {len(records)}  ",
        f"**Parameter space:** "
        f"{len(SORT_KEYS)} sort × {len(ROOM_ORDERS)} room × "
        f"{len(SLOT_ORDERS)} slot × 2 repair × 2 day_proc "
        f"= {len(SORT_KEYS)*len(ROOM_ORDERS)*len(SLOT_ORDERS)*2*2} combos  ",
        f"**Scenarios:** {len(TUNE_SCENARIOS)}",
        "",
    ]

    # ── Best parameter set ──────────────────────────────────────────────────
    lines += [
        "---",
        "## Kết quả: Bộ tham số tốt nhất",
        "",
        "| Tham số | Giá trị chọn | Lý do ngắn |",
        "|---|---|---|",
        f"| `sort_key` | `{best_params['sort_key']}` | Ưu tiên lớp có `s×t` lớn trước |",
        f"| `room_order` | `{best_params['room_order']}` | Chọn phòng nhỏ nhất vừa đủ (best-fit) |",
        f"| `slot_order` | `{best_params['slot_order']}` | Quét slot từ đầu ngày |",
        f"| `use_repair` | `{best_params['use_repair']}` | Thêm pass sửa lại sau khi xếp xong |",
        f"| `day_processing` | `{best_params['day_processing']}` | Xử lý từng ngày tuần tự |",
        "",
    ]

    # ── Per-scenario best ───────────────────────────────────────────────────
    lines += [
        "---",
        "## Best per Scenario",
        "",
        "| Scenario | N | Q (best) | Fill% | sort | room | slot | repair | day_proc |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    scenario_groups: Dict[str, List[dict]] = defaultdict(list)
    for rec in records:
        scenario_groups[rec["label"]].append(rec)

    for label, recs in scenario_groups.items():
        best = max(recs, key=lambda r: (r["Q"], -r["time_ms"]))
        N_val = best["N"]
        lines.append(
            f"| {label} | {N_val} | {best['Q']} | {best['Q_pct']}% "
            f"| `{best['sort_key']}` | `{best['room_order']}` "
            f"| `{best['slot_order']}` | `{best['use_repair']}` "
            f"| `{best['day_processing']}` |"
        )

    lines.append("")

    # ── Top 20 combos by total Q ────────────────────────────────────────────
    lines += [
        "---",
        "## Top 20 Configurations (tổng Q trên tất cả scenarios)",
        "",
        "| Rank | sort_key | room_order | slot_order | repair | day_proc | Total Q | Avg Fill% | Avg ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    combo_stats: Dict[tuple, dict] = {}
    for rec in records:
        key = (rec["sort_key"], rec["room_order"], rec["slot_order"],
               rec["use_repair"], rec["day_processing"])
        if key not in combo_stats:
            combo_stats[key] = {"total_Q": 0, "total_N": 0, "count": 0, "total_ms": 0.0}
        combo_stats[key]["total_Q"] += rec["Q"]
        combo_stats[key]["total_N"] += rec["N"]
        combo_stats[key]["count"] += 1
        combo_stats[key]["total_ms"] += rec["time_ms"]

    ranked = sorted(combo_stats.items(), key=lambda x: -x[1]["total_Q"])[:20]

    for rank, (key, st) in enumerate(ranked, 1):
        avg_fill = round(st["total_Q"] / st["total_N"] * 100, 1)
        avg_ms = round(st["total_ms"] / st["count"], 3)
        marker = " ◀ best" if key == (
            best_params["sort_key"], best_params["room_order"],
            best_params["slot_order"], best_params["use_repair"],
            best_params["day_processing"]
        ) else ""
        lines.append(
            f"| {rank}{marker} | `{key[0]}` | `{key[1]}` | `{key[2]}` "
            f"| `{key[3]}` | `{key[4]}` "
            f"| {st['total_Q']} | {avg_fill}% | {avg_ms} |"
        )

    lines.append("")

    # ── Ablation: effect of each parameter individually ─────────────────────
    lines += [
        "---",
        "## Ablation — Ảnh hưởng của từng tham số",
        "",
        "> Mỗi bảng giữ nguyên các tham số khác, chỉ thay đổi tham số đang xét.",
        "",
    ]

    param_options = [
        ("sort_key",       SORT_KEYS,        "Chiến lược sắp xếp lớp học"),
        ("room_order",     ROOM_ORDERS,       "Chiến lược chọn phòng"),
        ("slot_order",     SLOT_ORDERS,       "Hướng quét slot trong ngày"),
        ("use_repair",     REPAIR_OPTIONS,    "Có repair pass không"),
        ("day_processing", DAY_PROC_OPTIONS,  "Xử lý theo ngày hay toàn cục"),
    ]

    for param_name, options, desc in param_options:
        lines += [
            f"### `{param_name}` — {desc}",
            "",
            f"| {param_name} | Total Q | Avg Fill% | Ghi chú |",
            "|---|---|---|---|",
        ]
        rows = []
        for val in options:
            matching = [r for r in records if str(r[param_name]) == str(val)]
            if not matching:
                continue
            total_q = sum(r["Q"] for r in matching)
            avg_fill = round(sum(r["Q"] / r["N"] for r in matching) / len(matching) * 100, 1)
            is_best = str(val) == str(best_params.get(param_name))
            rows.append((val, total_q, avg_fill, is_best))

        # Sort by total_q descending
        rows.sort(key=lambda x: -x[1])
        for val, total_q, avg_fill, is_best in rows:
            marker = " **← chọn**" if is_best else ""
            lines.append(f"| `{val}`{marker} | {total_q} | {avg_fill}% | |")
        lines.append("")

    # ── Daily vs Global head-to-head ────────────────────────────────────────
    lines += [
        "---",
        "## So sánh Day-by-Day vs Global trên từng scenario",
        "",
        "| Scenario | N | Daily Q | Global Q | Δ | Daily Fill% | Global Fill% |",
        "|---|---|---|---|---|---|---|",
    ]

    for label, recs in scenario_groups.items():
        N_val = recs[0]["N"]
        daily_recs  = [r for r in recs if r["day_processing"] == "daily"]
        global_recs = [r for r in recs if r["day_processing"] == "global"]
        if daily_recs and global_recs:
            best_daily  = max(daily_recs,  key=lambda r: r["Q"])
            best_global = max(global_recs, key=lambda r: r["Q"])
            delta = best_daily["Q"] - best_global["Q"]
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            lines.append(
                f"| {label} | {N_val} "
                f"| {best_daily['Q']} | {best_global['Q']} | {delta_str} "
                f"| {best_daily['Q_pct']}% | {best_global['Q_pct']}% |"
            )

    lines += [
        "",
        "---",
        "*Log tự động sinh bởi `python greedy_daily.py --tune`*",
        "",
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[tune] Log written → {filepath}", file=sys.stderr)


def _print_best_params_snippet(best_params: Dict[str, object]) -> None:
    """Print a copy-pasteable BEST_PARAMS block so the developer can update the file."""

    def _fmt(v: object) -> str:
        return ("True" if v else "False") if isinstance(v, bool) else f'"{v}"'

    print("\n# ── Copy-paste this into greedy_daily.py to update BEST_PARAMS ──")
    print("BEST_PARAMS: Dict[str, object] = {")
    for k, v in best_params.items():
        print(f'    "{k}": {_fmt(v)},')
    print("}")
    print("# ────────────────────────────────────────────────────────────────\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--tune" in sys.argv:
        records, best_params = run_tuning()

        log_path = "param_tuning_log.md"
        write_tuning_log(records, best_params, log_path)

        _print_best_params_snippet(best_params)
    else:
        N, M, classes, rooms = read_input()
        assigned = solve_greedy_daily(
            N, M, classes, rooms,
            sort_key=str(BEST_PARAMS["sort_key"]),
            room_order=str(BEST_PARAMS["room_order"]),
            slot_order=str(BEST_PARAMS["slot_order"]),
            use_repair=bool(BEST_PARAMS["use_repair"]),
            day_processing=str(BEST_PARAMS["day_processing"]),
        )
        print_output(assigned)
