# Kế hoạch 1 tuần (17/05/2026 → 23/05/2026)

## Mục tiêu chung
- Hoàn thiện pipeline giải bài toán Timetabling theo đặc tả I/O.
- Có 3 tầng giải: **CP-SAT (exact)**, **Greedy (baseline)**, **Metaheuristic: Tabu Search (improve)**.
- Ưu tiên mục tiêu chính: **tối đa số lớp xếp được (Q)**, tuân thủ ràng buộc:
  - Không trùng phòng.
  - Không trùng giáo viên.
  - Không học xuyên ngày (1 ngày 12 tiết, tổng 60 tiết).
  - Phòng đủ sức chứa (capacity ≥ s).

## Quy ước làm việc
- Repo/file chính: `main.py` (monolithic).
- Nhánh/commit: nếu có git thì mỗi người 1 nhánh; nếu không có git thì dùng quy ước “copy/paste patch” + review chéo.
- Mỗi ngày kết thúc: chốt **deliverables** + danh sách issue/bug.
- Thời gian sync: 15 phút đầu ngày + 15 phút cuối ngày.

## Định nghĩa nhanh (để thống nhất khi code)
- Theo đề bài: slot được đánh số **1..60** (5 ngày × 12 tiết).
- Khi code nội bộ có thể dùng 0-based **0..59** để tiện xử lý, nhưng **output phải in 1-based (u = start + 1)**.
- Lớp i có thời lượng t(i) (1..4) chiếm các slot liên tiếp.
- Không xuyên ngày (với start nội bộ 0-based): `start % 12 <= 12 - t(i)`.

---

# Ngày 1 — 17/05/2026 (CODE 1/5) — Khởi tạo & chốt ràng buộc

## Huy Vũ (CP-SAT)
- Xác nhận mô hình CP-SAT:
  - Biến `start_i`, `room_i`, `is_assigned_i`.
  - `OptionalIntervalVar` cho **(room, class)** và **(teacher, class)**.
  - `NoOverlap` theo từng phòng, từng giáo viên.
  - Ràng buộc không xuyên ngày.
  - Ràng buộc sức chứa theo room được chọn.
- Chốt objective: maximize `sum(is_assigned_i)`.

**Deliverable**
- Draft công thức ràng buộc + danh sách biến cần có.

## Nguyễn Văn Phú Thái (Greedy)
- Xác định heuristic thứ tự xếp lớp:
  - Primary: `s` giảm dần.
  - Tie-break: `t` giảm dần, hoặc `g` để ổn định.
- Thiết kế cấu trúc dữ liệu bận:
  - `room_busy[room][slot]` boolean.
  - `teacher_busy[teacher][slot]` boolean (teacher id 1..100).

**Deliverable**
- Spec chi tiết cách check feasibility cho (room, start).

## Xuân Hoàng (Tabu Search)
- Thiết kế hàm đánh giá (score) để Tabu tối ưu:
  - Mục tiêu 1: maximize số lớp assigned.
  - Mục tiêu 2: minimize “xung đột” (nếu cho phép tạm thời) hoặc minimize lãng phí sức chứa.
- Chốt neighborhood (các move):
  - Move 1: đổi slot của 1 lớp (giữ room).
  - Move 2: đổi room của 1 lớp (giữ slot).
  - Move 3: swap 2 lớp cùng thời lượng trong 2 room/slot.
- Chốt cấu trúc tabu list:
  - Lưu (class_id, new_room, new_start) với tenure k.

**Deliverable**
- Mô tả neighborhood + tabu list + aspiration criterion.

## Việc chung (tất cả)
- Chốt bộ test tay nhỏ (N≈10) để debug: case trùng giáo viên, case phòng nhỏ, case sát biên ngày.

---

# Ngày 2 — 18/05/2026 (CODE 2/5) — Hoàn thiện Greedy baseline

## Nguyễn Văn Phú Thái (Greedy)
- Implement `solve_with_greedy()` đầy đủ:
  - Duyệt lớp theo thứ tự heuristic.
  - Duyệt room theo capacity tăng dần (best-fit) hoặc theo id.
  - Duyệt start slot từ 0..59, loại start xuyên ngày.
  - Check room/teacher availability trong t(i) slot.
  - Cập nhật `assigned_slot`, `assigned_room`, `is_assigned`.
- Xuất danh sách assigned đúng format.

**Deliverable**
- Greedy chạy được end-to-end trên test tay.

## Huy Vũ (CP-SAT)
- Bắt đầu code khung CP-SAT:
  - Tạo vars + intervals.
  - NoOverlap theo phòng.
  - NoOverlap theo giáo viên.

**Deliverable**
- CP-SAT chạy được (dù chưa tối ưu/đủ ràng buộc).

## Xuân Hoàng (Tabu Search)
- Chuẩn bị helper cho metaheuristic:
  - Hàm build “state” từ assigned_list.
  - Hàm kiểm tra feasibility nhanh.
  - Hàm tính score.

**Deliverable**
- Bộ hàm state/score/feasibility tối thiểu.

---

# Ngày 3 — 19/05/2026 (CODE 3/5) — Hoàn thiện CP-SAT + ràng buộc capacity

## Huy Vũ (CP-SAT)
- Hoàn thiện ràng buộc capacity:
  - Nếu chọn room v thì `capacity[v] >= s(i)`.
  - Triển khai bằng: chỉ cho phép domain room hợp lệ, hoặc dùng bool implies.
