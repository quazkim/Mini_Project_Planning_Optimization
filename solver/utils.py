#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tiện ích dùng chung: log, sinh start hợp lệ, reset trạng thái."""

from __future__ import annotations

import sys
from typing import List, Optional

from .config import DAYS, SLOTS_PER_DAY
from .models import ClassDTO


def debug(msg: str) -> None:
    """Ghi log ra stderr để không làm hỏng stdout dành cho judge."""
    sys.stderr.write(msg.rstrip() + "\n")


def allowed_starts_for_duration(t: int) -> List[int]:
    """Trả về các tiết bắt đầu hợp lệ (0-based) sao cho lớp không vượt ngày.

    Ràng buộc: với mỗi ngày, offset trong ngày <= SLOTS_PER_DAY - t.
    """
    allowed: List[int] = []
    max_in_day = SLOTS_PER_DAY - t
    for day in range(DAYS):
        base = day * SLOTS_PER_DAY
        for offset in range(max_in_day + 1):
            allowed.append(base + offset)
    return allowed


def reset_assignments(classes: List[Optional[ClassDTO]]) -> None:
    """Xóa toàn bộ trạng thái gán lịch của các lớp."""
    for c in classes[1:]:
        if c is None:
            continue
        c.assigned_slot = None
        c.assigned_room = None
        c.is_assigned = False
