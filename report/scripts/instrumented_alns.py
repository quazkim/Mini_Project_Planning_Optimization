#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ALNS có ghi vết (instrumented) phục vụ phân tích độ nhạy tham số.

Tái sử dụng *nguyên vẹn* các toán tử Destroy/Repair và lớp ``ScheduleState`` của
gói ``solver`` (không sao chép logic), chỉ bọc thêm vòng lặp để:
  - phơi bày tham số ``lam`` (hệ số học), ``T0`` (nhiệt độ đầu), ``cooling``.
  - ghi lại lịch sử mỗi vòng lặp: trọng số/xác suất toán tử, nhiệt độ,
    score hiện tại, score tốt nhất, toán tử được chọn, reward.

Nhờ vậy đồ thị trong báo cáo phản ánh đúng thuật toán đang chạy trong solver.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional

import common  # noqa: F401  (đảm bảo sys.path có project root)
from solver.algorithms.alns import (
    _destroy_random,
    _destroy_related_teacher,
    _destroy_worst_time,
    _repair_first_possible,
    _repair_greedy,
    _repair_regret2,
    _roulette_wheel_selection,
)
from solver.models import ClassDTO, RoomDTO
from solver.schedule_state import build_state_from_assignment

DESTROY_NAMES = ["Random", "Worst-Time", "Related-Teacher"]
REPAIR_NAMES = ["Greedy", "Regret-2", "First-Possible"]


def run_instrumented_alns(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    initial_assigned_list: List[ClassDTO],
    max_iters: int = 500,
    lam: float = 0.5,
    T0: float = 10.0,
    cooling: float = 0.98,
    pi: tuple = (10.0, 5.0, 2.0),
    destroy_frac: float = 0.15,
    seed: Optional[int] = None,
) -> Dict[str, list]:
    """Chạy ALNS và trả về lịch sử các đại lượng theo vòng lặp.

    Trả về dict gồm các list cùng độ dài (theo số vòng lặp):
      - it, T, score_current, score_best, reward
      - weights_d (list[3]), prob_d (list[3]) — trọng số & xác suất Destroy
      - weights_r (list[3]), prob_r (list[3]) — trọng số & xác suất Repair
      - chosen_d, chosen_r — chỉ số toán tử được chọn
    """
    if seed is not None:
        random.seed(seed)

    state = build_state_from_assignment(N, M, classes, rooms, initial_assigned_list)

    best_snapshot = state.snapshot()
    score_best = state.count()
    score_current = score_best

    T = T0
    PI_1, PI_2, PI_3 = pi

    ops_destroy = [_destroy_random, _destroy_worst_time, _destroy_related_teacher]
    weights_d = [1.0, 1.0, 1.0]
    ops_repair = [_repair_greedy, _repair_regret2, _repair_first_possible]
    weights_r = [1.0, 1.0, 1.0]

    hist: Dict[str, list] = {
        "it": [], "T": [], "score_current": [], "score_best": [], "reward": [],
        "weights_d": [], "prob_d": [], "weights_r": [], "prob_r": [],
        "chosen_d": [], "chosen_r": [],
    }

    def _norm(w: List[float]) -> List[float]:
        tot = sum(w)
        return [x / tot for x in w] if tot > 0 else [1.0 / len(w)] * len(w)

    it = 0
    while it < max_iters:
        it += 1
        if state.count() == 0:
            break

        idx_d = _roulette_wheel_selection(weights_d)
        idx_r = _roulette_wheel_selection(weights_r)
        op_destroy = ops_destroy[idx_d]
        op_repair = ops_repair[idx_r]

        k = max(1, int(destroy_frac * state.count()))
        for c in op_destroy(state, k):
            state.remove(c)

        u_list = state.unassigned_classes()
        op_repair(state, u_list)

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
                state.restore(best_snapshot)
                score_current = score_best
                reward = 0.0

        weights_d[idx_d] = lam * weights_d[idx_d] + (1 - lam) * reward
        weights_r[idx_r] = lam * weights_r[idx_r] + (1 - lam) * reward

        # Ghi vết SAU cập nhật trọng số (phản ánh trạng thái học tới thời điểm này).
        hist["it"].append(it)
        hist["T"].append(T)
        hist["score_current"].append(score_current)
        hist["score_best"].append(score_best)
        hist["reward"].append(reward)
        hist["weights_d"].append(list(weights_d))
        hist["prob_d"].append(_norm(weights_d))
        hist["weights_r"].append(list(weights_r))
        hist["prob_r"].append(_norm(weights_r))
        hist["chosen_d"].append(idx_d)
        hist["chosen_r"].append(idx_r)

        T *= cooling

    hist["score_best_final"] = score_best
    return hist
