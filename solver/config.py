#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Hằng số cấu hình chung cho bài toán Timetabling.

- 5 ngày, mỗi ngày 12 tiết => tổng 60 tiết (slots).
- Một lớp không được vượt ranh giới ngày.
"""

from __future__ import annotations

SLOTS_PER_DAY = 12
DAYS = 5
TOTAL_SLOTS = SLOTS_PER_DAY * DAYS  # 60
