
from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple



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



SLOTS_PER_DAY = 12
DAYS = 5
TOTAL_SLOTS = SLOTS_PER_DAY * DAYS  # 60




def _allowed_starts(t: int) -> List[int]:
    out: List[int] = []
    for day in range(DAYS):
        base = day * SLOTS_PER_DAY
        for offset in range(SLOTS_PER_DAY - t + 1):
            out.append(base + offset)
    return out



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


# ─── Ejection Chain helpers ───────────────────────────────────────────────────

def _do_assign(c, s0, r, room_busy, teacher_busy, room_occ, teacher_occ):
    for tt in range(s0, s0 + c.t):
        room_busy[r][tt] = True
        room_occ[r][tt] = c
        teacher_busy[c.g][tt] = True
        teacher_occ[c.g][tt] = c
    c.assigned_slot = s0 + 1
    c.assigned_room = r
    c.is_assigned = True


def _do_unassign(c, room_busy, teacher_busy, room_occ, teacher_occ):
    s0 = c.assigned_slot - 1
    r = c.assigned_room
    for tt in range(s0, s0 + c.t):
        room_busy[r][tt] = False
        room_occ[r][tt] = None
        teacher_busy[c.g][tt] = False
        teacher_occ[c.g][tt] = None
    c.assigned_slot = None
    c.assigned_room = None
    c.is_assigned = False


def _find_slot(c, room_busy, teacher_busy, rooms, sorted_room_ids):
    """Tìm (s0 0-based, room_id) đầu tiên hợp lệ cho c. Trả None nếu không có."""
    if c.g not in teacher_busy:
        teacher_busy[c.g] = [False] * TOTAL_SLOTS
    tb = teacher_busy[c.g]
    for s0 in _allowed_starts(c.t):
        conflict = False
        for tt in range(s0, s0 + c.t):
            if tb[tt]:
                conflict = True
                break
        if conflict:
            continue
        for r in sorted_room_ids:
            room = rooms[r]
            if room is None or room.capacity < c.s:
                continue
            conflict = False
            for tt in range(s0, s0 + c.t):
                if room_busy[r][tt]:
                    conflict = True
                    break
            if not conflict:
                return s0, r
    return None


def _ejection_chain(
    class_list: List[ClassDTO],
    room_busy: List[List[bool]],
    teacher_busy: Dict[int, List[bool]],
    room_occ: List[List[Optional[ClassDTO]]],
    teacher_occ: Dict[int, List[Optional[ClassDTO]]],
    rooms: List[Optional[RoomDTO]],
    sorted_room_ids: List[int],
) -> None:
    """
    Với mỗi lớp chưa xếp, thử tìm đúng 1 lớp đang chặn (victim).
    Bỏ victim ra, xếp lớp mới vào, rồi tìm chỗ mới cho victim.
    Chỉ commit nếu victim tìm được chỗ mới (Q không đổi, nhưng sắp xếp thay đổi
    → greedy pass sau có thể xếp thêm lớp mới).
    """
    improved = True
    while improved:
        improved = False
        for c in class_list:
            if c.is_assigned:
                continue

            if c.g not in teacher_occ:
                teacher_occ[c.g] = [None] * TOTAL_SLOTS
            if c.g not in teacher_busy:
                teacher_busy[c.g] = [False] * TOTAL_SLOTS

            placed = False
            for s0 in _allowed_starts(c.t):
                slots = range(s0, s0 + c.t)

                # Tìm lớp đang chặn teacher
                teacher_blockers: set = set()
                for tt in slots:
                    occ = teacher_occ[c.g][tt]
                    if occ is not None:
                        teacher_blockers.add(occ)
                if len(teacher_blockers) > 1:
                    continue

                for r in sorted_room_ids:
                    room = rooms[r]
                    if room is None or room.capacity < c.s:
                        continue

                    # Tìm lớp đang chặn phòng
                    room_blockers: set = set()
                    for tt in slots:
                        occ = room_occ[r][tt]
                        if occ is not None:
                            room_blockers.add(occ)

                    all_blockers = teacher_blockers | room_blockers
                    if len(all_blockers) != 1:
                        continue  # 0: greedy đã bắt được; >1: quá phức tạp

                    victim = next(iter(all_blockers))
                    v_s0 = victim.assigned_slot - 1
                    v_r = victim.assigned_room

                    # Tạm bỏ victim
                    _do_unassign(victim, room_busy, teacher_busy, room_occ, teacher_occ)

                    # Kiểm tra c có xếp vào (s0, r) được không
                    can_place = True
                    for tt in slots:
                        if room_busy[r][tt] or teacher_busy[c.g][tt]:
                            can_place = False
                            break

                    if can_place:
                        _do_assign(c, s0, r, room_busy, teacher_busy, room_occ, teacher_occ)

                        # Tìm chỗ mới cho victim
                        result = _find_slot(victim, room_busy, teacher_busy, rooms, sorted_room_ids)
                        if result is not None:
                            new_s0, new_r = result
                            _do_assign(victim, new_s0, new_r, room_busy, teacher_busy, room_occ, teacher_occ)
                            improved = True
                            placed = True
                            break
                        else:
                            # Rollback: không tìm được chỗ cho victim
                            _do_unassign(c, room_busy, teacher_busy, room_occ, teacher_occ)
                            _do_assign(victim, v_s0, v_r, room_busy, teacher_busy, room_occ, teacher_occ)
                    else:
                        # Khôi phục victim
                        _do_assign(victim, v_s0, v_r, room_busy, teacher_busy, room_occ, teacher_occ)

                if placed:
                    break


