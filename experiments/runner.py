from __future__ import annotations
import time
from math import log2
from pathlib import Path
from typing import Iterable, List, Dict, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from algorithms.partial_enum import PartialEnum
from algorithms.genetic import GAParams, GeneticAlgorithm
from data_io.generator import random_instance


def _avg(v: List[float]) -> float:
    return sum(v) / len(v) if v else 0.0


def _gen_tunnels(n: int, seed: int = 0):
    return random_instance(n, 0, 0, 20, 20, (1, 3), (1, 3), seed=seed)


def _exp_k_sweep(
    k_list: Iterable[int],
    n_pop: int,
    repeats: int,
    base_ga: Dict,
    pe_timeout: float = 0.2,
) -> Tuple[List[List[float]], int]:
    rows = [["k", "g", "R_pe", "T_pe", "R_ga", "T_ga"]]
    best_row = None
    for k in k_list:
        g_val = int(k * n_pop * log2(n_pop))
        print(f"[E-1] k = {k}  (g = {g_val}) …", flush=True)
        z_ga, t_ga, z_pe, t_pe = [], [], [], []
        for rep in range(repeats):
            tuns = _gen_tunnels(n_pop, seed=rep)

            pe = PartialEnum(timeout_s=pe_timeout)
            _, _, z = pe.solve(tuns)
            z_pe.append(z)
            t_pe.append(pe.runtime_ms)

            P = GAParams(**{**base_ga, "g": g_val, "G": g_val, "seed": rep})
            t0 = time.perf_counter()
            best = GeneticAlgorithm(tuns, P).run()
            t_ga.append((time.perf_counter() - t0) * 1e3)
            z_ga.append(best.Z)

        row = [k, g_val, _avg(z_pe), _avg(t_pe), _avg(z_ga), _avg(t_ga)]
        rows.append(row)
        if best_row is None or row[4] > best_row[4] or (
            row[4] == best_row[4] and row[5] < best_row[5]
        ):
            best_row = row
    k_best = int(best_row[0])
    return rows, k_best


def _exp_m_sweep(
    m_list: Iterable[int],
    n_pop: int,
    g_fix: int,
    repeats: int,
    base_ga: Dict,
    pe_timeout: float = 0.2,
) -> List[List[float]]:
    rows = [["m", "R_pe", "T_pe", "R_ga", "T_ga"]]
    for m in m_list:
        print(f"[E-2] m = {m} …", flush=True)
        z_ga, t_ga, z_pe, t_pe = [], [], [], []
        for rep in range(repeats):
            tuns = _gen_tunnels(n_pop, seed=rep)

            pe = PartialEnum(timeout_s=pe_timeout)
            _, _, z = pe.solve(tuns)
            z_pe.append(z)
            t_pe.append(pe.runtime_ms)

            P = GAParams(
                **{**base_ga, "m": m, "g": g_fix, "G": g_fix, "seed": rep}
            )
            t0 = time.perf_counter()
            best = GeneticAlgorithm(tuns, P).run()
            t_ga.append((time.perf_counter() - t0) * 1e3)
            z_ga.append(best.Z)

        rows.append([m, _avg(z_pe), _avg(t_pe), _avg(z_ga), _avg(t_ga)])
    return rows


def _exp_n_sweep(
    n_range: Iterable[int],
    k_best: int,
    repeats: int,
    base_ga: Dict,
    pe_timeout: float = 0.2,
) -> List[List[float]]:
    rows = [["n", "R_pe", "T_pe", "R_ga", "T_ga", "ΔF"]]
    for n in n_range:
        g_n = int(k_best * n * log2(n))
        print(f"[E-3] n = {n}  (g = {g_n}) …", flush=True)
        z_ga, t_ga, z_pe, t_pe = [], [], [], []
        for rep in range(repeats):
            tuns = _gen_tunnels(n, seed=rep)

            pe = PartialEnum(timeout_s=pe_timeout)
            _, _, z = pe.solve(tuns)
            z_pe.append(z)
            t_pe.append(pe.runtime_ms)

            P = GAParams(
                **{**base_ga, "g": g_n, "G": g_n, "seed": rep}
            )
            t0 = time.perf_counter()
            best = GeneticAlgorithm(tuns, P).run()
            t_ga.append((time.perf_counter() - t0) * 1e3)
            z_ga.append(best.Z)

        ΔF = _avg(z_ga) - _avg(z_pe)
        rows.append([n, _avg(z_pe), _avg(t_pe), _avg(z_ga), _avg(t_ga), ΔF])
    return rows


def run_dim_experiment(cfg: Dict, repeats: int) -> Tuple[Path, Path, Path]:
    base_ga0 = dict(m=50, p=0.2, k_off=0.3, d_a=0.5, d_k=1.0)
    out = Path("results/experiments")
    out.mkdir(parents=True, exist_ok=True)
    ts = str(int(time.time()))

    n_pop = cfg.get("n_pop", 50)
    k_rows, k_best = _exp_k_sweep(cfg["k_list"], n_pop, repeats, base_ga0)
    csv_k = out / f"exp_stop_k_{ts}.csv"
    _save_csv(k_rows, csv_k)

    g_fix = int(k_best * n_pop * log2(n_pop))
    base_ga = {**base_ga0, "m": 50}

    m_rows = _exp_m_sweep(cfg["m_list"], n_pop, g_fix, repeats, base_ga)
    csv_m = out / f"exp_population_{ts}.csv"
    _save_csv(m_rows, csv_m)

    n_rows = _exp_n_sweep(cfg["n_range"], k_best, repeats, base_ga)
    csv_n = out / f"exp_dimension_{ts}.csv"
    _save_csv(n_rows, csv_n)

    figs = out / "figures"
    figs.mkdir(exist_ok=True)
    _plot(csv_n, "n", "T_ga", "T-vs-n", figs / f"T_vs_n_{ts}.png")
    _plot(csv_n, "n", "R_ga", "R-vs-n", figs / f"R_vs_n_{ts}.png")
    _plot(csv_n, "n", "ΔF", "DeltaF-vs-n", figs / f"Delta_vs_n_{ts}.png")

    return csv_n, csv_m, csv_k


def _save_csv(rows: List[List], path: Path):
    path.write_text("\n".join(";".join(map(str, r)) for r in rows), encoding="utf-8")


def _plot(csv_path: Path, x: str, y: str, title: str, out_png: Path):
    df = pd.read_csv(csv_path, delimiter=";")
    plt.figure()
    plt.plot(df[x], df[y], marker="o")
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()


def make_k_list() -> List[int]:
    return [10, 20, 50]