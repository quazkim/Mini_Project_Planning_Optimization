#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""main_greedy.py — Greedy-only solver (không cần ortools)

Chạy: python main_greedy.py < input.txt
"""
from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple


# ── Models ────────────────────────────────────────────────────────────────────

class ClassDTO:
    def __init__(self, class_id: int, t: int, g: int, s: int):
        self.class_id = class_id
        self.t = t
        self.g = g
        self.s = s
        self.assigned_slot: Optional[int] = None
        self.assigned_room: Optional[int] = None
        self.is_assigned: bool = False


class RoomDTO:
    def __init__(self, room_id: int, capacity: int):
        self.room_id = room_id
        self.capacity = capacity


# ── Constants ─────────────────────────────────────────────────────────────────

SLOTS_PER_DAY = 12
DAYS = 5
TOTAL_SLOTS = SLOTS_PER_DAY * DAYS  # 60


# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_starts(t: int) -> List[int]:
    out: List[int] = []
    for day in range(DAYS):
        base = day * SLOTS_PER_DAY
        for offset in range(SLOTS_PER_DAY - t + 1):
            out.append(base + offset)
    return out


# ── IO ────────────────────────────────────────────────────────────────────────

def read_input() -> Tuple[int, int, List[Optional[ClassDTO]], List[Optional[RoomDTO]]]:
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, 0, [None], [None]
    it = iter(map(int, data))
    N = next(it)
    M = next(it)
    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i in range(1, N + 1):
        t, g, s = next(it), next(it), next(it)
        classes[i] = ClassDTO(i, t, g, s)
    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r in range(1, M + 1):
        rooms[r] = RoomDTO(r, next(it))
    return N, M, classes, rooms


def print_output(assigned: List[ClassDTO]) -> None:
    out = [str(len(assigned))]
    for c in sorted(assigned, key=lambda c: c.class_id):
        out.append(f"{c.class_id} {c.assigned_slot} {c.assigned_room}")
    sys.stdout.write("\n".join(out) + "\n")


# ── Greedy solver ─────────────────────────────────────────────────────────────

def solve_greedy(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
) -> List[ClassDTO]:
    if N <= 0 or M <= 0:
        return []

    room_busy: List[List[bool]] = [[False] * TOTAL_SLOTS for _ in range(M + 1)]
    teacher_busy: Dict[int, List[bool]] = {}

    # Sort: lớp đông sinh viên trước (room capacity là bottleneck chính)
    class_list = sorted(
        [c for c in classes[1:] if c is not None],
        key=lambda c: (-c.s, c.class_id),
    )

    assigned: List[ClassDTO] = []

    # ── Main pass ──────────────────────────────────────────────────────────────
    for c in class_list:
        if c.g not in teacher_busy:
            teacher_busy[c.g] = [False] * TOTAL_SLOTS

        tb = teacher_busy[c.g]
        placed = False

        for r in range(1, M + 1):
            room = rooms[r]
            if room is None or room.capacity < c.s:
                continue
            rb = room_busy[r]
            for s0 in _allowed_starts(c.t):
                ok = True
                for tt in range(s0, s0 + c.t):
                    if rb[tt] or tb[tt]:
                        ok = False
                        break
                if ok:
                    for tt in range(s0, s0 + c.t):
                        rb[tt] = True
                        tb[tt] = True
                    c.assigned_room = r
                    c.assigned_slot = s0 + 1   # 1-based
                    c.is_assigned = True
                    assigned.append(c)
                    placed = True
                    break
            if placed:
                break

    # ── Repair pass: thử lại lớp chưa xếp, ngắn nhất trước ──────────────────
    for c in sorted([c for c in class_list if not c.is_assigned], key=lambda x: (x.t, -x.s)):
        if c.g not in teacher_busy:
            teacher_busy[c.g] = [False] * TOTAL_SLOTS
        tb = teacher_busy[c.g]
        for r in range(1, M + 1):
            room = rooms[r]
            if room is None or room.capacity < c.s:
                continue
            rb = room_busy[r]
            for s0 in _allowed_starts(c.t):
                ok = True
                for tt in range(s0, s0 + c.t):
                    if rb[tt] or tb[tt]:
                        ok = False
                        break
                if ok:
                    for tt in range(s0, s0 + c.t):
                        rb[tt] = True
                        tb[tt] = True
                    c.assigned_room = r
                    c.assigned_slot = s0 + 1
                    c.is_assigned = True
                    assigned.append(c)
                    break
            if c.is_assigned:
                break

    return assigned


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    N, M, classes, rooms = read_input()
    assigned = solve_greedy(N, M, classes, rooms)
    print_output(assigned)
