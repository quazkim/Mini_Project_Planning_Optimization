#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Đọc input từ stdin và xuất kết quả ra stdout theo định dạng judge."""

from __future__ import annotations

import sys
from typing import List, Optional, Tuple

from .models import ClassDTO, RoomDTO


def read_input() -> Tuple[int, int, List[Optional[ClassDTO]], List[Optional[RoomDTO]]]:
    """Đọc N, M, danh sách lớp và sức chứa phòng từ stdin.

    Định dạng:
      N M
      t g s   (lặp N lần)
      c       (lặp M lần)
    """
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, 0, [None], [None]

    it = iter(map(int, data))
    try:
        N = next(it)
        M = next(it)
    except StopIteration:
        raise ValueError("Invalid input: missing N M")

    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i in range(1, N + 1):
        try:
            t = next(it)
            g = next(it)
            s = next(it)
        except StopIteration:
            raise ValueError("Invalid input: missing class lines")
        classes[i] = ClassDTO(i, t, g, s)

    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r in range(1, M + 1):
        try:
            cap = next(it)
        except StopIteration:
            raise ValueError("Invalid input: missing room capacities")
        rooms[r] = RoomDTO(r, cap)

    # Dư token thì bỏ qua (robustness).
    return N, M, classes, rooms


def print_output(assigned_list: List[ClassDTO]) -> None:
    """In số lớp xếp được và từng dòng `class_id slot room` (slot 1-based)."""
    assigned_sorted = sorted(assigned_list, key=lambda c: c.class_id)
    out_lines = [str(len(assigned_sorted))]
    for c in assigned_sorted:
        out_lines.append(f"{c.class_id} {c.assigned_slot} {c.assigned_room}")
    sys.stdout.write("\n".join(out_lines))
