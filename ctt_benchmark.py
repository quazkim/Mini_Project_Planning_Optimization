#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ctt_benchmark.py — Benchmark greedy_daily.py trên ITC-2007 CB-CTT datasets

Parses all *.ctt files in datasets/, converts to our internal format,
runs all parameter combinations, and writes updated param_tuning_log.md.

Usage:
    python ctt_benchmark.py                  # benchmark + write log
    python ctt_benchmark.py --datasets-dir datasets
"""
from __future__ import annotations

import copy
import glob
import itertools
import os
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from greedy_daily import (
    ClassDTO,
    RoomDTO,
    solve_greedy_daily,
    SORT_KEYS,
    ROOM_ORDERS,
    SLOT_ORDERS,
    REPAIR_OPTIONS,
    DAY_PROC_OPTIONS,
)

# ─────────────────────────────────────────────────────────────────────────────
# ITC-2007 CB-CTT Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_ctt(filepath: str):
    """Parse a .ctt file and return everything needed to run our solver.

    ITC-2007 format:
        COURSES: course_name teacher num_lectures min_working_days num_students
        ROOMS:   room_name capacity
        Each course needs num_lectures separate 1-period lectures.
        We create one ClassDTO per lecture (t=1).

    Returns:
        N, M, classes, rooms, slots_per_day, total_days, instance_name,
        teacher_map (name → id), total_lectures
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    # ── Header ──
    header: Dict[str, str] = {}
    for line in lines:
        if ":" in line and not line.startswith("COURSES") \
                and not line.startswith("ROOMS") \
                and not line.startswith("CURRICULA") \
                and not line.startswith("UNAVAILABILITY") \
                and not line.strip() == "END.":
            key, _, val = line.partition(":")
            header[key.strip()] = val.strip()

    instance_name = header.get("Name", os.path.basename(filepath))
    days = int(header.get("Days", 5))
    periods_per_day = int(header.get("Periods_per_day", 6))

    # ── Parse sections ──
    section = None
    course_lines = []
    room_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped == "COURSES:":
            section = "courses"
            continue
        if stripped == "ROOMS:":
            section = "rooms"
            continue
        if stripped in ("CURRICULA:", "UNAVAILABILITY_CONSTRAINTS:"):
            section = "other"
            continue
        if stripped in ("END.", ""):
            section = None
            continue
        if section == "courses":
            course_lines.append(stripped)
        elif section == "rooms":
            room_lines.append(stripped)

    # ── Build teacher map ──
    teacher_map: Dict[str, int] = {}
    next_tid = 1

    # ── Convert courses → lectures (each lecture = 1-period class) ──
    lectures: List[Tuple[int, int, int]] = []  # (t=1, teacher_id, students)

    for line in course_lines:
        parts = line.split()
        if len(parts) < 5:
            continue
        # course_name teacher num_lectures min_working_days num_students
        _, teacher_name, num_lec_str, _, num_students_str = parts[:5]
        num_lec = int(num_lec_str)
        num_students = int(num_students_str)

        if teacher_name not in teacher_map:
            teacher_map[teacher_name] = next_tid
            next_tid += 1
        tid = teacher_map[teacher_name]

        for _ in range(num_lec):
            lectures.append((1, tid, num_students))  # t=1 always

    N = len(lectures)
    classes: List[Optional[ClassDTO]] = [None] * (N + 1)
    for i, (t, g, s) in enumerate(lectures, 1):
        classes[i] = ClassDTO(i, t, g, s)

    # ── Convert rooms ──
    M = len(room_lines)
    rooms: List[Optional[RoomDTO]] = [None] * (M + 1)
    for r_idx, line in enumerate(room_lines, 1):
        parts = line.split()
        if len(parts) >= 2:
            cap = int(parts[1])
        else:
            cap = 0
        rooms[r_idx] = RoomDTO(r_idx, cap)

    return (
        N, M, classes, rooms,
        periods_per_day, days,
        instance_name, teacher_map, N,  # total_lectures == N
    )


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark runner
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark(datasets_dir: str = "datasets") -> Tuple[List[dict], Dict[str, object]]:
    """Run all param combos on all .ctt files. Return (records, best_params)."""

    ctt_files = sorted(glob.glob(os.path.join(datasets_dir, "*.ctt")))
    if not ctt_files:
        print(f"[bench] No .ctt files found in {datasets_dir}/", file=sys.stderr)
        sys.exit(1)

    combos = list(itertools.product(
        SORT_KEYS, ROOM_ORDERS, SLOT_ORDERS, REPAIR_OPTIONS, DAY_PROC_OPTIONS
    ))

    total_runs = len(ctt_files) * len(combos)
    print(
        f"[bench] {len(ctt_files)} instances × {len(combos)} combos = {total_runs} runs",
        file=sys.stderr,
    )

    records: List[dict] = []
    run_idx = 0

    for ctt_path in ctt_files:
        filename = os.path.basename(ctt_path)
        try:
            N, M, base_classes, base_rooms, spd, total_days, name, _, total_lec = parse_ctt(ctt_path)
        except Exception as e:
            print(f"[bench] SKIP {filename}: {e}", file=sys.stderr)
            continue

        print(
            f"[bench] {filename:16s}  N={N:4d} lec  M={M:3d} rooms  "
            f"{total_days}d×{spd}p",
            file=sys.stderr,
        )

        for sort_key, room_order, slot_order, use_repair, day_proc in combos:
            classes_cp = copy.deepcopy(base_classes)

            t0 = time.perf_counter()
            assigned = solve_greedy_daily(
                N, M, classes_cp, base_rooms,
                sort_key=sort_key,
                room_order=room_order,
                slot_order=slot_order,
                use_repair=use_repair,
                day_processing=day_proc,
                slots_per_day=spd,
                total_days=total_days,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            Q = len(assigned)
            records.append({
                "instance": filename,
                "name": name,
                "N": N,
                "M": M,
                "slots_per_day": spd,
                "total_days": total_days,
                "sort_key": sort_key,
                "room_order": room_order,
                "slot_order": slot_order,
                "use_repair": use_repair,
                "day_processing": day_proc,
                "Q": Q,
                "total_lec": total_lec,
                "Q_pct": round(Q / total_lec * 100, 1) if total_lec > 0 else 0.0,
                "unplaced": total_lec - Q,
                "time_ms": round(elapsed_ms, 3),
            })

        run_idx += len(combos)
        if run_idx % 500 == 0 or run_idx == total_runs:
            print(f"[bench]   {run_idx}/{total_runs} total runs done", file=sys.stderr)

    # ── Select best params: maximize total Q across all instances ──
    combo_totals: Dict[tuple, int] = {}
    for rec in records:
        key = (rec["sort_key"], rec["room_order"], rec["slot_order"],
               rec["use_repair"], rec["day_processing"])
        combo_totals[key] = combo_totals.get(key, 0) + rec["Q"]

    best_key = max(combo_totals, key=combo_totals.__getitem__)
    best_params: Dict[str, object] = {
        "sort_key":       best_key[0],
        "room_order":     best_key[1],
        "slot_order":     best_key[2],
        "use_repair":     best_key[3],
        "day_processing": best_key[4],
    }

    total_q_best = combo_totals[best_key]
    total_lec_all = sum(r["total_lec"] for r in records if r["sort_key"] == best_key[0]
                        and r["room_order"] == best_key[1] and r["slot_order"] == best_key[2]
                        and r["use_repair"] == best_key[3] and r["day_processing"] == best_key[4])

    print(
        f"\n[bench] Best combo: {best_params}",
        file=sys.stderr,
    )
    print(
        f"[bench] Total Q = {total_q_best} / {total_lec_all} lectures "
        f"({round(total_q_best/total_lec_all*100,1) if total_lec_all else 0}% placed)",
        file=sys.stderr,
    )

    return records, best_params


# ─────────────────────────────────────────────────────────────────────────────
# Log writer (overwrites param_tuning_log.md)
# ─────────────────────────────────────────────────────────────────────────────

def write_benchmark_log(
    records: List[dict],
    best_params: Dict[str, object],
    filepath: str,
) -> None:

    lines: List[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    instances = list(dict.fromkeys(r["instance"] for r in records))
    n_instances = len(instances)
    n_combos = len(set(
        (r["sort_key"], r["room_order"], r["slot_order"], r["use_repair"], r["day_processing"])
        for r in records
    ))

    lines += [
        "# Greedy Parameter Tuning Log — ITC-2007 CB-CTT Benchmark",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Dataset:** ITC-2007 Curriculum-Based Course Timetabling  ",
        f"**Instances:** {n_instances} files (`toy.ctt`, `toytoy.ctt`, `comp01`–`comp21`)  ",
        f"**Parameter combos:** {n_combos}  ",
        f"**Total runs:** {len(records)}  ",
        "",
    ]

    # ── Best params table ────────────────────────────────────────────────────
    def _fmt_reason(k: str, v: object) -> str:
        reasons = {
            ("sort_key",       "s_desc"):        "Ưu tiên lớp đông SV — phòng lớn là bottleneck",
            ("sort_key",       "s_t_combo"):      "Ưu tiên (s desc, t desc) — đa tiêu chí",
            ("sort_key",       "st_desc"):        "Ưu tiên tổng gánh nặng s×t",
            ("sort_key",       "t_desc"):         "Ưu tiên lớp dài — khó xếp nhất",
            ("room_order",     "best_fit"):       "Phòng nhỏ nhất vừa đủ — bin-packing",
            ("room_order",     "worst_fit"):      "Phòng lớn nhất — luôn có chỗ",
            ("room_order",     "first_fit"):      "Phòng id nhỏ nhất",
            ("slot_order",     "forward"):        "Quét slot từ đầu ngày",
            ("slot_order",     "backward"):       "Quét slot từ cuối ngày",
            ("use_repair",     True):             "Repair pass — thêm cơ hội cho lớp sót",
            ("use_repair",     False):            "Không repair",
            ("day_processing", "daily"):          "Xử lý từng ngày — tránh slot fragmentation",
            ("day_processing", "global"):         "Toàn bộ tuần — standard greedy",
        }
        return reasons.get((k, v), str(v))

    lines += [
        "---",
        "## Bộ tham số tốt nhất (từ ITC-2007 benchmark)",
        "",
        "| Tham số | Giá trị | Lý do |",
        "|---|---|---|",
    ]
    for k, v in best_params.items():
        lines.append(f"| `{k}` | `{v}` | {_fmt_reason(k, v)} |")
    lines.append("")

    # ── Per-instance best result ─────────────────────────────────────────────
    lines += [
        "---",
        "## Kết quả tốt nhất trên từng instance",
        "",
        "| Instance | N lec | M rooms | Slots | Best Q | Fill% | sort | room | slot | repair | day_proc | ms |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    inst_groups: Dict[str, List[dict]] = defaultdict(list)
    for rec in records:
        inst_groups[rec["instance"]].append(rec)

    total_lec_sum = 0
    total_q_sum = 0

    for inst in instances:
        recs = inst_groups[inst]
        best = max(recs, key=lambda r: (r["Q"], -r["time_ms"]))
        slot_str = f"{best['total_days']}×{best['slots_per_day']}"
        total_lec_sum += best["total_lec"]
        total_q_sum += best["Q"]
        lines.append(
            f"| `{best['instance']}` | {best['N']} | {best['M']} | {slot_str} "
            f"| {best['Q']} | {best['Q_pct']}% "
            f"| `{best['sort_key']}` | `{best['room_order']}` "
            f"| `{best['slot_order']}` | `{best['use_repair']}` "
            f"| `{best['day_processing']}` | {best['time_ms']} |"
        )

    overall_fill = round(total_q_sum / total_lec_sum * 100, 1) if total_lec_sum else 0
    lines += [
        f"| **TOTAL** | **{total_lec_sum}** | — | — | **{total_q_sum}** | **{overall_fill}%** | | | | | | |",
        "",
    ]

    # ── Top 20 combos by total Q ─────────────────────────────────────────────
    lines += [
        "---",
        "## Top 20 Configurations (tổng Q trên toàn bộ ITC-2007)",
        "",
        "| Rank | sort_key | room_order | slot_order | repair | day_proc | Total Q | Avg Fill% | Avg ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    combo_stats: Dict[tuple, dict] = {}
    for rec in records:
        key = (rec["sort_key"], rec["room_order"], rec["slot_order"],
               rec["use_repair"], rec["day_processing"])
        if key not in combo_stats:
            combo_stats[key] = {"total_Q": 0, "total_lec": 0, "count": 0, "total_ms": 0.0}
        combo_stats[key]["total_Q"] += rec["Q"]
        combo_stats[key]["total_lec"] += rec["total_lec"]
        combo_stats[key]["count"] += 1
        combo_stats[key]["total_ms"] += rec["time_ms"]

    ranked = sorted(combo_stats.items(), key=lambda x: -x[1]["total_Q"])[:20]

    best_key_tuple = (
        best_params["sort_key"], best_params["room_order"],
        best_params["slot_order"], best_params["use_repair"],
        best_params["day_processing"],
    )

    for rank, (key, st) in enumerate(ranked, 1):
        avg_fill = round(st["total_Q"] / st["total_lec"] * 100, 1) if st["total_lec"] else 0
        avg_ms = round(st["total_ms"] / st["count"], 3)
        marker = " **◀ best**" if key == best_key_tuple else ""
        lines.append(
            f"| {rank}{marker} | `{key[0]}` | `{key[1]}` | `{key[2]}` "
            f"| `{key[3]}` | `{key[4]}` "
            f"| {st['total_Q']} | {avg_fill}% | {avg_ms} |"
        )
    lines.append("")

    # ── Ablation ─────────────────────────────────────────────────────────────
    lines += [
        "---",
        "## Ablation — Ảnh hưởng từng tham số trên ITC-2007",
        "",
        "> Mỗi hàng tổng hợp tất cả runs có giá trị tham số đó, bất kể các tham số khác.",
        "",
    ]

    param_options = [
        ("sort_key",       SORT_KEYS,        "Chiến lược sắp xếp lớp học"),
        ("room_order",     ROOM_ORDERS,       "Chiến lược chọn phòng"),
        ("slot_order",     SLOT_ORDERS,       "Hướng quét slot trong ngày"),
        ("use_repair",     REPAIR_OPTIONS,    "Có repair pass không"),
        ("day_processing", DAY_PROC_OPTIONS,  "Xử lý theo ngày hay toàn cục"),
    ]

    for param_name, options, desc in param_options:
        lines += [
            f"### `{param_name}` — {desc}",
            "",
            f"| {param_name} | Total Q | Avg Fill% | Rank |",
            "|---|---|---|---|",
        ]
        rows = []
        for val in options:
            matching = [r for r in records if str(r[param_name]) == str(val)]
            if not matching:
                continue
            total_q = sum(r["Q"] for r in matching)
            total_l = sum(r["total_lec"] for r in matching)
            avg_fill = round(total_q / total_l * 100, 1) if total_l else 0
            is_best = str(val) == str(best_params.get(param_name))
            rows.append((val, total_q, avg_fill, is_best))

        rows.sort(key=lambda x: -x[1])
        for rank_i, (val, total_q, avg_fill, is_best) in enumerate(rows, 1):
            marker = " **← chọn**" if is_best else ""
            lines.append(f"| `{val}`{marker} | {total_q} | {avg_fill}% | #{rank_i} |")
        lines.append("")

    # ── Daily vs Global ──────────────────────────────────────────────────────
    lines += [
        "---",
        "## Day-by-Day vs Global — so sánh trực tiếp",
        "",
        "| Instance | N | Daily Q | Global Q | Δ | Daily Fill% | Global Fill% |",
        "|---|---|---|---|---|---|---|",
    ]

    for inst in instances:
        recs = inst_groups[inst]
        N_val = recs[0]["N"]
        tl = recs[0]["total_lec"]
        daily_recs  = [r for r in recs if r["day_processing"] == "daily"]
        global_recs = [r for r in recs if r["day_processing"] == "global"]
        if not daily_recs or not global_recs:
            continue
        bd = max(daily_recs,  key=lambda r: r["Q"])
        bg = max(global_recs, key=lambda r: r["Q"])
        delta = bd["Q"] - bg["Q"]
        d_str = f"+{delta}" if delta >= 0 else str(delta)
        lines.append(
            f"| `{inst}` | {N_val} "
            f"| {bd['Q']} | {bg['Q']} | {d_str} "
            f"| {bd['Q_pct']}% | {bg['Q_pct']}% |"
        )

    lines += [
        "",
        "---",
        "*Tự động sinh bởi `python ctt_benchmark.py` trên ITC-2007 CB-CTT dataset*",
        "",
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[bench] Log written → {filepath}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Update BEST_PARAMS in greedy_daily.py
# ─────────────────────────────────────────────────────────────────────────────

def update_greedy_best_params(best_params: Dict[str, object]) -> None:
    """Rewrite the BEST_PARAMS block in greedy_daily.py using line-based replacement."""

    source_path = os.path.join(os.path.dirname(__file__), "greedy_daily.py")
    with open(source_path, encoding="utf-8") as f:
        src_lines = f.readlines()

    def _fmt(v: object) -> str:
        return ("True" if v else "False") if isinstance(v, bool) else f'"{v}"'

    # Find the start of BEST_PARAMS block and the closing }
    start_line = None
    end_line = None
    for i, line in enumerate(src_lines):
        if "BEST_PARAMS" in line and "Dict[str, object]" in line and "=" in line:
            start_line = i
        if start_line is not None and i > start_line and line.strip() == "}":
            end_line = i
            break

    if start_line is None or end_line is None:
        print("[bench] Could not locate BEST_PARAMS block — skipping auto-update", file=sys.stderr)
        return

    # Build replacement lines
    new_block = []
    new_block.append(
        "# Best parameters — chosen from ITC-2007 CB-CTT benchmark "
        "(see param_tuning_log.md)\n"
    )
    new_block.append("BEST_PARAMS: Dict[str, object] = {\n")
    for k, v in best_params.items():
        new_block.append(f'    "{k}": {_fmt(v)},\n')
    new_block.append("}\n")

    # Replace lines [start_line-1 .. end_line] (include the comment line above if exists)
    insert_at = start_line
    # also remove the comment line immediately above if it mentions "chosen from"
    if start_line > 0 and "chosen from" in src_lines[start_line - 1]:
        insert_at = start_line - 1

    updated = src_lines[:insert_at] + new_block + src_lines[end_line + 1:]

    with open(source_path, "w", encoding="utf-8") as f:
        f.writelines(updated)

    print(f"[bench] greedy_daily.py BEST_PARAMS updated to: {best_params}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    datasets_dir = "datasets"
    for arg in sys.argv[1:]:
        if arg.startswith("--datasets-dir="):
            datasets_dir = arg.split("=", 1)[1]
        elif arg == "--datasets-dir":
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                datasets_dir = sys.argv[idx + 1]

    records, best_params = run_benchmark(datasets_dir)
    write_benchmark_log(records, best_params, "param_tuning_log.md")
    update_greedy_best_params(best_params)

    print("\n=== Best Parameters (ITC-2007 benchmark) ===")
    for k, v in best_params.items():
        print(f"  {k:20s} = {v}")
