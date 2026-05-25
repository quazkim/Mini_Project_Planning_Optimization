# Greedy Parameter Tuning Log — ITC-2007 CB-CTT Benchmark

**Generated:** 2026-05-24 08:59:49  
**Dataset:** ITC-2007 Curriculum-Based Course Timetabling  
**Instances:** 23 files (`toy.ctt`, `toytoy.ctt`, `comp01`–`comp21`)  
**Parameter combos:** 96  
**Total runs:** 2208  

---
## Bộ tham số tốt nhất (từ ITC-2007 benchmark)

| Tham số | Giá trị | Lý do |
|---|---|---|
| `sort_key` | `s_desc` | Ưu tiên lớp đông SV — phòng lớn là bottleneck |
| `room_order` | `first_fit` | Phòng id nhỏ nhất |
| `slot_order` | `forward` | Quét slot từ đầu ngày |
| `use_repair` | `True` | Repair pass — thêm cơ hội cho lớp sót |
| `day_processing` | `global` | Toàn bộ tuần — standard greedy |

---
## Kết quả tốt nhất trên từng instance

| Instance | N lec | M rooms | Slots | Best Q | Fill% | sort | room | slot | repair | day_proc | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `comp01.ctt` | 160 | 6 | 5×6 | 156 | 97.5% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 0.456 |
| `comp02.ctt` | 283 | 16 | 5×5 | 283 | 100.0% | `s_desc` | `best_fit` | `forward` | `True` | `global` | 0.938 |
| `comp03.ctt` | 251 | 16 | 5×5 | 251 | 100.0% | `s_t_combo` | `best_fit` | `forward` | `False` | `global` | 0.732 |
| `comp04.ctt` | 286 | 18 | 5×5 | 286 | 100.0% | `t_desc` | `best_fit` | `forward` | `True` | `global` | 1.035 |
| `comp05.ctt` | 152 | 9 | 6×6 | 152 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 0.327 |
| `comp06.ctt` | 361 | 18 | 5×5 | 361 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 1.301 |
| `comp07.ctt` | 434 | 20 | 5×5 | 434 | 100.0% | `s_desc` | `best_fit` | `forward` | `True` | `global` | 2.516 |
| `comp08.ctt` | 324 | 18 | 5×5 | 324 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 1.306 |
| `comp09.ctt` | 279 | 18 | 5×5 | 279 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 0.958 |
| `comp10.ctt` | 370 | 18 | 5×5 | 370 | 100.0% | `st_desc` | `best_fit` | `forward` | `False` | `global` | 1.778 |
| `comp11.ctt` | 162 | 5 | 5×9 | 162 | 100.0% | `t_desc` | `best_fit` | `forward` | `False` | `global` | 0.376 |
| `comp12.ctt` | 218 | 11 | 6×6 | 218 | 100.0% | `s_desc` | `best_fit` | `forward` | `True` | `global` | 0.771 |
| `comp13.ctt` | 308 | 19 | 5×5 | 308 | 100.0% | `st_desc` | `best_fit` | `forward` | `False` | `global` | 1.179 |
| `comp14.ctt` | 275 | 17 | 5×5 | 275 | 100.0% | `t_desc` | `best_fit` | `forward` | `False` | `global` | 1.045 |
| `comp15.ctt` | 251 | 16 | 5×5 | 251 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 0.722 |
| `comp16.ctt` | 366 | 20 | 5×5 | 366 | 100.0% | `s_t_combo` | `best_fit` | `forward` | `False` | `global` | 1.699 |
| `comp17.ctt` | 339 | 17 | 5×5 | 339 | 100.0% | `s_t_combo` | `best_fit` | `forward` | `False` | `global` | 1.353 |
| `comp18.ctt` | 138 | 9 | 6×6 | 138 | 100.0% | `s_desc` | `best_fit` | `forward` | `False` | `global` | 0.333 |
| `comp19.ctt` | 277 | 16 | 5×5 | 277 | 100.0% | `s_t_combo` | `best_fit` | `forward` | `True` | `global` | 1.004 |
| `comp20.ctt` | 390 | 19 | 5×5 | 390 | 100.0% | `st_desc` | `best_fit` | `forward` | `False` | `global` | 1.655 |
| `comp21.ctt` | 327 | 18 | 5×5 | 327 | 100.0% | `s_t_combo` | `best_fit` | `forward` | `False` | `global` | 1.273 |
| `toy.ctt` | 16 | 2 | 5×4 | 16 | 100.0% | `t_desc` | `best_fit` | `forward` | `False` | `daily` | 0.019 |
| `toytoy.ctt` | 7 | 2 | 3×3 | 7 | 100.0% | `s_desc` | `best_fit` | `forward` | `True` | `daily` | 0.008 |
| **TOTAL** | **5974** | — | — | **5970** | **99.9%** | | | | | | |

