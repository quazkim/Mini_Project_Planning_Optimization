#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ScheduleState: quản lý trạng thái lịch để metaheuristic thao tác nhanh."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .config import TOTAL_SLOTS
from .models import ClassDTO, RoomDTO
from .utils import allowed_starts_for_duration, reset_assignments


class ScheduleState:
    """Theo dõi trạng thái phòng/giáo viên và cung cấp insert/remove nhanh.

    Theo dõi:
      - room_busy[r][time]    : phòng r có bận tại tiết time (0-based) không.
      - teacher_busy[g][time] : giáo viên g có bận tại tiết time không.

    Quy ước thời gian:
      - Nội bộ dùng slot 0-based [0..59].
      - ClassDTO.assigned_slot lưu 1-based (đồng bộ với phần còn lại của project),
        nên insert nhận start 0-based còn snapshot lưu lại theo 1-based.
    """

    def __init__(
        self,
        N: int,
        M: int,
        classes: List[Optional[ClassDTO]],
        rooms: List[Optional[RoomDTO]],
    ):
        self.N = N
        self.M = M
        self.classes = classes
        self.rooms = rooms

        self.room_busy: List[List[bool]] = [[False] * TOTAL_SLOTS for _ in range(M + 1)]
        self.teacher_busy: Dict[int, List[bool]] = {}

        # Tập class_id đang được xếp trong lịch hiện tại.
        self.assigned_ids: set = set()

        # Cache các start hợp lệ theo thời lượng để khỏi tính lại nhiều lần.
        self._allowed_cache: Dict[int, List[int]] = {}

    # --- tiện ích nội bộ ---

    def _teacher_arr(self, g: int) -> List[bool]:
        arr = self.teacher_busy.get(g)
        if arr is None:
            arr = [False] * TOTAL_SLOTS
            self.teacher_busy[g] = arr
        return arr

    def _allowed(self, t: int) -> List[int]:
        a = self._allowed_cache.get(t)
        if a is None:
            a = allowed_starts_for_duration(t)
            self._allowed_cache[t] = a
        return a

    # --- kiểm tra & thao tác trạng thái ---

    def can_place(self, c: ClassDTO, r: int, s0: int) -> bool:
        """Kiểm tra lớp c có đặt được vào phòng r bắt đầu tại slot s0 (0-based)."""
        room = self.rooms[r]
        if room is None or room.capacity < c.s:
            return False
        rb = self.room_busy[r]
        tb = self._teacher_arr(c.g)
        for tt in range(s0, s0 + c.t):
            if rb[tt] or tb[tt]:
                return False
        return True

    def insert(self, c: ClassDTO, r: int, s0: int) -> None:
        """Chèn lớp c vào phòng r tại slot s0 (0-based) và cập nhật trạng thái."""
        rb = self.room_busy[r]
        tb = self._teacher_arr(c.g)
        for tt in range(s0, s0 + c.t):
            rb[tt] = True
            tb[tt] = True
        c.assigned_room = r
        c.assigned_slot = s0 + 1  # 1-based ra ngoài
        c.is_assigned = True
        self.assigned_ids.add(c.class_id)

    def remove(self, c: ClassDTO) -> None:
        """Rút lớp c khỏi lịch và giải phóng các tiết đang chiếm."""
        if not c.is_assigned or c.assigned_room is None or c.assigned_slot is None:
            return
        r = c.assigned_room
        s0 = c.assigned_slot - 1
        rb = self.room_busy[r]
        tb = self._teacher_arr(c.g)
        for tt in range(s0, s0 + c.t):
            rb[tt] = False
            tb[tt] = False
        c.assigned_room = None
        c.assigned_slot = None
        c.is_assigned = False
        self.assigned_ids.discard(c.class_id)

    def find_position(self, c: ClassDTO) -> Optional[Tuple[int, int]]:
        """Trả về (room, start0) hợp lệ đầu tiên cho lớp c, hoặc None."""
        for r in range(1, self.M + 1):
            room = self.rooms[r]
            if room is None or room.capacity < c.s:
                continue
            for s0 in self._allowed(c.t):
                if self.can_place(c, r, s0):
                    return (r, s0)
        return None

    def feasible_room_count(self, c: ClassDTO) -> Tuple[int, Optional[Tuple[int, int]]]:
        """Đếm số phòng hợp lệ cho lớp c và trả kèm vị trí trống đầu tiên.

        Dùng cho Regret-2: lớp càng ít phòng hợp lệ thì độ hối tiếc càng cao.
        """
        count = 0
        first: Optional[Tuple[int, int]] = None
        for r in range(1, self.M + 1):
            room = self.rooms[r]
            if room is None or room.capacity < c.s:
                continue
            for s0 in self._allowed(c.t):
                if self.can_place(c, r, s0):
                    count += 1
                    if first is None:
                        first = (r, s0)
                    break  # chỉ cần biết phòng này có chỗ là đủ
        return count, first

    def count(self) -> int:
        return len(self.assigned_ids)

    # --- snapshot / khôi phục ---

    def snapshot(self) -> Dict[int, Tuple[int, int]]:
        """Sao chép nhẹ lịch hiện tại: class_id -> (room, slot 1-based)."""
        snap: Dict[int, Tuple[int, int]] = {}
        for cid in self.assigned_ids:
            c = self.classes[cid]
            snap[cid] = (c.assigned_room, c.assigned_slot)  # type: ignore[arg-type]
        return snap

    def restore(self, snap: Dict[int, Tuple[int, int]]) -> None:
        """Khôi phục trạng thái về đúng snapshot đã lưu."""
        for cid in list(self.assigned_ids):
            self.remove(self.classes[cid])
        for cid, (r, slot) in snap.items():
            self.insert(self.classes[cid], r, slot - 1)

    def unassigned_classes(self) -> List[ClassDTO]:
        """Danh sách các lớp hiện chưa được xếp."""
        result: List[ClassDTO] = []
        for c in self.classes[1:]:
            if c is None:
                continue
            if c.class_id not in self.assigned_ids:
                result.append(c)
        return result


def build_state_from_assignment(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    initial_assigned_list: List[ClassDTO],
) -> ScheduleState:
    """Dựng ScheduleState sạch rồi nạp lại nghiệm ban đầu (từ Greedy)."""
    # Chốt lại vị trí trước khi reset, vì initial_assigned_list dùng chung
    # tham chiếu ClassDTO với `classes` (reset sẽ xóa assigned_slot).
    placements = [
        (c.class_id, c.assigned_room, c.assigned_slot)
        for c in initial_assigned_list
        if c.assigned_room is not None and c.assigned_slot is not None
    ]
    reset_assignments(classes)
    state = ScheduleState(N, M, classes, rooms)
    for cid, room, slot in placements:
        # placements mang slot 1-based; insert cần 0-based.
        state.insert(classes[cid], room, slot - 1)  # type: ignore[arg-type]
    return state
