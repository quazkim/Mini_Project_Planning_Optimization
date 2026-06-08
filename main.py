#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Điểm vào của bộ giải Timetabling.

Bài toán: Xếp thời khóa biểu
- 5 ngày, mỗi ngày 12 tiết => tổng 60 tiết (slots).
- Mỗi lớp i: t(i) số tiết liên tiếp, g(i) mã giáo viên, s(i) số sinh viên.
- Mỗi phòng v có sức chứa c(v).

Output: Q dòng `i u v` (class_id, slot bắt đầu 1-based, room_id).

Toàn bộ logic được tách thành gói `solver/` theo nguyên tắc 1 thuật toán 1 file;
file này chỉ làm: đọc input -> điều phối giải -> in output.
"""

from __future__ import annotations

from typing import List

from solver import ClassDTO, print_output, read_input, solve

# Chọn chế độ chạy:
#   "AUTO"        : Nhỏ chạy CP-SAT, lớn chạy Greedy + metaheuristic (chuẩn nộp bài).
#   "CP_ONLY"     : Chỉ chạy CP-SAT (dành cho người làm CP-SAT test máy).
#   "GREEDY_ONLY" : Chỉ chạy Greedy (dành cho người làm Greedy test máy).
#   "ALNS"        : Greedy + ALNS (test metaheuristic mạnh).
MODE_CHOOSE = "AUTO"


def main() -> None:
    N, M, classes, rooms = read_input()
    assigned_list: List[ClassDTO] = solve(N, M, classes, rooms, mode=MODE_CHOOSE)
    print_output(assigned_list)


if __name__ == "__main__":
    main()