---
## Top 20 Configurations (tổng Q trên toàn bộ ITC-2007)

| Rank | sort_key | room_order | slot_order | repair | day_proc | Total Q | Avg Fill% | Avg ms |
|---|---|---|---|---|---|---|---|---|
| 1 **◀ best** | `s_desc` | `first_fit` | `forward` | `True` | `global` | 5970 | 99.9% | 1.397 |
| 2 | `s_desc` | `first_fit` | `forward` | `False` | `global` | 5970 | 99.9% | 1.4 |
| 3 | `s_desc` | `first_fit` | `backward` | `True` | `global` | 5970 | 99.9% | 1.42 |
| 4 | `s_desc` | `first_fit` | `backward` | `False` | `global` | 5970 | 99.9% | 1.415 |
| 5 | `s_desc` | `best_fit` | `forward` | `True` | `global` | 5970 | 99.9% | 1.013 |
| 6 | `s_desc` | `best_fit` | `forward` | `False` | `global` | 5970 | 99.9% | 1.003 |
| 7 | `s_desc` | `best_fit` | `backward` | `True` | `global` | 5970 | 99.9% | 1.029 |
| 8 | `s_desc` | `best_fit` | `backward` | `False` | `global` | 5970 | 99.9% | 1.031 |
| 9 | `s_desc` | `worst_fit` | `forward` | `True` | `global` | 5970 | 99.9% | 2.419 |
| 10 | `s_desc` | `worst_fit` | `forward` | `False` | `global` | 5970 | 99.9% | 2.393 |
| 11 | `s_desc` | `worst_fit` | `backward` | `True` | `global` | 5970 | 99.9% | 2.426 |
| 12 | `s_desc` | `worst_fit` | `backward` | `False` | `global` | 5970 | 99.9% | 2.43 |
| 13 | `t_desc` | `first_fit` | `forward` | `True` | `global` | 5970 | 99.9% | 1.401 |
| 14 | `t_desc` | `first_fit` | `forward` | `False` | `global` | 5970 | 99.9% | 1.395 |
| 15 | `t_desc` | `first_fit` | `backward` | `True` | `global` | 5970 | 99.9% | 1.423 |
| 16 | `t_desc` | `first_fit` | `backward` | `False` | `global` | 5970 | 99.9% | 1.415 |
| 17 | `t_desc` | `best_fit` | `forward` | `True` | `global` | 5970 | 99.9% | 1.014 |
| 18 | `t_desc` | `best_fit` | `forward` | `False` | `global` | 5970 | 99.9% | 1.007 |
| 19 | `t_desc` | `best_fit` | `backward` | `True` | `global` | 5970 | 99.9% | 1.032 |
| 20 | `t_desc` | `best_fit` | `backward` | `False` | `global` | 5970 | 99.9% | 1.021 |

---
## Ablation — Ảnh hưởng từng tham số trên ITC-2007

> Mỗi hàng tổng hợp tất cả runs có giá trị tham số đó, bất kể các tham số khác.

### `sort_key` — Chiến lược sắp xếp lớp học

