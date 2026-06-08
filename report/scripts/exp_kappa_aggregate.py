#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tổng hợp kết quả khảo sát κ từ các shard và vẽ đồ thị định tuyến.

Đọc mọi kappa_shard_*.json trong kappa_out/, gộp lại, sắp theo κ, in bảng, ước
lượng ngưỡng κ* tách "ALNS thắng" khỏi "LS thắng", và vẽ kappa_routing.png.
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    rows = []
    for p in glob.glob("kappa_out/**/kappa_shard_*.json", recursive=True):
        rows += json.load(open(p))
    if not rows:
        raise SystemExit("Không tìm thấy kappa_shard_*.json trong kappa_out/")
    # loại trùng (nếu artifact gộp lặp), giữ theo tên instance.
    uniq = {r["instance"]: r for r in rows}
    rows = sorted(uniq.values(), key=lambda r: r["kappa"])

    with open("kappa_survey.json", "w") as f:
        json.dump(rows, f, indent=2)

    # --- in bảng ---
    print(f"{'instance':12s} {'N':>5} {'M':>4} {'U':>5} {'kappa':>7} "
          f"{'LS':>7} {'ALNS':>7} {'Δ':>6}  winner")
    for r in rows:
        print(f"{r['instance']:12s} {r['N']:5d} {r['M']:4d} {r['U']:5d} {r['kappa']:7d} "
              f"{r['ls']:7.1f} {r['alns']:7.1f} {r['delta']:+6.1f}  {r['winner']}")

    # --- ước lượng ngưỡng κ*: ranh giới giữa κ lớn nhất của ca ALNS-thắng và
    #     κ nhỏ nhất của ca LS-thắng (bỏ qua tie). ---
    alns_k = [r["kappa"] for r in rows if r["winner"] == "ALNS"]
    ls_k = [r["kappa"] for r in rows if r["winner"] == "LS"]
    kstar = None
    if alns_k and ls_k:
        lo, hi = max(alns_k), min(ls_k)
        kstar = (lo + hi) / 2 if lo < hi else None
        print(f"\nALNS thắng: kappa <= {max(alns_k)} | LS thắng: kappa >= {min(ls_k)}")
        print(f"Ngưỡng đề xuất kappa* ~ {kstar}" if kstar
              else "Hai miền chồng nhau -> không tách được bằng 1 ngưỡng.")

    # --- đồ thị: kappa vs (ALNS - LS) ---
    xs = np.array([max(r["kappa"], 1) for r in rows])
    ys = np.array([r["delta"] for r in rows])
    colors = ["#2ca02c" if r["winner"] == "ALNS"
              else ("#d62728" if r["winner"] == "LS" else "#888888") for r in rows]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.axhline(0, color="black", lw=0.8)
    if kstar:
        ax.axvline(kstar, color="#1f77b4", ls="--", lw=1.4,
                   label=f"$\\kappa^*\\approx{kstar:.0f}$")
    ax.scatter(xs, ys, c=colors, s=60, edgecolor="k", linewidth=0.4, zorder=3)
    for r in rows:
        ax.annotate(r["instance"], (max(r["kappa"], 1), r["delta"]),
                    fontsize=6, xytext=(2, 2), textcoords="offset points")
    ax.set_xscale("symlog")
    ax.set_xlabel(r"$\kappa = U \cdot M$ (log)")
    ax.set_ylabel("ALNS $-$ LS (số lớp, $>0$: ALNS thắng)")
    ax.set_title("Khảo sát định tuyến theo độ nghẽn: $\\kappa$ vs ưu thế ALNS/LS")
    ax.grid(True, alpha=0.3, ls="--")
    if kstar:
        ax.legend()
    fig.tight_layout()
    fig.savefig("kappa_routing.png", dpi=150)
    print("saved kappa_routing.png")


if __name__ == "__main__":
    main()
