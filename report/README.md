# Báo cáo — Đánh giá CP-SAT & Metaheuristic cho bài toán xếp thời khóa biểu

Báo cáo LaTeX cùng toàn bộ script thực nghiệm sinh số liệu/đồ thị một cách tái lập.

## Cấu trúc
```
report/
├── main.tex              # File LaTeX chính (\input các phần trong sections/)
├── sections/             # 9 mục nội dung (s1..s9) + phụ lục
├── figures/              # Đồ thị PNG do scripts sinh ra
├── data/                 # JSON kết quả + các bảng .tex được sinh tự động
└── scripts/              # Script thực nghiệm (mọi số liệu đều từ đây)
    ├── common.py                     # nạp dataset, cấu hình matplotlib
    ├── instrumented_alns.py          # ALNS có ghi vết (tái dùng toán tử của solver)
    ├── exp_scenario1_operators.py    # Kịch bản 1: tiến hóa xác suất toán tử
    ├── exp_scenario2_lambda.py       # Kịch bản 2: hệ số học lambda
    ├── exp_scenario3_temperature.py  # Kịch bản 3: nhiệt độ T & alpha
    ├── exp_cpsat_scaling.py          # CP-SAT theo N (dữ liệu loose)
    ├── exp_cpsat_real.py             # CP-SAT trên dữ liệu thực nghẽn tài nguyên
    ├── exp_benchmark.py              # Benchmark Greedy/LS/ALNS/CP-SAT
    └── make_tables.py                # Sinh bảng .tex từ JSON
```

## Yêu cầu
```bash
pip install ortools matplotlib numpy
# Trình biên dịch LaTeX hỗ trợ Unicode: tectonic (khuyến nghị) hoặc xelatex
brew install tectonic
```

## Tái lập số liệu & biên dịch
```bash
cd report/scripts
python3 exp_scenario1_operators.py
python3 exp_scenario2_lambda.py
python3 exp_scenario3_temperature.py
python3 exp_cpsat_scaling.py
python3 exp_cpsat_real.py
python3 exp_benchmark.py
python3 make_tables.py

cd ..
tectonic main.tex      # -> main.pdf
```

Mọi đồ thị/bảng được sinh trực tiếp từ mã nguồn trong `solver/`, đảm bảo báo cáo
phản ánh đúng thuật toán đang chạy (không có tham số "hộp đen").
