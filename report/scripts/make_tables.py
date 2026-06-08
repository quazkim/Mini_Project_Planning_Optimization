#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh các bảng LaTeX (.tex) từ kết quả JSON của các thực nghiệm.

Đầu ra ghi vào report/data/*.tex để main.tex \\input. Chạy SAU khi các script
exp_*.py đã tạo xong JSON.
"""

from __future__ import annotations

import json
import os

import common

D = common.DATA_DIR


def _load(name):
    with open(os.path.join(D, name)) as f:
        return json.load(f)


def _w(name, text):
    with open(os.path.join(D, name), "w") as f:
        f.write(text)
    print("wrote", name)


# ---------- Bảng CP-SAT scaling ----------
def cpsat_scaling():
    rows = _load("cpsat_scaling.json")
    body = "\n".join(
        f"{r['N']} & {r['nvars']} & {r['elapsed']:.2f} & {r['status']} & "
        f"{r['objective']} & {r['gap']:.0f} \\\\"
        for r in rows
    )
    tex = r"""\begin{table}[ht]
\centering\small
\caption{CP-SAT trên dữ liệu ngẫu nhiên ``loose'' ($M=8$): số biến và thời gian
tăng theo $N$, vẫn chứng minh được tối ưu.}
\label{tab:cpsat-scaling}
\begin{tabular}{rrrlrr}
\toprule
$N$ & Số biến & Thời gian (s) & Trạng thái & $Q$ (obj) & Gap \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    _w("cpsat_table.tex", tex)


# ---------- Bảng CP-SAT trên dữ liệu thực ----------
def cpsat_real():
    rows = _load("cpsat_real.json")
    body = "\n".join(
        f"\\texttt{{{r['instance']}}} & {r['N']} & {r['M']} & {r['nvars']} & "
        f"{r['wall']:.2f} & {r['status']} & {r['greedy']} & {r['objective']} & "
        f"{r['bound']:.0f} & {r['gap']:.0f} \\\\"
        for r in rows
    )
    tex = r"""\begin{table}[ht]
\centering\small
\caption{CP-SAT trên dữ liệu thực nghẽn tài nguyên (time-limit $20$s). Khi $N$
lớn, solver chỉ đạt \textsc{feasible} với gap dương: không kịp chứng minh tối ưu.}
\label{tab:cpsat-real}
\begin{tabular}{lrrrrlrrrr}
\toprule
Instance & $N$ & $M$ & Số biến & Wall (s) & Trạng thái & Greedy & $Q$ & Cận trên & Gap \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    _w("cpsat_real_table.tex", tex)


# ---------- Bảng môi trường & giao thức (8.1) ----------
def bench_env():
    e = _load("bench_env.json")
    reps = e.get("reps", {})
    nseed = (str(reps.get("small", "?")) + " (nhỏ/vừa), "
             + str(reps.get("large", "?")) + " (lớn)") if reps else "?"
    seeds_pool = ", ".join(str(s) for s in e["seeds"])
    tex = r"""\begin{table}[H]
\centering\small
\caption{Môi trường thực nghiệm và giao thức đánh giá công bằng.}
\label{tab:bench-env}
\begin{tabular}{ll}
\toprule
Hạng mục & Giá trị \\
\midrule
Hệ điều hành & \texttt{%s} \\
CPU & \texttt{%s} (%s nhân) \\
Python & %s \\
OR-Tools & %s \\
Ngân sách thời gian chung & %.0f giây / instance (LS, ALNS, CP-SAT) \\
Số lần lặp (seed) & %s \\
Tập seed & lấy từ \{%s\} \\
\bottomrule
\end{tabular}
\end{table}
""" % (e["platform"], e["processor"], e["cpu_count"], e["python"],
       e["ortools"], e["time_limit_s"], nseed, seeds_pool)
    _w("bench_env_table.tex", tex)


# ---------- Bảng benchmark nhóm nhỏ ----------
def bench_small():
    data = _load("benchmark.json")["small"]
    body = ""
    for r in data:
        opt = r["cpsat"]["Q"]
        pa = 100.0 * r["alns"]["avg"] / opt if opt else 0
        pl = 100.0 * r["ls"]["avg"] / opt if opt else 0
        body += (
            f"\\texttt{{{r['instance']}}} & {r['N']} & {r['M']} & "
            f"{opt} & {r['greedy']['Q']} & "
            f"{r['ls']['avg']:.1f} & {r['alns']['avg']:.1f} & "
            f"{pl:.0f}\\% & {pa:.0f}\\% \\\\\n"
        )
    tex = r"""\begin{table}[H]
\centering\small
\caption{Nhóm nhỏ ($N\le 30$): CP-SAT là chuẩn tối ưu. LS/ALNS trung bình các seed.}
\label{tab:bench-small}
\begin{tabular}{lrr rr rr rr}
\toprule
Instance & $N$ & $M$ & CP-SAT & Greedy & LS avg & ALNS avg & \%opt(LS) & \%opt(ALNS) \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}
\end{table}
"""
    _w("bench_small_table.tex", tex)


# ---------- Bảng nhóm trung bình / lớn ----------
def _group_table(size, caption, label, fname):
    data = _load("benchmark.json")[size]
    body = ""
    for r in data:
        ls, al, cp = r["ls"], r["alns"], r["cpsat"]
        gain = al["avg"] - r["greedy"]["Q"]
        body += (
            f"\\texttt{{{r['instance']}}} & {r['N']} & {r['M']} & "
            f"{r['greedy']['Q']} & "
            f"{ls['min']:.0f}/{ls['avg']:.1f}/{ls['max']:.0f} & "
            f"{al['min']:.0f}/{al['avg']:.1f}/{al['max']:.0f} & {al['std']:.2f} & "
            f"{cp['Q']} ({cp['status'][:4]}) & "
            f"{gain:+.1f} \\\\\n"
        )
    tex = r"""\begin{table}[H]
\centering\small
\caption{""" + caption + r"""}
\label{""" + label + r"""}
\begin{tabular}{lrr r l ll l r}
\toprule
\multirow{2}{*}{Instance} & \multirow{2}{*}{$N$} & \multirow{2}{*}{$M$}
& \multirow{2}{*}{Greedy}
& \multicolumn{1}{c}{LS} & \multicolumn{2}{c}{ALNS} & \multirow{2}{*}{CP-SAT}
& \multirow{2}{*}{$\Delta$(ALNS$-$Gr)} \\
\cmidrule(lr){5-5}\cmidrule(lr){6-7}
& & & & min/avg/max & min/avg/max & std & & \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}
\end{table}
"""
    _w(fname, tex)


# ---------- Bảng đánh đổi thời gian/chất lượng ----------
def tradeoff():
    bench = _load("benchmark.json")
    body = ""
    for size in ["small", "medium", "large"]:
        for r in bench[size]:
            la = r["ls"]["avg"]
            aa = r["alns"]["avg"]
            gain_pct = 100.0 * (aa - la) / la if la else 0.0
            body += (
                f"\\texttt{{{r['instance']}}} & {size} & {r['N']} & "
                f"{r['ls_fast']['time']*1000:.1f} & {r['alns']['time']:.2f} & "
                f"{la:.1f} & {aa:.1f} & {gain_pct:+.2f}\\% \\\\\n"
            )
    tex = r"""\begin{table}[H]
\centering\small
\caption{Đánh đổi thời gian--chất lượng: Local Search (hội tụ tự nhiên) so với
ALNS (ngân sách $30$s). $\Delta\%$ là chênh lệch số lớp của ALNS so với LS
(giá trị \emph{âm} nghĩa là LS tốt hơn, ví dụ \texttt{hustack02}).}
\label{tab:tradeoff}
\begin{tabular}{ll r rr rr r}
\toprule
Instance & Nhóm & $N$ & LS (ms) & ALNS (s) & LS avg & ALNS avg & $\Delta\%$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}
\end{table}
"""
    _w("tradeoff_table.tex", tex)


def main():
    cpsat_scaling()
    cpsat_real()
    bench_env()
    bench_small()
    _group_table("medium",
                 r"Nhóm trung bình ($N\approx 100$--$200$): trộn instance dư tài "
                 r"nguyên và nghẽn phòng ($M$ nhỏ). Cùng ngân sách $30$s.",
                 "tab:bench-medium", "bench_medium_table.tex")
    _group_table("large",
                 r"Nhóm lớn ($N\ge 500$). Cùng ngân sách $30$s; LS/ALNS trung bình "
                 r"các seed.",
                 "tab:bench-large", "bench_large_table.tex")
    tradeoff()


if __name__ == "__main__":
    main()
