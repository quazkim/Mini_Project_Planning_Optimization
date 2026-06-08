#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHẦN 2.3 (bổ sung) — CP-SAT trên dữ liệu THỰC quy mô lớn.

Trên các instance ngẫu nhiên "loose", CP-SAT chứng minh tối ưu rất nhanh. Bức
tranh thực tế khác hẳn: với dữ liệu nghẽn tài nguyên (HUStack/CTT), chi phí dựng
mô hình và việc *chứng minh* tối ưu bùng nổ. Script đo trên các instance thật với
time-limit nới rộng để bộc lộ khoảng cách cận (gap) còn lại — chính là lý do
production đặt ngưỡng N<=100 và chuyển sang metaheuristic.
"""

from __future__ import annotations

import json
import os
import time

import common
from exp_cpsat_scaling import build_and_solve

INSTANCES = ["hustack01", "hustack02", "test08"]   # N = 200, 500, 1000
TIME_LIMIT = 20.0


def main():
    rows = []
    for name in INSTANCES:
        N, M, classes, rooms = common.load_instance(name)
        t0 = time.time()
        res = build_and_solve(N, M, classes, rooms, TIME_LIMIT)
        res["wall"] = time.time() - t0
        res["instance"] = name
        res["N"], res["M"] = N, M
        rows.append(res)
        print(f"{name:10s} N={N:4d} M={M:3d} status={res['status']:10s} "
              f"wall={res['wall']:6.2f}s obj={res['objective']:4d} "
              f"bound={res['bound']:.1f} gap={res['gap']:.1f} greedy={res['greedy']} "
              f"vars={res['nvars']}", flush=True)

    with open(os.path.join(common.DATA_DIR, "cpsat_real.json"), "w") as f:
        json.dump(rows, f, indent=2)
    print("saved cpsat_real.json")


if __name__ == "__main__":
    main()