# ─── Greedy pass ──────────────────────────────────────────────────────────────

def _greedy_pass(
    class_list: List[ClassDTO],
    room_busy: List[List[bool]],
    teacher_busy: Dict[int, List[bool]],
    room_occ: List[List[Optional[ClassDTO]]],
    teacher_occ: Dict[int, List[Optional[ClassDTO]]],
    rooms: List[Optional[RoomDTO]],
    sorted_room_ids: List[int],
) -> None:
    check = True
    while check:
        check = False
        for c in class_list:
            if c.is_assigned:
                continue

            if c.g not in teacher_busy:
                teacher_busy[c.g] = [False] * TOTAL_SLOTS
            if c.g not in teacher_occ:
                teacher_occ[c.g] = [None] * TOTAL_SLOTS

            for start in _allowed_starts(c.t):
                if any(teacher_busy[c.g][start + offset] for offset in range(c.t)):
                    continue

                for r in sorted_room_ids:
                    if rooms[r] is None or rooms[r].capacity < c.s:
                        continue
                    if any(room_busy[r][start + offset] for offset in range(c.t)):
                        continue

                    _do_assign(c, start, r, room_busy, teacher_busy, room_occ, teacher_occ)
                    check = True
                    break

                if c.is_assigned:
                    break


# ─── Main solver ──────────────────────────────────────────────────────────────

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
    room_occ: List[List[Optional[ClassDTO]]] = [[None] * TOTAL_SLOTS for _ in range(M + 1)]
    teacher_occ: Dict[int, List[Optional[ClassDTO]]] = {}

    class_list = sorted(
        [c for c in classes if c is not None],
        key=lambda c: (c.t, c.s)
    )

    sorted_room_ids = sorted(
        range(1, M + 1),
        key=lambda r: rooms[r].capacity if rooms[r] else 0
    )

    prev_count = -1
    while True:
        _greedy_pass(class_list, room_busy, teacher_busy, room_occ, teacher_occ, rooms, sorted_room_ids)
        cur_count = sum(1 for c in class_list if c.is_assigned)
        if cur_count == prev_count:
            break
        prev_count = cur_count
        _ejection_chain(class_list, room_busy, teacher_busy, room_occ, teacher_occ, rooms, sorted_room_ids)

    return [c for c in class_list if c.is_assigned]



if __name__ == "__main__":
    N, M, classes, rooms = read_input()
    assigned = solve_greedy(N, M, classes, rooms)
    print_output(assigned)