| sort_key | Total Q | Avg Fill% | Rank |
|---|---|---|---|
| `s_desc` **← chọn** | 143160 | 99.8% | #1 |
| `t_desc` | 143160 | 99.8% | #2 |
| `st_desc` | 143160 | 99.8% | #3 |
| `s_t_combo` | 143160 | 99.8% | #4 |

### `room_order` — Chiến lược chọn phòng

| room_order | Total Q | Avg Fill% | Rank |
|---|---|---|---|
| `first_fit` **← chọn** | 190880 | 99.8% | #1 |
| `best_fit` | 190880 | 99.8% | #2 |
| `worst_fit` | 190880 | 99.8% | #3 |

### `slot_order` — Hướng quét slot trong ngày

| slot_order | Total Q | Avg Fill% | Rank |
|---|---|---|---|
| `forward` **← chọn** | 286320 | 99.8% | #1 |
| `backward` | 286320 | 99.8% | #2 |

### `use_repair` — Có repair pass không

| use_repair | Total Q | Avg Fill% | Rank |
|---|---|---|---|
| `True` **← chọn** | 286320 | 99.8% | #1 |
| `False` | 286320 | 99.8% | #2 |

### `day_processing` — Xử lý theo ngày hay toàn cục

| day_processing | Total Q | Avg Fill% | Rank |
|---|---|---|---|
| `global` **← chọn** | 286560 | 99.9% | #1 |
| `daily` | 286080 | 99.8% | #2 |

---
## Day-by-Day vs Global — so sánh trực tiếp

| Instance | N | Daily Q | Global Q | Δ | Daily Fill% | Global Fill% |
|---|---|---|---|---|---|---|
| `comp01.ctt` | 160 | 156 | 156 | +0 | 97.5% | 97.5% |
| `comp02.ctt` | 283 | 283 | 283 | +0 | 100.0% | 100.0% |
| `comp03.ctt` | 251 | 251 | 251 | +0 | 100.0% | 100.0% |
| `comp04.ctt` | 286 | 286 | 286 | +0 | 100.0% | 100.0% |
| `comp05.ctt` | 152 | 152 | 152 | +0 | 100.0% | 100.0% |
| `comp06.ctt` | 361 | 361 | 361 | +0 | 100.0% | 100.0% |
| `comp07.ctt` | 434 | 432 | 434 | -2 | 99.5% | 100.0% |
| `comp08.ctt` | 324 | 324 | 324 | +0 | 100.0% | 100.0% |
| `comp09.ctt` | 279 | 279 | 279 | +0 | 100.0% | 100.0% |
| `comp10.ctt` | 370 | 370 | 370 | +0 | 100.0% | 100.0% |
| `comp11.ctt` | 162 | 162 | 162 | +0 | 100.0% | 100.0% |
| `comp12.ctt` | 218 | 218 | 218 | +0 | 100.0% | 100.0% |
| `comp13.ctt` | 308 | 308 | 308 | +0 | 100.0% | 100.0% |
| `comp14.ctt` | 275 | 275 | 275 | +0 | 100.0% | 100.0% |
| `comp15.ctt` | 251 | 251 | 251 | +0 | 100.0% | 100.0% |
| `comp16.ctt` | 366 | 366 | 366 | +0 | 100.0% | 100.0% |
| `comp17.ctt` | 339 | 339 | 339 | +0 | 100.0% | 100.0% |
| `comp18.ctt` | 138 | 138 | 138 | +0 | 100.0% | 100.0% |
| `comp19.ctt` | 277 | 277 | 277 | +0 | 100.0% | 100.0% |
| `comp20.ctt` | 390 | 390 | 390 | +0 | 100.0% | 100.0% |
| `comp21.ctt` | 327 | 319 | 327 | -8 | 97.6% | 100.0% |
| `toy.ctt` | 16 | 16 | 16 | +0 | 100.0% | 100.0% |
| `toytoy.ctt` | 7 | 7 | 7 | +0 | 100.0% | 100.0% |

---
*Tự động sinh bởi `python ctt_benchmark.py` trên ITC-2007 CB-CTT dataset*
