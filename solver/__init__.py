#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Gói giải bài toán Timetabling.

Tổ chức theo nguyên tắc "1 thuật toán 1 file":
  - config.py          : hằng số (slots/days).
  - models.py          : ClassDTO, RoomDTO.
  - utils.py           : tiện ích dùng chung.
  - io_handler.py      : đọc/ghi dữ liệu.
  - schedule_state.py  : ScheduleState cho metaheuristic.
  - algorithms/        : mỗi thuật toán một file (cp_sat, greedy, local_search, alns).
  - runner.py          : điều phối chọn thuật toán.
"""

from __future__ import annotations

from .algorithms import (
    optimize_with_alns,
    optimize_with_local_search,
    solve_with_cp_sat,
    solve_with_greedy,
)
from .io_handler import print_output, read_input
from .models import ClassDTO, RoomDTO
from .runner import optimize_with_metaheuristic, solve

__all__ = [
    "ClassDTO",
    "RoomDTO",
    "read_input",
    "print_output",
    "solve_with_cp_sat",
    "solve_with_greedy",
    "optimize_with_local_search",
    "optimize_with_alns",
    "optimize_with_metaheuristic",
    "solve",
]