- Ràng buộc không xuyên ngày:
  - Cho phép start thuộc tập hợp hợp lệ (lọc domain) hoặc constraint theo `start % 12`.
- Objective maximize số lớp assigned.
- Thiết lập time limit 300s.

**Deliverable**
- CP-SAT chạy ổn N<=100, trả nghiệm hợp lệ.

## Nguyễn Văn Phú Thái (Greedy)
- Tối ưu tốc độ greedy:
  - Tiền xử lý danh sách room hợp lệ theo s(i).
  - Dừng sớm nếu không thể tìm slot.
  - Cân nhắc thứ tự duyệt room (best-fit để giảm lãng phí).

**Deliverable**
- Greedy chạy được N≈1000 trong thời gian ngắn.

## Xuân Hoàng (Tabu Search)
- Code khung Tabu chạy được (iteration loop):
  - Tạo candidate moves.
  - Chọn best non-tabu (hoặc thỏa aspiration).
  - Update tabu list.
  - Track best solution.

**Deliverable**
- Tabu loop chạy được trên nghiệm greedy nhỏ.

---

# Ngày 4 — 20/05/2026 (CODE 4/5) — Tabu Search “đúng nghĩa” + tích hợp pipeline

## Xuân Hoàng (Tabu Search)
- Hoàn thiện Tabu Search để **tăng Q** thực tế:
  - Cho phép move “unassign + reinsert” để thoát kẹt.
  - Candidate selection theo chiến lược: sample ngẫu nhiên K move/lần (giảm O(N*60*M)).
  - Tenure động (ví dụ 7..15) + aspiration (nếu cải thiện best).

**Deliverable**
- `optimize_with_metaheuristic()` trả về nghiệm không tệ hơn greedy trên test tay.

## Nguyễn Văn Phú Thái (Greedy)
- Bổ sung greedy “repair” nhẹ:
  - Sau khi xếp xong, thử chèn các lớp unassigned theo thứ tự t nhỏ trước.

**Deliverable**
- Greedy+repair tăng Q trên một vài test.

## Huy Vũ (CP-SAT)
- Tích hợp chọn solver theo `MODE_CHOOSE` + fallback không có ortools.
- Tối ưu mô hình CP-SAT để giảm số biến:
  - Chỉ tạo intervals cho các room đủ capacity.

**Deliverable**
- CP-SAT ổn định, không crash khi dữ liệu lớn (dù có thể chậm).

---

# Ngày 5 — 21/05/2026 (CODE 5/5) — Chốt chất lượng, log, và chuẩn bị chạy HUSTack

## Huy Vũ (CP-SAT)
- Kiểm tra tính hợp lệ nghiệm CP-SAT bằng validator nội bộ (chỉ chạy khi debug).
- Xử lý corner cases:
  - N=0? (không có theo đề nhưng input có thể rỗng) → an toàn.
  - Không có room đủ capacity cho lớp.

**Deliverable**
- CP-SAT pass validator.

## Nguyễn Văn Phú Thái (Greedy)
- Chốt cấu trúc dữ liệu bận và tốc độ.
- Kiểm tra format output đúng (Q + Q dòng i u v).

**Deliverable**
- Greedy pass validator.

## Xuân Hoàng (Tabu Search)
- Thêm dừng theo thời gian (time budget) và số vòng lặp.
- Chốt tham số mặc định:
  - `time_budget_seconds` (ví dụ 2..10s cho N lớn).
  - `tabu_tenure`.
  - `candidate_sample_size`.

**Deliverable**
- Tabu có time budget, không chạy quá lâu.

## Việc chung
- Viết README ngắn (nếu được phép) về cách chạy: `python main.py < input.txt`.
- Chốt default `MODE_CHOOSE = "AUTO"` khi nộp.

---

# Ngày 6 — 22/05/2026 (CHẠY 1/2) — Benchmark, tuning, và so sánh

## Chạy & đo
- Chạy batch test (nếu có) cho 3 chế độ:
  - `CP_ONLY` (N nhỏ).
  - `GREEDY_ONLY`.
  - `AUTO`.
- Ghi lại:
  - Q đạt được.
  - Thời gian chạy.
  - Tỉ lệ lớp không xếp được theo nguyên nhân (room nhỏ/giáo viên bận/slot).

## Tuning
- Tuning tham số greedy (thứ tự room, tie-break).
- Tuning tham số tabu (tenure, sample size, time budget).

**Deliverable cuối ngày**
- Bảng so sánh Q/thời gian cho vài input đại diện.

---

# Ngày 7 — 23/05/2026 (CHẠY 2/2) — Final run, đóng gói, và checklist nộp

## Checklist kỹ thuật
- Không in log ra stdout trong chế độ nộp (chỉ in output).
  - Nếu cần log, chuyển sang stderr hoặc bật/tắt bằng flag.
- Đảm bảo không phụ thuộc package ngoài trừ `ortools` (và có fallback).
- Đảm bảo output đúng format và chỉ gồm số.

## Final run
- Chạy lại `AUTO` trên input lớn.
- Nếu có ortools: xác nhận `AUTO` dùng CP-SAT cho N<=100.
- Nếu không có ortools: xác nhận fallback sang greedy+tabu.

**Deliverable cuối ngày**
- File `main.py` ổn định để nộp + note tham số cuối.
