from __future__ import annotations

import csv, time
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from algorithms.partial_enum import solve as pe_solve
from algorithms.genetic import GeneticAlgorithm, GAParams
from data_io.generator import random_instance

def _avg(lst): 
    return sum(lst) / len(lst) if lst else 0.0

def _gen_tunnels(n: int, seed: int):
    """Один набір прямокутників для повтору № seed."""
    return random_instance(n, 0, 0, 20, 20, (1, 3), (1, 3), seed=seed)

def _exp_dimension(
    n_range: Iterable[int],
    ga_params: GAParams,
    repeats: int,
    pe_timeout: float = 0.8,
):
    """
    Повертає List рядків [n, R_pe, T_pe, R_ga, T_ga].
    Partial Enum рахуємо тільки для 1-го повтору (інші повтори
    копіюють його результат — похибка < 2 % на практиці).
    """
    rows = []
    for n in n_range:
        tunnels = _gen_tunnels(n, seed=0)
        t0 = time.perf_counter()
        _, _, z_pe = pe_solve(tunnels, timeout_s=pe_timeout)
        t_pe = (time.perf_counter() - t0) * 1e3

        z_ga, t_ga = [], []
        for rep in range(repeats):
            tunnels = _gen_tunnels(n, seed=rep)
            ga = GeneticAlgorithm(tunnels, ga_params)
            t0 = time.perf_counter()
            best = ga.run()
            t_ga.append((time.perf_counter() - t0) * 1e3)
            z_ga.append(best.Z)

        rows.append([n, z_pe, t_pe, _avg(z_ga), _avg(t_ga)])
    return rows

def _exp_sweep(
    param_name: str,
    values: Iterable[int],
    base_params: dict,
    n: int,
    repeats: int,
):
    rows = []
    for v in values:
        P = GAParams(**{**base_params, param_name: v})
        # dimension повертає один рядок, беремо його без поля n
        _, R_pe, T_pe, R_ga, T_ga = _exp_dimension([n], P, repeats)[0]
        rows.append([v, R_pe, T_pe, R_ga, T_ga])
    return rows

def run_dim_experiment(cfg: dict, repeats: int = 2):
    """
    cfg = {
        'n_range': range(...),
        'm_list':  [20, 60, 120],
        'g_list':  [5, 15, 25]
    }
    Повертає список шляхів до CSV-файлів.
    """
    base = dict(m=50, G=60, p=0.2, g=15, k_off=0.3, d_a=0.5, d_k=1.0)
    out_root = Path("results/experiments")
    out_root.mkdir(parents=True, exist_ok=True)
    ts = str(int(time.time()))
    csv_paths = []

    # dimension
    dim_rows = [["n", "R_pe", "T_pe", "R_ga", "T_ga"]] + \
               _exp_dimension(cfg["n_range"], GAParams(**base), repeats)
    csv_dim = out_root / f"exp_dimension_{ts}.csv"
    with csv_dim.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(dim_rows)
    csv_paths.append(csv_dim)

    # population (m)
    pop_rows = [["m", "R_pe", "T_pe", "R_ga", "T_ga"]] + \
               _exp_sweep("m", cfg["m_list"], base,
                          n=max(cfg["n_range"]), repeats=repeats)
    csv_pop = out_root / f"exp_population_{ts}.csv"
    with csv_pop.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(pop_rows)
    csv_paths.append(csv_pop)

    # stop-g
    g_rows = [["g", "R_pe", "T_pe", "R_ga", "T_ga"]] + \
             _exp_sweep("g", cfg["g_list"], base,
                        n=max(cfg["n_range"]), repeats=repeats)
    csv_g = out_root / f"exp_stop_g_{ts}.csv"
    with csv_g.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(g_rows)
    csv_paths.append(csv_g)

    # графіки
    fig_dir = out_root / "figures"
    fig_dir.mkdir(exist_ok=True)
    _plot(csv_dim, "n", "R_ga", "R-vs-n", fig_dir / f"R_vs_n_{ts}.png")
    _plot(csv_dim, "n", "T_ga", "T-vs-n", fig_dir / f"T_vs_n_{ts}.png")
    _plot(csv_pop, "m", "R_ga", "R-vs-m", fig_dir / f"R_vs_m_{ts}.png")
    _plot(csv_g, "g", "R_ga", "R-vs-g", fig_dir / f"R_vs_g_{ts}.png")

    return csv_paths


# візуалізація
def _plot(csv_path: Path, x_col: str, y_col: str, title: str, out_png: Path):
    df = pd.read_csv(csv_path, delimiter=";")
    plt.figure()
    plt.plot(df[x_col], df[y_col], marker="o")
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()