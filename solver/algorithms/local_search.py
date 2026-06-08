#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Local Search dùng Ejection Chain.

Cố nhét thêm các lớp chưa xếp: nếu không chèn trực tiếp được, "đá" một lớp
đang xếp ra lấy chỗ cho lớp mới, rồi tìm lại chỗ cho lớp bị đá. Chỉ giữ lại
nước đi khi nó có lợi (lớp mới tốn ít tiết hơn), ngược lại revert.
"""

from __future__ import annotations

import random
import time
from typing import List, Optional

from ..models import ClassDTO, RoomDTO
from ..schedule_state import build_state_from_assignment


def optimize_with_local_search(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    initial_assigned_list: List[ClassDTO],
    max_iters: int = 2000,
    time_limit: Optional[float] = None,
) -> List[ClassDTO]:
    """Local Search dùng Ejection Chain để cố nhét thêm lớp chưa xếp.

    Logic bám sát pseudocode LocalSearch_EjectionChain:
      1. Chọn ngẫu nhiên 1 lớp chờ u.
      2. Thử chèn trực tiếp; nếu được thì giữ và cập nhật best.
      3. Nếu không, "đá" 1 lớp v đang xếp ra để lấy chỗ cho u, rồi tìm lại chỗ
         cho v. Nếu không trả được v về, chỉ giữ u khi u tốn ít tiết hơn v;
         ngược lại revert toàn bộ.

    time_limit (giây): nếu đặt, dừng khi vượt ngân sách thời gian (dùng cho
    benchmark công bằng). Mặc định None -> chỉ dừng theo max_iters (hành vi cũ).
    """
    if N <= 0 or M <= 0:
        return list(initial_assigned_list)

    state = build_state_from_assignment(N, M, classes, rooms, initial_assigned_list)

    best_snapshot = state.snapshot()
    best_count = state.count()

    # U_list: các lớp hiện chưa được xếp.
    u_list: List[ClassDTO] = state.unassigned_classes()

    start = time.time()
    it = 0
    while it < max_iters and u_list:
        if time_limit is not None and time.time() - start > time_limit:
            break
        it += 1
        u = random.choice(u_list)

        # BƯỚC 1: thử chèn trực tiếp.
        pos = state.find_position(u)
        if pos is not None:
            state.insert(u, pos[0], pos[1])
            u_list.remove(u)
            if state.count() > best_count:
                best_count = state.count()
                best_snapshot = state.snapshot()
            continue

        # BƯỚC 2: Ejection Chain — cần có lớp đang xếp để đá ra.
        if not state.assigned_ids:
            continue
        v = classes[random.choice(tuple(state.assigned_ids))]
        old_v = (v.assigned_room, v.assigned_slot)  # lưu vị trí cũ (room, slot 1-based)
        state.remove(v)
        u_list.append(v)

        pos_u = state.find_position(u)
        if pos_u is not None:
            state.insert(u, pos_u[0], pos_u[1])
            u_list.remove(u)

            # Cố nhét lại v vào vị trí khác.
            pos_v = state.find_position(v)
            if pos_v is not None:
                state.insert(v, pos_v[0], pos_v[1])
                u_list.remove(v)
                if state.count() > best_count:
                    best_count = state.count()
                    best_snapshot = state.snapshot()
            else:
                # Không trả được v về chỗ nào.
                if u.t < v.t:
                    # Giữ u (tốn ít tiết hơn -> lợi về sau), v ở lại U_list.
                    pass
                else:
                    # Revert: rút u ra, trả v về vị trí cũ.
                    state.remove(u)
                    u_list.append(u)
                    u_list.remove(v)
                    state.insert(v, old_v[0], old_v[1] - 1)  # type: ignore[index]
        else:
            # u vẫn không nhét được -> trả v về chỗ cũ.
            u_list.remove(v)
            state.insert(v, old_v[0], old_v[1] - 1)  # type: ignore[index]

    state.restore(best_snapshot)
    return [c for c in classes[1:] if c is not None and c.is_assigned]
