#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Điều phối giải thuật theo chế độ (mode).

Tách riêng phần "chọn thuật toán nào" khỏi từng thuật toán, để main.py chỉ còn
là điểm vào mỏng (đọc input -> solve -> in output).
"""

from __future__ import annotations

from typing import List, Optional

from .algorithms import (
    optimize_with_alns,
    optimize_with_local_search,
    solve_with_cp_sat,
    solve_with_greedy,
)
from .models import ClassDTO, RoomDTO
from .utils import debug

# Ngưỡng N để CP-SAT còn giải kịp; trên ngưỡng dùng Greedy + metaheuristic.
CP_SAT_MAX_N = 100


def optimize_with_metaheuristic(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    initial_assigned_list: List[ClassDTO],
) -> List[ClassDTO]:
    """Tinh chỉnh nghiệm Greedy bằng metaheuristic.

    Mặc định dùng Local Search (Ejection Chain): nhanh, an toàn về thời gian và
    chỉ làm tăng (không giảm) số lớp xếp được. ALNS mạnh hơn nhưng tốn thời gian
    hơn (Regret-2 nặng với N lớn) nên để gọi tường minh khi cần.
    """
    return optimize_with_local_search(N, M, classes, rooms, initial_assigned_list)


def solve(
    N: int,
    M: int,
    classes: List[Optional[ClassDTO]],
    rooms: List[Optional[RoomDTO]],
    mode: str = "AUTO",
) -> List[ClassDTO]:
    """Chọn và chạy giải thuật phù hợp, trả về danh sách lớp đã xếp.

    mode:
      - "AUTO"        : N nhỏ -> CP-SAT, N lớn -> Greedy + metaheuristic.
      - "CP_ONLY"     : chỉ chạy CP-SAT.
      - "GREEDY_ONLY" : chỉ chạy Greedy.
      - "ALNS"        : Greedy + ALNS.
    """
    if mode == "CP_ONLY":
        debug("--- ĐANG CHẠY CHẾ ĐỘ CHỈ ĐỊNH: CP-SAT SOLVER ---")
        _, assigned_list = solve_with_cp_sat(N, M, classes, rooms)
        return assigned_list

    if mode == "GREEDY_ONLY":
        debug("--- ĐANG CHẠY CHẾ ĐỘ CHỈ ĐỊNH: GREEDY BASELINE ---")
        return solve_with_greedy(N, M, classes, rooms)

    if mode == "ALNS":
        debug("--- ĐANG CHẠY CHẾ ĐỘ CHỈ ĐỊNH: GREEDY + ALNS ---")
        greedy_res = solve_with_greedy(N, M, classes, rooms)
        return optimize_with_alns(N, M, classes, rooms, greedy_res)

    # Chế độ "AUTO" chuẩn để nộp bài HUSTack.
    if N <= CP_SAT_MAX_N:
        try:
            _, cp_result = solve_with_cp_sat(N, M, classes, rooms)
            if cp_result:
                # CP-SAT tìm được nghiệm (luôn >= Greedy nhờ warm-start).
                return cp_result
            # CP-SAT timeout chưa kịp tìm nghiệm nào -> classes đã reset sạch.
            debug("[AUTO] CP-SAT không tìm được nghiệm, fallback Greedy...")
        except Exception as e:
            # ImportError (không có ortools) hoặc lỗi bất ngờ khác.
            debug(f"[AUTO] CP-SAT lỗi ({e}), fallback Greedy...")

    greedy_res = solve_with_greedy(N, M, classes, rooms)
    return optimize_with_metaheuristic(N, M, classes, rooms, greedy_res)
