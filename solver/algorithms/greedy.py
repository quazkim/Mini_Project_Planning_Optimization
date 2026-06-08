#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Thuật toán Greedy (baseline).

Nguyên lý (theo main_greedy.py):
- Sắp lớp theo (thời lượng t tăng dần, rồi sĩ số s tăng dần): ưu tiên lớp ngắn,
  ít sinh viên trước.
- Duyệt phòng theo sức chứa tăng dần (best-fit): dùng phòng vừa đủ trước, để dành
  phòng lớn cho lớp đông.
- Với mỗi lớp, quét tiết bắt đầu hợp lệ (ngoài) rồi phòng (trong), chọn cặp
  (tiết, phòng) hợp lệ ĐẦU TIÊN và gán luôn (first-feasible).
- Lặp lại các lượt gán cho đến khi một lượt không xếp thêm được lớp nào.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..config import TOTAL_SLOTS
from ..models import ClassDTO, RoomDTO
from ..utils import allowed_starts_for_duration, reset_assignments


def solve_with_greedy(
    N: int, M: int, classes: List[Optional[ClassDTO]], rooms: List[Optional[RoomDTO]]
) -> List[ClassDTO]:
    """Greedy baseline, trả về danh sách lớp đã xếp."""
    if N <= 0 or M <= 0:
        return []

    reset_assignments(classes)

    # room_busy[room_id][time] => bool
    room_busy: List[List[bool]] = [[False] * TOTAL_SLOTS for _ in range(M + 1)]
    # teacher_busy[g][time] => bool
    teacher_busy: Dict[int, List[bool]] = {}

    # Sắp lớp: thời lượng tăng dần, rồi sĩ số tăng dần (tiết ngắn & ít SV trước).
    class_list: List[ClassDTO] = [c for c in classes[1:] if c is not None]
    class_list.sort(key=lambda c: (c.t, c.s))

    # Duyệt phòng theo sức chứa tăng dần (best-fit).
    sorted_room_ids: List[int] = sorted(
        range(1, M + 1),
        key=lambda r: rooms[r].capacity if rooms[r] is not None else 0,
    )

    assigned: List[ClassDTO] = []

    # Lặp các lượt gán cho đến khi không xếp thêm được lớp nào.
    check = True
    while check:
        check = False
        for c in class_list:
            if c.is_assigned:
                continue
            if c.g not in teacher_busy:
                teacher_busy[c.g] = [False] * TOTAL_SLOTS
            tb = teacher_busy[c.g]

            placed = False
            for s0 in allowed_starts_for_duration(c.t):
                # Giáo viên bận trong khối [s0, s0+t) thì bỏ qua sớm.
                if any(tb[s0 + o] for o in range(c.t)):
                    continue
                for r in sorted_room_ids:
                    room = rooms[r]
                    if room is None or room.capacity < c.s:
                        continue
                    if any(room_busy[r][s0 + o] for o in range(c.t)):
                        continue
                    # Cặp (tiết, phòng) hợp lệ đầu tiên -> gán.
                    for tt in range(s0, s0 + c.t):
                        room_busy[r][tt] = True
                        tb[tt] = True
                    c.assigned_room = r
                    c.assigned_slot = s0 + 1
                    c.is_assigned = True
                    assigned.append(c)
                    check = True
                    placed = True
                    break
                if placed:
                    break

    return assigned
