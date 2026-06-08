#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ALNS: Ruin & Recreate + Simulated Annealing + trọng số thích nghi.

- 3 toán tử Destroy: Random / Worst-Time / Related-Teacher.
- 3 toán tử Repair: Greedy / Regret-2 / First-Possible.
- Chọn cặp toán tử bằng bánh xe roulette theo trọng số thích nghi.
- Chấp nhận nghiệm theo Simulated Annealing; cập nhật trọng số theo reward.
"""

from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Optional, Tuple

from ..models import ClassDTO, RoomDTO
from ..schedule_state import ScheduleState, build_state_from_assignment


# --- chọn toán tử ---


def _roulette_wheel_selection(weights: List[float]) -> int:
    """Chọn 1 chỉ số theo bánh xe roulette tỉ lệ với trọng số (>=0)."""
    total = sum(weights)
    if total <= 0:
        return random.randrange(len(weights))
    pick = random.uniform(0, total)
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if pick <= acc:
            return i
    return len(weights) - 1


# --- các toán tử Destroy ---


def _destroy_random(state: ScheduleState, k: int) -> List[ClassDTO]:
    ids = random.sample(tuple(state.assigned_ids), min(k, len(state.assigned_ids)))
    return [state.classes[i] for i in ids]  # type: ignore[misc]


def _destroy_worst_time(state: ScheduleState, k: int) -> List[ClassDTO]:
    assigned = [state.classes[i] for i in state.assigned_ids]
    assigned.sort(key=lambda c: c.t, reverse=True)  # type: ignore[union-attr]
    return assigned[:k]  # type: ignore[return-value]


def _destroy_related_teacher(state: ScheduleState, k: int) -> List[ClassDTO]:
    # Gom lớp theo giáo viên.
    by_teacher: Dict[int, List[ClassDTO]] = {}
    for i in state.assigned_ids:
        c = state.classes[i]
        by_teacher.setdefault(c.g, []).append(c)  # type: ignore[union-attr]
    if not by_teacher:
        return []
    # Chọn giáo viên có lịch dày đặc nhất (nhiều lớp nhất), tie-break ngẫu nhiên.
    max_load = max(len(v) for v in by_teacher.values())
    dense = [g for g, v in by_teacher.items() if len(v) == max_load]
    g = random.choice(dense)
    return by_teacher[g][:k]


# --- các toán tử Repair ---


def _repair_greedy(state: ScheduleState, u_list: List[ClassDTO]) -> None:
    # Ưu tiên sĩ số giảm dần, rồi thời lượng giảm dần.
    for u in sorted(u_list, key=lambda c: (c.s, c.t), reverse=True):
        pos = state.find_position(u)
        if pos is not None:
            state.insert(u, pos[0], pos[1])


def _repair_regret2(state: ScheduleState, u_list: List[ClassDTO]) -> None:
    pending = list(u_list)
    while pending:
        best_u: Optional[ClassDTO] = None
        best_pos: Optional[Tuple[int, int]] = None
        best_regret = -1.0  # regret cao = ít phòng hợp lệ
        placeable_remaining = False
        for u in pending:
            cnt, pos = state.feasible_room_count(u)
            if cnt == 0 or pos is None:
                continue
            placeable_remaining = True
            # Ít phòng hợp lệ -> hối tiếc cao. Quy ra điểm: regret lớn khi cnt nhỏ.
            regret = 1.0 / cnt
            if regret > best_regret:
                best_regret = regret
                best_u = u
                best_pos = pos
        if not placeable_remaining or best_u is None or best_pos is None:
            break
        state.insert(best_u, best_pos[0], best_pos[1])
        pending.remove(best_u)


def _repair_first_possible(state: ScheduleState, u_list: List[ClassDTO]) -> None:
    order = list(u_list)
    random.shuffle(order)
    for u in order:
        pos = state.find_position(u)
        if pos is not None:
            state.insert(u, pos[0], pos[1])


def optimize_with_alns(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    initial_assigned_list: List[ClassDTO],
    max_iters: int = 500,
    time_limit: Optional[float] = None,
) -> List[ClassDTO]:
    """ALNS: Ruin & Recreate + Simulated Annealing + trọng số thích nghi.

    Bám sát pseudocode Full_ALNS:
      - Mỗi vòng phá ~15% số lớp rồi sửa lại; chấp nhận nghiệm theo SA.
      - Cập nhật trọng số: W = Lambda*W + (1-Lambda)*Reward, với reward
        PI_1 > PI_2 > PI_3 tùy mức cải thiện.

    time_limit (giây): nếu đặt, dừng khi vượt ngân sách thời gian (dùng cho
    benchmark công bằng). Mặc định None -> chỉ dừng theo max_iters (hành vi cũ).
    """
    if N <= 0 or M <= 0:
        return list(initial_assigned_list)

    state = build_state_from_assignment(N, M, classes, rooms, initial_assigned_list)

    best_snapshot = state.snapshot()
    score_best = state.count()
    score_current = score_best

    # Tham số Luyện kim mô phỏng (SA).
    T = 10.0
    cooling_rate = 0.98

    # Rổ toán tử + trọng số thích nghi.
    ops_destroy = [_destroy_random, _destroy_worst_time, _destroy_related_teacher]
    weights_d = [1.0, 1.0, 1.0]
    ops_repair = [_repair_greedy, _repair_regret2, _repair_first_possible]
    weights_r = [1.0, 1.0, 1.0]

    lam = 0.5
    PI_1, PI_2, PI_3 = 10.0, 5.0, 2.0

    start = time.time()
    it = 0
    while it < max_iters:
        if time_limit is not None and time.time() - start > time_limit:
            break
        it += 1
        if state.count() == 0:
            break
        # Early-stop: đã xếp được toàn bộ lớp -> không thể tốt hơn.
        if score_best >= N:
            break

        # Chọn cặp toán tử bằng bánh xe roulette.
        idx_d = _roulette_wheel_selection(weights_d)
        idx_r = _roulette_wheel_selection(weights_r)
        op_destroy = ops_destroy[idx_d]
        op_repair = ops_repair[idx_r]

        # PHA 1: DESTROY ~15% số lớp đang có.
        k = max(1, int(0.15 * state.count()))
        to_remove = op_destroy(state, k)
        for c in to_remove:
            state.remove(c)

        # PHA 2: REPAIR.
        u_list = state.unassigned_classes()
        op_repair(state, u_list)

        # PHA 3: ĐÁNH GIÁ (SA) & CẬP NHẬT TRỌNG SỐ.
        score_new = state.count()
        reward = 0.0

        if score_new > score_best:
            best_snapshot = state.snapshot()
            score_best = score_new
            score_current = score_new
            reward = PI_1
        elif score_new > score_current:
            score_current = score_new
            reward = PI_2
        else:
            delta = score_best - score_new
            if T > 1e-9 and random.random() < math.exp(-delta / T):
                score_current = score_new
                reward = PI_3
            else:
                # Bác bỏ: khôi phục về nghiệm tốt nhất.
                state.restore(best_snapshot)
                score_current = score_best
                reward = 0.0

        # Cập nhật trọng số cho cả hai toán tử vừa dùng.
        weights_d[idx_d] = lam * weights_d[idx_d] + (1 - lam) * reward
        weights_r[idx_r] = lam * weights_r[idx_r] + (1 - lam) * reward

        T *= cooling_rate

    state.restore(best_snapshot)
    return [c for c in classes[1:] if c is not None and c.is_assigned]
