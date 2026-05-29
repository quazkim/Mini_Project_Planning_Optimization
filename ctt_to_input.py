#!/usr/bin/env python3
"""ctt_to_input.py — Convert ITC-2007 .ctt file sang format bài toán của nhóm.

Quy tắc chuyển đổi:
  - Mỗi course có L lectures → tạo L class riêng biệt, mỗi class có t=1
  - Teacher name → teacher id số nguyên (map theo thứ tự xuất hiện)
  - Room capacity giữ nguyên
  - Bỏ qua: CURRICULA, UNAVAILABILITY_CONSTRAINTS (không có trong bài toán gốc)

Usage:
    python ctt_to_input.py datasets/comp01.ctt          # in ra stdout
    python ctt_to_input.py datasets/comp01.ctt > input.txt
    python ctt_to_input.py datasets/comp01.ctt | python main_greedy.py
"""

import sys


def convert(filepath: str) -> str:
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # ── Parse section ──────────────────────────────────────────────────────────
    section = None
    course_lines = []
    room_lines = []

    for line in lines:
        s = line.strip()
        if s == "COURSES:":
            section = "courses"
        elif s == "ROOMS:":
            section = "rooms"
        elif s in ("CURRICULA:", "UNAVAILABILITY_CONSTRAINTS:", "END."):
            section = None
        elif s == "":
            continue
        elif section == "courses":
            course_lines.append(s)
        elif section == "rooms":
            room_lines.append(s)

    # ── Build teacher map ──────────────────────────────────────────────────────
    teacher_map: dict[str, int] = {}
    next_tid = 1

    # ── Convert courses → lectures ─────────────────────────────────────────────
    # ITC-2007 course line: course_name teacher num_lectures min_days num_students
    lectures = []   # list of (t, teacher_id, num_students)

    for line in course_lines:
        parts = line.split()
        if len(parts) < 5:
            continue
        _, teacher_name, num_lec_str, _, num_students_str = parts[:5]
        num_lec     = int(num_lec_str)
        num_students = int(num_students_str)

        if teacher_name not in teacher_map:
            teacher_map[teacher_name] = next_tid
            next_tid += 1
        tid = teacher_map[teacher_name]

        for _ in range(num_lec):
            lectures.append((1, tid, num_students))   # t=1 luôn

    # ── Rooms ──────────────────────────────────────────────────────────────────
    capacities = []
    for line in room_lines:
        parts = line.split()
        if len(parts) >= 2:
            capacities.append(int(parts[1]))

    # ── Build output ───────────────────────────────────────────────────────────
    N = len(lectures)
    M = len(capacities)

    out_lines = [f"{N} {M}"]
    for t, g, s in lectures:
        out_lines.append(f"{t} {g} {s}")
    out_lines.append(" ".join(map(str, capacities)))

    return "\n".join(out_lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ctt_to_input.py <file.ctt>", file=sys.stderr)
        sys.exit(1)

    print(convert(sys.argv[1]), end="")
