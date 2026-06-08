#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Các đối tượng dữ liệu (DTO) của bài toán Timetabling."""

from __future__ import annotations

from typing import Optional


class ClassDTO:
    """Một lớp cần xếp lịch.

    Thuộc tính đầu vào:
      - t: số tiết liên tiếp (duration).
      - g: mã giáo viên.
      - s: số sinh viên.

    Thuộc tính trạng thái (được điền khi gán lịch):
      - assigned_slot: tiết bắt đầu, 1-based (1..60).
      - assigned_room: mã phòng được gán.
      - is_assigned: đã được xếp hay chưa.
    """

    def __init__(self, class_id: int, t: int, g: int, s: int):
        self.class_id = class_id
        self.t = t
        self.g = g
        self.s = s
        self.assigned_slot: Optional[int] = None
        self.assigned_room: Optional[int] = None
        self.is_assigned: bool = False


class RoomDTO:
    """Một phòng học với sức chứa cố định."""

    def __init__(self, room_id: int, capacity: int):
        self.room_id = room_id
        self.capacity = capacity
