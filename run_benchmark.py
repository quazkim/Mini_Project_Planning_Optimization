#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from main_greedy import (
    read_input, ClassDTO, RoomDTO,
    _greedy_pass, _ejection_chain,
    _do_assign, _do_unassign, _find_slot,
    TOTAL_SLOTS, SLOTS_PER_DAY, DAYS, _allowed_starts,
)
from typing import Dict, List, Optional


def _reset_classes(classes):
    for c in classes:
        if c is not None:
            c.assigned_slot = None
            c.assigned_room = None
            c.is_assigned = False


def solve(classes, rooms, use_ls: bool):
    M = len(rooms) - 1
    room_busy = [[False] * TOTAL_SLOTS for _ in range(M + 1)]
    teacher_busy: Dict = {}
    room_occ = [[None] * TOTAL_SLOTS for _ in range(M + 1)]
    teacher_occ: Dict = {}

    class_list = sorted(
        [c for c in classes if c is not None],
        key=lambda c: (c.t, c.s)
    )
    sorted_room_ids = sorted(
        range(1, M + 1),
        key=lambda r: rooms[r].capacity if rooms[r] else 0
    )

    if use_ls:
        prev_count = -1
        while True:
            _greedy_pass(class_list, room_busy, teacher_busy, room_occ, teacher_occ, rooms, sorted_room_ids)
            cur_count = sum(1 for c in class_list if c.is_assigned)
            if cur_count == prev_count:
                break
            prev_count = cur_count
            _ejection_chain(class_list, room_busy, teacher_busy, room_occ, teacher_occ, rooms, sorted_room_ids)
    else:
        _greedy_pass(class_list, room_busy, teacher_busy, room_occ, teacher_occ, rooms, sorted_room_ids)

    return sum(1 for c in class_list if c.is_assigned), class_list


TEST_DIR = "test_input"
files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".txt"))

rows = []
for fname in files:
    path = os.path.join(TEST_DIR, fname)
    with open(path) as f:
        import io, sys as _sys
        _sys.stdin = io.StringIO(f.read())
        N, M, classes, rooms = read_input()
        _sys.stdin = sys.__stdin__ if hasattr(sys, '__stdin__') else sys.stdin

    # Run without LS
    _reset_classes(classes[1:])
    t0 = time.time()
    q_no_ls, _ = solve(classes[1:], rooms, use_ls=False)
    t_no_ls = time.time() - t0

    # Reset and run with LS
    _reset_classes(classes[1:])
    t0 = time.time()
    q_ls, _ = solve(classes[1:], rooms, use_ls=True)
    t_ls = time.time() - t0

    diff = q_ls - q_no_ls
    rows.append((fname, N, M, q_no_ls, q_ls, diff, t_no_ls, t_ls))
    print(f"  {fname:25s} N={N:4d} M={M:3d} | no_ls={q_no_ls:4d} | ls={q_ls:4d} | +{diff:3d}", flush=True)

print()
print(f"{'File':<25} {'N':>5} {'M':>4} | {'No LS':>6} | {'With LS':>7} | {'Diff':>5} | {'t_no_ls':>8} | {'t_ls':>8}")
print("-" * 80)
for fname, N, M, q_no, q_ls, diff, t1, t2 in rows:
    print(f"{fname:<25} {N:>5} {M:>4} | {q_no:>6} | {q_ls:>7} | {diff:>+5} | {t1:>7.2f}s | {t2:>7.2f}s")

total_no = sum(r[3] for r in rows)
total_ls = sum(r[4] for r in rows)
print("-" * 80)
print(f"{'TOTAL':<25} {'':>5} {'':>4} | {total_no:>6} | {total_ls:>7} | {total_ls-total_no:>+5}")
