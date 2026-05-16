# Mini Project – Planning Optimization (Timetabling)

Giải bài toán **xếp thời khóa biểu (Timetabling)**: gán **phòng** và **tiết bắt đầu** cho các lớp sao cho:
- Không trùng lịch **giáo viên**.
- Không trùng lịch **phòng**.
- **Sức chứa phòng** đủ cho số sinh viên của lớp.
- Lớp học các tiết **liên tiếp** và **không học xuyên ngày** (mỗi ngày 12 tiết, 5 ngày/tuần → 60 tiết).
- **Tối đa hóa số lớp xếp được** (maximize Q).

## Mô tả bài toán
- Có N lớp (1..N), mỗi lớp i có:
  - `t(i)`: số tiết (1..4)
  - `g(i)`: mã giáo viên (1..100)
  - `s(i)`: số sinh viên (1..200)
- Có M phòng (1..M), mỗi phòng v có:
  - `c(v)`: sức chứa (1..300)
- 1 tuần có 5 ngày, mỗi ngày 12 tiết → các tiết đánh số **1..60**.

## Input / Output
### Input
- Dòng 1: `N M`
- N dòng tiếp theo: `t(i) g(i) s(i)`
- Dòng cuối: `c(1) c(2) ... c(M)`

### Output
- Dòng 1: `Q` (số lớp xếp được)
- Q dòng tiếp theo: `i u v` nghĩa là lớp i học từ tiết u tại phòng v
  - `u` là **tiết bắt đầu (1..60)**

## Thuật toán
Dự án cung cấp 2 lớp giải:

1) **CP-SAT (Exact)** – dùng OR-Tools
- Dùng `OptionalIntervalVar` + `AddNoOverlap` để mô hình hóa ràng buộc trùng phòng và trùng giáo viên.
- Mục tiêu: maximize số lớp được gán.
- Time limit: 300s.

2) **Greedy (Baseline)**
- Sắp xếp lớp theo số sinh viên giảm dần (`s` giảm dần).
- Thử gán cặp (phòng, slot bắt đầu) hợp lệ đầu tiên.

3) **Metaheuristic (Khung)**
- Có khung `optimize_with_metaheuristic()` để nhóm phát triển tiếp (Tabu Search / Simulated Annealing).

## Chạy chương trình
Yêu cầu: Python 3.9+.

Chạy với stdin/stdout theo đúng format đề:

```bash
python3 main.py < input.txt > output.txt
```

### Chế độ chạy (đổi trong `main.py`)
- `MODE_CHOOSE = "AUTO"`: N nhỏ (<=100) ưu tiên CP-SAT; nếu thiếu OR-Tools hoặc N lớn thì dùng Greedy (+ meta khung).
- `MODE_CHOOSE = "CP_ONLY"`: chỉ chạy CP-SAT.
- `MODE_CHOOSE = "GREEDY_ONLY"`: chỉ chạy Greedy.

## Phụ thuộc (tùy chọn)
CP-SAT cần OR-Tools. Nếu môi trường không có OR-Tools, chương trình tự động fallback sang Greedy.

Cài OR-Tools (tùy chọn):
```bash
pip install ortools
```
