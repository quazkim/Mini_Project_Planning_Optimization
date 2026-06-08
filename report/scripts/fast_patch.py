import json, time, random, statistics as st
import common
from solver.algorithms.greedy import solve_with_greedy
from solver.algorithms.local_search import optimize_with_local_search
from solver.algorithms.cp_sat import solve_with_cp_sat
from ortools.sat.python import cp_model

TIME_LIMIT = 30.0
SEEDS = [1, 7, 13, 21, 42]
REPS = {"small": 5, "medium": 5, "large": 3}

d = json.load(open("../data/benchmark.json"))

for size in d:
    for r in d[size]:
        name = r["instance"]
        print(f"Patching {name}...")
        N, M, classes, rooms = common.load_instance(name)
        
        # ls_fast
        lsf_q, lsf_t = [], []
        for k in range(REPS[size]):
            random.seed(SEEDS[k])
            N_, M_, c_, r_ = common.load_instance(name)
            gg = solve_with_greedy(N_, M_, c_, r_)
            t0 = time.time()
            res = optimize_with_local_search(N_, M_, c_, r_, gg, max_iters=2000)
            lsf_t.append(time.time() - t0)
            lsf_q.append(len(res))
        r["ls_fast"] = {
            "min": min(lsf_q), "max": max(lsf_q),
            "avg": st.mean(lsf_q), "std": st.pstdev(lsf_q) if len(lsf_q)>1 else 0.0,
            "time": st.mean(lsf_t)
        }
        
        # cpsat
        t0 = time.time()
        status, res = solve_with_cp_sat(N, M, classes, rooms, time_limit=TIME_LIMIT)
        r["cpsat"] = {
            "Q": len(res), "time": time.time() - t0,
            "optimal": status == cp_model.OPTIMAL,
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else
                      ("FEASIBLE" if status == cp_model.FEASIBLE else "NONE")
        }
        print(f"   ls_fast: {r['ls_fast']['avg']}, cpsat: {r['cpsat']['Q']} ({r['cpsat']['status']})")

with open("../data/benchmark.json", "w") as f:
    json.dump(d, f, indent=2)
print("Patched benchmark.json successfully.")
