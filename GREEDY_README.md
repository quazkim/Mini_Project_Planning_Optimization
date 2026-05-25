# Greedy Day-by-Day — Tài liệu giải thuật

## Mục lục
1. [Tổng quan bài toán](#1-tổng-quan-bài-toán)
2. [Vì sao chọn Greedy?](#2-vì-sao-chọn-greedy)
3. [Ý tưởng Day-by-Day](#3-ý-tưởng-day-by-day)
4. [Mô tả giải thuật chi tiết](#4-mô-tả-giải-thuật-chi-tiết)
5. [Benchmark trên ITC-2007 CB-CTT](#5-benchmark-trên-itc-2007-cb-ctt)
6. [Phân tích tham số (ablation)](#6-phân-tích-tham-số-ablation)
7. [Kết luận tham số chọn](#7-kết-luận-tham-số-chọn)
8. [Cách chạy](#8-cách-chạy)

---

## 1. Tổng quan bài toán

Cho:
- **N lớp học**, mỗi lớp `i` có: `t(i)` tiết liên tiếp (1–4), `g(i)` mã giáo viên (1–100), `s(i)` số sinh viên (1–200).
- **M phòng học**, mỗi phòng `v` có sức chứa `c(v)`.
- **60 tiết**: 5 ngày × 12 tiết/ngày.

Mục tiêu: gán phòng + tiết bắt đầu cho càng nhiều lớp càng tốt (**maximize Q**), thỏa:
- Không trùng phòng.
- Không trùng giáo viên.
- Sức chứa phòng ≥ số sinh viên.
- Lớp học không kéo sang ngày hôm sau.

---

## 2. Vì sao chọn Greedy?

| Tiêu chí | CP-SAT (exact) | **Greedy** | Tabu Search |
|---|---|---|---|
| Độ chính xác | Tối ưu toàn cục | ~97–100% (ITC-2007) | Cải thiện từ Greedy |
| Thời gian (N=434) | Có thể > 300s | **< 3ms** | Vài giây |
| Cài đặt | Phức tạp (ortools) | Đơn giản, không phụ thuộc | Trung bình |
| Fallback khi không có ortools | Không | **Có — bắt buộc** | Cần greedy làm khởi đầu |

**Lý do cốt lõi:** Greedy là **baseline fast solver** và **khởi điểm bắt buộc** cho Tabu Search. Kết quả benchmark ITC-2007 (23 instances thực tế, tổng 5974 lectures): **99.9% lectures placed trong < 3ms/instance**.

---

## 3. Ý tưởng Day-by-Day

### Greedy toàn cục (Global)
Với mỗi lớp, tìm cặp (phòng, tiết) hợp lệ đầu tiên trong toàn bộ 60 tiết.

### Greedy Day-by-Day (Daily)
Xử lý **từng ngày theo thứ tự** — lấp đầy ngày 1 rồi mới sang ngày 2:

```
Cho mỗi ngày d ∈ {1, 2, 3, 4, 5}:
    Với mỗi lớp chưa xếp (theo thứ tự ưu tiên):
        Thử xếp lớp vào ngày d
        Nếu được → đánh dấu đã xếp
Sau 5 ngày → Repair pass
```

**Khi nào Daily tốt hơn Global?**
- Khi các lớp có `t > 1` (2–4 tiết liên tiếp): Daily ngăn slot fragmentation trong ngày — tránh tình trạng một ngày chỉ còn khe hở nhỏ lẻ không đủ cho lớp dài.
- Khi slot capacity per day là bottleneck (ít phòng, nhiều lớp dài).

**Khi nào Global tốt hơn Daily?**
- Khi tất cả lớp có `t = 1` (một tiết đơn): không có vấn đề fragmentation. Daily thậm chí có thể kém hơn vì ép buộc xếp hết lớp vào một ngày trước khi sang ngày tiếp theo.
- Bằng chứng từ ITC-2007 (tất cả lectures t=1): Global = Daily trên 21/23 instances, và Daily **tệ hơn** trên 2 instances lớn (comp07: −2, comp21: −8).

> **Kết luận từ data:** `global` là lựa chọn an toàn hơn cho bài toán thuần t=1. Với bài toán của nhóm có t=1..4, `daily` có thể mang lại lợi thế ở một số test case bottleneck.

### Repair Pass
Sau main pass, thử lại các lớp chưa xếp trên **toàn tuần**, ưu tiên lớp ngắn (t=1) vì chúng cần ít slot trống nhất:
```python
unassigned.sort(key=lambda c: (c.t, -c.s))  # ngắn trước, đông SV trước cùng nhóm
```

---

## 4. Mô tả giải thuật chi tiết

```
Input: N classes, M rooms, slots_per_day, total_days

Bước 0 — Tiền xử lý
  Với mỗi lớp c:
    feasible_rooms[c] = {r | capacity[r] >= s(c)}  ← lọc 1 lần
    Sắp xếp feasible_rooms[c] theo room_order strategy

Bước 1 — Sắp xếp lớp theo sort_key

Bước 2 — Main pass
  room_busy[r][slot]    = False  (M × total_slots boolean)
  teacher_busy[g][slot] = False  (n_teachers × total_slots boolean)
  
  if day_processing == "global":
    for c in sorted_class_list:
      starts = valid_starts_anywhere(c.t)   ← tất cả slot hợp lệ
      try_place(c, feasible_rooms[c], starts)
  
  if day_processing == "daily":
    for day in [0..total_days-1]:
      for c in sorted_class_list (chưa xếp):
        starts = valid_starts_in_day(c.t, day)  ← chỉ 1 ngày
        try_place(c, feasible_rooms[c], starts)

Bước 3 — Repair pass (nếu use_repair=True)
  unassigned.sort(t asc, s desc)
  for c in unassigned:
    try_place(c, feasible_rooms[c], all_valid_starts)

Output: danh sách (class_id, slot_start_1based, room_id)
```

**Độ phức tạp:**
- Tiền xử lý: O(N × M)
- Main pass: O(N × M × slots_per_day) per day → O(N × M × total_slots) overall
- Với N=434, M=20, total_slots=25: < 3ms trên Python thuần

---

## 5. Benchmark trên ITC-2007 CB-CTT

**Dataset:** 23 instances từ ITC-2007 International Timetabling Competition  
**Quy mô:** 7–434 lectures, 2–20 phòng, 3–6 ngày × 3–9 tiết/ngày  
**Tổng runs:** 2208 (96 combos × 23 instances)

### Kết quả với bộ tham số tốt nhất

| Instance | N lectures | M rooms | Slots | Q | Fill% | Thời gian |
|---|---|---|---|---|---|---|
| `comp01` (Fis0506-1) | 160 | 6 | 5×6 | **156** | **97.5%** | 0.46ms |
| `comp07` (Ing0607-2) | **434** | 20 | 5×5 | 434 | 100% | 2.5ms |
| `comp11` (Fis0506-2) | 162 | **5** | 5×9 | 162 | 100% | 0.38ms |
| `comp20` (Ing0506-2) | 390 | 19 | 5×5 | 390 | 100% | 1.7ms |
| **TỔNG (23 instances)** | **5974** | — | — | **5970** | **99.93%** | — |

**comp01 tại sao 97.5%?**  
Đây là instance khó nhất: 160 lectures / 6 rooms / 30 slots = chỉ **20 slot dư** (thừa 12.5%). Mỗi slot của mỗi teacher bị block chỉ cần 1 conflict là không dùng được. 4 lectures không place được là do teacher bottleneck — không còn slot nào mà vừa phòng đủ lớn vừa teacher rảnh.

### Daily vs Global trên ITC-2007

| Instance | N | Daily Q | Global Q | Δ |
|---|---|---|---|---|
| `comp07` | 434 | 432 | **434** | −2 |
| `comp21` | 327 | 319 | **327** | −8 |
| 21 instances còn lại | — | = Global | = Global | 0 |

Lý do Global thắng trên ITC-2007: tất cả lectures có t=1 (đơn tiết). Daily gây overhead bằng cách commit vào từng ngày quá sớm, bỏ lỡ cơ hội đặt lecture ở ngày sau khi ngày trước "đầy" về mặt teacher conflict.

---

## 6. Phân tích tham số (ablation)

Kết quả ablation từ 2208 runs trên ITC-2007:

### `sort_key` — Thứ tự ưu tiên xếp lớp

| Chiến lược | Mô tả | Total Q | Avg Fill% |
|---|---|---|---|
| `s_desc` ✓ | Ưu tiên lớp đông SV nhất | 143160 | **99.8%** |
| `s_t_combo` | Ưu tiên (s desc, t desc) | 143160 | 99.8% |
| `st_desc` | Ưu tiên s×t (total demand) | 143160 | 99.8% |
| `t_desc` | Ưu tiên lớp dài nhất | 143160 | 99.8% |

**Tất cả 4 chiến lược đều tie** trên ITC-2007 vì t=1 cho tất cả lectures — sort_key chỉ ảnh hưởng khi t thay đổi. Chọn `s_desc` vì đây là heuristic có lý thuyết rõ ràng nhất: lớp đông sinh viên cần phòng lớn — tài nguyên khan hiếm nhất.

> **Cho bài toán gốc (t=1..4):** `s_t_combo` tốt hơn `s_desc` một chút (từ synthetic benchmark: 15300 vs 15288 total Q). Khi t thay đổi, lớp có s=50, t=4 khó place hơn lớp s=50, t=1 vì cần 4 slot liên tiếp.

### `room_order` — Chiến lược chọn phòng

| Chiến lược | Mô tả | Total Q | Avg Fill% |
|---|---|---|---|
| `first_fit` ✓ | Phòng id nhỏ nhất (deterministic) | 190880 | **99.8%** |
| `best_fit` | Phòng nhỏ nhất vừa đủ | 190880 | 99.8% |
| `worst_fit` | Phòng lớn nhất | 190880 | 99.8% |

**Tie trên ITC-2007** vì capacity bottleneck yếu (nhiều phòng, nhiều room đủ lớn). Chọn `first_fit` vì nhanh nhất (không cần sort).

> **Cho bài toán gốc khi room bottleneck:** `best_fit` tốt hơn (synthetic benchmark: 20188 vs 20048 total Q). Best-fit "tiết kiệm" phòng lớn cho lớp thực sự cần — cổ điển bin-packing heuristic.

### `slot_order` — Hướng quét slot

| Chiến lược | Total Q | Avg Fill% |
|---|---|---|
| `forward` ✓ | 286320 | 99.8% |
| `backward` | 286320 | 99.8% |

**Hoàn toàn tie** trên mọi bộ test. Chọn `forward` vì trực quan (xếp từ tiết 1 của ngày).

### `use_repair` — Repair pass

| Tùy chọn | Total Q | Avg Fill% |
|---|---|---|
| `True` ✓ | 286320 | 99.8% |
| `False` | 286320 | 99.8% |

**Tie** trên ITC-2007 (vì t=1 ít sót lớp). Luôn chọn `True` — chi phí gần 0, giúp edge case bài toán gốc khi t=2..4 tạo nhiều lớp chưa place được sau main pass.

### `day_processing` — Daily vs Global

| Chiến lược | Total Q | Avg Fill% |
|---|---|---|
| `global` ✓ | **286560** | **99.9%** |
| `daily` | 286080 | 99.8% |

**Global tốt hơn (+480 Q tổng)** trên ITC-2007 vì t=1. Tuy nhiên với bài toán gốc (t=1..4), synthetic benchmark cho thấy daily tốt hơn +736 Q tổng trong scenario có nhiều lớp dài.

---

## 7. Kết luận tham số chọn

```python
BEST_PARAMS = {
    "sort_key":       "s_desc",    # ưu tiên lớp đông SV — phòng lớn là bottleneck chính
    "room_order":     "first_fit", # deterministic, đủ tốt; best_fit nếu room bottleneck
    "slot_order":     "forward",   # tie với backward — chọn trực quan
    "use_repair":     True,        # miễn phí, giúp edge case
    "day_processing": "global",    # tốt hơn trên ITC-2007; daily có thể tốt hơn nếu t>1
}
```

### Hướng dẫn chọn tham số theo context

| Bài toán | sort_key | room_order | day_processing | Lý do |
|---|---|---|---|---|
| t=1 (ITC-2007 style) | `s_desc` | `first_fit` | `global` | ITC benchmark |
| t=1..4, room tight | `s_t_combo` | `best_fit` | `daily` | synthetic benchmark |
| t=1..4, teacher tight | `s_desc` | `first_fit` | `global` | teacher bottleneck |
| Mixed (không biết trước) | `s_desc` | `first_fit` | `global` | **default an toàn** |

### Performance summary

| Nguồn benchmark | Instances | Total Q | Fill rate | Thời gian max |
|---|---|---|---|---|
| ITC-2007 CB-CTT (23 instances) | 5974 lectures | **5970** | **99.93%** | 2.5ms |
| Synthetic (5 scenarios, N≤300) | 650 classes | 638 | 98.2% | 1.4ms |

---

## 8. Cách chạy

```bash
# Giải từ stdin (dùng BEST_PARAMS):
python greedy_daily.py < input.txt

# Benchmark trên ITC-2007 (cần datasets/ folder):
python ctt_benchmark.py

# Chạy synthetic tuning:
python greedy_daily.py --tune
```

### Format input/output (giống main.py)

**Input:**
```
N M
t1 g1 s1
t2 g2 s2
...
c1 c2 ... cM
```

**Output:**
```
Q
class_id slot_start(1-based) room_id
...
```

---

*Tham số chọn từ kết quả thực nghiệm — xem chi tiết trong `param_tuning_log.md` (2208 runs, sinh tự động bởi `ctt_benchmark.py`).*
