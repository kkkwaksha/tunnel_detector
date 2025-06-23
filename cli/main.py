"""
Запускайте:
    python -m cli.main menu
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import List, Dict

import click
import colorama
from algorithms.partial_enum import PartialEnum
from algorithms.genetic import GAParams, GeneticAlgorithm
from data_io.io import load_instance, save_instance
from data_io.generator import random_instance
from experiments.runner import run_dim_experiment, make_k_list
from geometry.primitives import Point, Rectangle

colorama.init(autoreset=True)


def _avg(v: List[float]) -> float:
    return sum(v) / len(v) if v else 0.0


def _interactive_input() -> List[Rectangle]:
    tuns: List[Rectangle] = []
    print("Вводьте id та 8 координат (a b c d e f g h). Порожній id — стоп.")
    while True:
        tid = input("id: ").strip()
        if not tid:
            break
        coords = [float(input(f"{lbl}: ")) for lbl in "abcdefgh"]
        tuns.append(Rectangle(int(tid),
                              [Point(coords[i], coords[i + 1]) for i in range(0, 8, 2)]))
    return tuns


def _edit_instance(tuns: List[Rectangle]):
    print("id у задачі:", [r.id for r in tuns])
    rid = int(input("id для заміни або видалення: "))
    tuns[:] = [r for r in tuns if r.id != rid]
    if input("d-delete, r-replace : ").lower() == "r":
        tuns.extend(_interactive_input())
    save_instance(tuns, "data/instances/interactive.csv")
    print("Файл оновлено.")


def _input_menu():
    sub = input("1.Ввести  2.Зчитати  3.Згенерувати  4.Редагувати : ").strip()
    if sub == "1":
        tuns = _interactive_input()
        if tuns:
            save_instance(tuns, "data/instances/interactive.csv")
            print("Файл збережено → data/instances/interactive.csv")
    elif sub == "2":
        path = input("Шлях до CSV/JSON: ").strip()
        tuns = load_instance(path)
        save_instance(tuns, "data/instances/interactive.csv")
    elif sub == "3":
        n = int(input("n = "))
        tuns = random_instance(n, 0, 0, 20, 20, (1, 3), (1, 3))
        save_instance(tuns, "data/instances/interactive.csv")
        print("Файл збережено → data/instances/interactive.csv")
    elif sub == "4":
        if not Path("data/instances/interactive.csv").exists():
            print("Спершу зчитайте або згенеруйте файл.")
            return
        tuns = load_instance("data/instances/interactive.csv")
        _edit_instance(tuns)


def _print_menu(has_data: bool):
    print(colorama.Fore.CYAN + "Головне меню" + colorama.Style.RESET_ALL)
    st = "Задача задана." if has_data else "Немає даних."
    print((colorama.Fore.GREEN if has_data else colorama.Fore.RED) + st + colorama.Style.RESET_ALL)
    print("1 - Введення / редагування даних")
    print("2 - Розв’язати задачу всіма алгоритмами")
    print("3 - Провести експерименти")
    print("4 - Вивести дані задачі")
    print("5 - Вивести розв’язки задачі")
    print("6 - Зберегти розв’язки у файл")
    print("0 - Завершити роботу")
    print("----------")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--file", type=click.Path(exists=True, dir_okay=False), required=True)
def solve(file):
    tuns = load_instance(file)
    pe = PartialEnum(timeout_s=5)
    a_pe, k_pe, z_pe = pe.solve(tuns)
    t_pe = pe.runtime_ms
    P = GAParams(m=50, G=100, p=0.2, g=15, k_off=0.3, d_a=0.5, d_k=1.0, seed=0)
    t0 = time.perf_counter()
    best = GeneticAlgorithm(tuns, P).run()
    t_ga = (time.perf_counter() - t0) * 1e3
    click.echo(f"PE : Z={z_pe:>3}  time={t_pe:7.1f} ms")
    click.echo(f"GA : Z={best.Z:>3}  time={t_ga:7.1f} ms")
    _save_both_solutions({
        "PE": {"a": a_pe, "k": k_pe, "Z": z_pe, "T": t_pe},
        "GA": {"a": best.a, "k": best.k, "Z": best.Z, "T": t_ga}
    })
    click.echo(colorama.Fore.YELLOW + "Файл записано.")


@cli.command()
@click.option("--n", required=True, type=int)
@click.option("--seed", default=1, type=int)
def generate(n, seed):
    tuns = random_instance(n, 0, 0, 20, 20, (1, 3), (1, 3), seed)
    path = Path(f"data/instances/random_{n}_{seed}.csv")
    save_instance(tuns, path)
    click.echo(f"Збережено {len(tuns)} тунелів → {path}")


@cli.command()
@click.option("--n-min", default=10, show_default=True, type=int)
@click.option("--n-max", default=100, show_default=True, type=int)
@click.option("--step", default=10, show_default=True, type=int)
@click.option("--m-list", default="10,20,30,40,50,60,70,80,90,100")
@click.option("--k-auto/--k-manual", default=True)
@click.option("--k-list", default="")
@click.option("--N", "n_tasks", default=20, show_default=True, type=int)
def experiments(n_min, n_max, step, m_list, k_auto, k_list, n_tasks):
    n_range = range(n_min, n_max + 1, step)
    m_vals = [int(x) for x in m_list.split(",")]
    if k_auto:
        k_vals = make_k_list()
    else:
        if not k_list:
            raise click.BadParameter("Потрібно задати --k-list.")
        k_vals = [int(x) for x in k_list.split(",")]
    click.echo(f"k-list = {k_vals}")
    cfg = {"n_range": n_range, "m_list": m_vals, "k_list": k_vals, "n_pop": 20}
    csv_n, csv_m, csv_k = run_dim_experiment(cfg, repeats=n_tasks)
    click.echo(colorama.Fore.CYAN + "CSV-файли результатів:")
    click.echo(f"  {csv_n}\n  {csv_m}\n  {csv_k}")


@cli.command()
def menu():
    tunnels = None
    solutions = None
    exp_cfg = {"n_range": range(10, 101, 10),
               "m_list": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
               "k_list": make_k_list(),
               "n_pop": 20}
    N = 20
    while True:
        _print_menu(tunnels is not None)
        ch = input(colorama.Fore.YELLOW + "Ваш вибір: " + colorama.Style.RESET_ALL).strip()
        if ch == "0":
            break
        if ch == "1":
            _input_menu()
            if Path("data/instances/interactive.csv").exists():
                tunnels = load_instance("data/instances/interactive.csv")
        elif ch == "2":
            if tunnels:
                solutions = _solve_both(tunnels)
            else:
                print("Спершу задайте дані.")
        elif ch == "3":
            _exp_menu(exp_cfg, N)
            N = exp_cfg.get("_N", N)
        elif ch == "4":
            print("\n".join(map(str, tunnels)) if tunnels else "Даних немає.")
        elif ch == "5":
            if solutions:
                _print_solutions(solutions)
            else:
                print("Немає розв’язків.")
        elif ch == "6":
            if solutions:
                print("Файл →", _save_both_solutions(solutions))
            else:
                print("Немає розв’язків.")


def _exp_menu(cfg: Dict, N_def: int):
    act = input("1.Налаштувати  2.Запустити : ").strip()
    if act == "1":
        n_min = int(input("n_min = "))
        n_max = int(input("n_max = "))
        step = int(input("Δn    = "))
        cfg["n_range"] = range(n_min, n_max + 1, step)
        cfg["m_list"] = [int(x) for x in input("m_list = ").split(",")]
        if input("k auto [Y/n]? ").lower() in ("", "y", "д"):
            cfg["k_list"] = make_k_list()
        else:
            cfg["k_list"] = [int(x) for x in input("k_list = ").split(",")]
        cfg["_N"] = int(input("N (кількість задач) = ") or N_def)
        print("Конфігурацію збережено.")
    else:
        N = cfg.get("_N", N_def)
        csv_n, csv_m, csv_k = run_dim_experiment(cfg, repeats=N)
        print(colorama.Fore.CYAN + "CSV:", csv_n, csv_m, csv_k, sep="\n  ")


def _solve_both(tuns):
    pe = PartialEnum(timeout_s=5)
    a, k, z = pe.solve(tuns)
    P = GAParams(m=50, G=100, p=0.2, g=15,
                 k_off=0.3, d_a=0.5, d_k=1.0, seed=0)
    best = GeneticAlgorithm(tuns, P).run()
    print(colorama.Fore.GREEN + f"PE: Z={z}   GA: Z={best.Z}")
    return {"PE": {"a": a, "k": k, "Z": z, "T": pe.runtime_ms},
            "GA": {"a": best.a, "k": best.k, "Z": best.Z, "T": 0}}


def _print_solutions(sols):
    print("Алгоритм |      a |       k |  Z |  T, ms")
    print("---------+--------+---------+----+--------")
    for n, s in sols.items():
        print(f"{n:>8} | {s['a']:7.3f} | {s['k']:8.3f} | "
              f"{s['Z']:>2} | {s['T']:7.1f}")


def _save_both_solutions(sol) -> Path:
    out = Path("results/individual")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"solution_{int(time.time())}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        f.write("algorithm;a;k;Z;runtime_ms\n")
        for n, s in sol.items():
            f.write(f"{n};{s['a']};{s['k']};{s['Z']};{s['T']:.1f}\n")
    return path


if __name__ == "__main__":
    cli()