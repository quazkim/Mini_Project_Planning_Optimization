#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tiện ích dùng chung cho các kịch bản thực nghiệm trong báo cáo.

- Nạp project root vào sys.path để dùng được gói ``solver``.
- Đọc một file test (đúng định dạng đề) thành (N, M, classes, rooms).
- Cấu hình matplotlib (font, lưới, kích thước) thống nhất cho mọi hình.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Tuple

# --- đường dẫn ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(REPORT_DIR)
FIG_DIR = os.path.join(REPORT_DIR, "figures")
DATA_DIR = os.path.join(REPORT_DIR, "data")
TEST_DIR = os.path.join(ROOT_DIR, "test_input")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from solver.models import ClassDTO, RoomDTO  # noqa: E402


def load_instance(name: str) -> Tuple[int, int, List[Optional[ClassDTO]], List[Optional[RoomDTO]]]:
    """Đọc file ``test_input/<name>.txt`` thành cấu trúc dữ liệu của solver."""
    path = os.path.join(TEST_DIR, f"{name}.txt") if not name.endswith(".txt") else os.path.join(TEST_DIR, name)
    with open(path, "r") as f:
        data = f.read().split()
    it = iter(map(int, data))
    N = next(it)
    M = next(it)
    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i in range(1, N + 1):
        t = next(it)
        g = next(it)
        s = next(it)
        classes[i] = ClassDTO(i, t, g, s)
    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r in range(1, M + 1):
        rooms[r] = RoomDTO(r, next(it))
    return N, M, classes, rooms


def setup_matplotlib():
    """Trả về module pyplot đã cấu hình đồng nhất cho báo cáo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.figsize": (8.0, 4.8),
        "figure.dpi": 130,
        "savefig.dpi": 160,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "axes.grid": True,
        "grid.alpha": 0.30,
        "grid.linestyle": "--",
        "legend.framealpha": 0.92,
        "legend.fontsize": 9.5,
        "lines.linewidth": 1.9,
    })
    return plt


# Bảng màu nhất quán cho các toán tử / phương pháp.
PALETTE = {
    "destroy": ["#1f77b4", "#ff7f0e", "#2ca02c"],   # Random, Worst-Time, Related-Teacher
    "repair": ["#9467bd", "#8c564b", "#17becf"],     # Greedy, Regret-2, First-Possible
    "method": {
        "Greedy": "#7f7f7f",
        "Local Search": "#1f77b4",
        "ALNS": "#d62728",
        "CP-SAT": "#2ca02c",
    },
}

# Bộ dữ liệu đại diện cho 3 nhóm quy mô. Cố ý trộn cả instance "dư tài nguyên"
# (Greedy đã tối ưu) lẫn instance "nghẽn tài nguyên" (M nhỏ) để bộc lộ khác biệt
# giữa Greedy / Local Search / ALNS.
INSTANCES = {
    "small": ["test01", "test03", "hustack05", "test02", "hustack08"],   # N <= 30
    "medium": ["test05", "comp11", "test09", "hustack01"],               # N ~ 100-200
    "large": ["test07", "hustack02", "hustack03", "hustack09", "test08", "hustack10"],  # N >= 500
}
