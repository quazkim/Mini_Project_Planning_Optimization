import random
import os

random.seed(42)

TESTS = [
    # (N,   M,  t_max, g_max, s_max, c_max, name)
    (5,    3,  2,     5,     30,    50,   "tiny"),
    (10,   5,  4,     5,     50,    80,   "small"),
    (20,   5,  4,     10,    80,    100,  "small_tight"),
    (50,   10, 4,     20,    100,   150,  "medium"),
    (100,  15, 4,     30,    120,   200,  "medium_large"),
    (200,  20, 4,     50,    150,   250,  "large"),
    (500,  30, 4,     80,    180,   280,  "stress"),
    (1000, 50, 4,     100,   200,   300,  "max_classes"),
    (200,  5,  4,     10,    200,   300,  "few_rooms"),     # ít phòng → bottleneck phòng
    (300,  100,4,     5,     200,   210,  "few_teachers"),  # ít giáo viên → bottleneck giáo viên
]

out_dir = "test_inputs"
os.makedirs(out_dir, exist_ok=True)

for idx, (N, M, t_max, g_max, s_max, c_max, name) in enumerate(TESTS, 1):
    lines = []
    lines.append(f"{N} {M}")
    for _ in range(N):
        t = random.randint(1, t_max)
        g = random.randint(1, g_max)
        s = random.randint(1, s_max)
        lines.append(f"{t} {g} {s}")
    capacities = [random.randint(1, c_max) for _ in range(M)]
    lines.append(" ".join(map(str, capacities)))

    fname = os.path.join(out_dir, f"test_{idx:02d}_{name}.txt")
    with open(fname, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[{idx:2d}] {fname}  (N={N}, M={M}, name={name})")

print(f"\nĐã tạo {len(TESTS)} test cases trong thư mục '{out_dir}/'")
