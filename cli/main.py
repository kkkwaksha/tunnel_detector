"""
Запускайте:
    python -m cli.main menu
    python -m cli.main solve --file ...
"""
from __future__ import annotations
import time
from pathlib import Path
import click, colorama

from algorithms.partial_enum import solve as pe_solve
from algorithms.genetic import GAParams, GeneticAlgorithm
from data_io.io import load_instance, save_instance
from data_io.generator import random_instance

colorama.init()

# ручний ввід
def _interactive_input() -> list:
    from geometry.primitives import Point, Rectangle
    tunnels = []
    click.echo("Вводьте id і координати a b c d e f g h; порожній id — стоп.")
    while True:
        tid = click.prompt("id", default="", show_default=False)
        if not tid:
            break
        coords = [click.prompt(lbl, type=float)
                  for lbl in ("a","b","c","d","e","f","g","h")]
        tunnels.append(
            Rectangle(int(tid),
                      [Point(coords[i], coords[i+1]) for i in range(0,8,2)])
        )
    return tunnels

# зберегти PE + GA
def _save_both_solutions(sol: dict) -> Path:
    out = Path("results/individual"); out.mkdir(parents=True, exist_ok=True)
    path = out / f"solution_{int(time.time())}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        f.write("algorithm;a;k;Z;runtime_ms\n")
        for name,s in sol.items():
            f.write(f"{name};{s['a']};{s['k']};{s['Z']};{s['T']:.1f}\n")
    return path

# Click CLI
@click.group()
def cli():
    """Tunnel Detector — CLI-інтерфейс курсової роботи."""

@cli.command()
@click.option("--file", type=click.Path(exists=True, dir_okay=False),
              required=True, help="Шлях до CSV/JSON із задачею")
def solve(file):
    """Розв’язати одну ІЗ двома алгоритмами й зберегти файл result."""
    tunnels = load_instance(file)

    t0=time.perf_counter(); a_pe,k_pe,z_pe=pe_solve(tunnels); t_pe=(time.perf_counter()-t0)*1e3
    P=GAParams(m=50,G=100,p=0.2,g=15,k_off=0.3,d_a=0.5,d_k=1.0)
    t0=time.perf_counter(); best=GeneticAlgorithm(tunnels,P).run(); t_ga=(time.perf_counter()-t0)*1e3

    click.echo(f"PE : Z={z_pe:>3}  time={t_pe:7.1f} ms")
    click.echo(f"GA : Z={best.Z:>3}  time={t_ga:7.1f} ms")

    sol={"PE":{"a":a_pe,"k":k_pe,"Z":z_pe,"T":t_pe},
         "GA":{"a":best.a,"k":best.k,"Z":best.Z,"T":t_ga}}
    path=_save_both_solutions(sol); click.echo(f"Файл → {path}")

@cli.command()
@click.option("--n", required=True, type=int)
@click.option("--seed", default=1, type=int)
def generate(n, seed):
    tunnels = random_instance(n,0,0,20,20,(1,3),(1,3),seed)
    path = Path(f"data/instances/random_{n}_{seed}.csv")
    save_instance(tunnels, path)
    click.echo(f"Збережено {len(tunnels)} тунелів → {path}")

@cli.command()
def interactive():
    tunnels=_interactive_input()
    if tunnels:
        save_instance(tunnels,"data/instances/interactive.csv")
        click.echo("Збережено → data/instances/interactive.csv")

@cli.command()
def experiments():
    from experiments.runner import run_dim_experiment
    P=GAParams(m=50,G=100,p=0.2,g=15,k_off=0.3,d_a=0.5,d_k=1.0)
    cfg={"n_range":range(10,51,10),"m_list":[50],"g_list":[15]}
    csv_paths=run_dim_experiment(cfg,repeats=3)
    click.echo("CSV:",*csv_paths,sep="\n  ")

# текстове меню
def _print_menu(has_data):
    print("----------")
    print(colorama.Fore.CYAN+"Головне меню"+colorama.Style.RESET_ALL)
    print((colorama.Fore.GREEN if has_data else colorama.Fore.RED)+
          ("Задача задана." if has_data else "Немає даних.")+
          colorama.Style.RESET_ALL)
    print("1 - Введення / редагування даних")
    print("2 - Розв'язати задачу всіма алгоритмами")
    print("3 - Провести експерименти")
    print("4 - Вивести дані задачі")
    print("5 - Вивести розв'язки задачі")
    print("6 - Зберегти розв'язки у файл")
    print("0 - Завершити роботу")
    print("----------")

@cli.command()
def menu():
    tunnels=None; solutions=None
    exp_cfg={"n_range":range(10,51,10),"m_list":[50],"g_list":[15]}
    while True:
        _print_menu(tunnels is not None)
        ch=input("Ваш вибір: ").strip()
        if ch=="0": break

        if ch=="1":              # введення/редагування
            sub=input("1.Ввести  2.Зчитати  3.Згенерувати  4.Редагувати : ").strip()
            if sub=="1":
                tunnels=_interactive_input()
                if tunnels: save_instance(tunnels,"data/instances/interactive.csv")
            elif sub=="2":
                tunnels=load_instance(input("Шлях до CSV/JSON: "))
            elif sub=="3":
                n=int(input("n = ")); tunnels=random_instance(n,0,0,20,20,(1,3),(1,3))
                save_instance(tunnels,"data/instances/generated.csv")
            elif sub=="4":
                if not tunnels: print("Спершу зчитайте чи згенеруйте файл."); continue
                print("id у задачі:",[r.id for r in tunnels])
                rid=int(input("id для заміни або видалення: "))
                tunnels=[r for r in tunnels if r.id!=rid]
                if input("d-delete, r-replace : ").lower()=="r":
                    tunnels.extend(_interactive_input())
                save_instance(tunnels,"data/instances/edited.csv")
                print("Файл оновлено.")
            continue

        if ch=="2":              # розв'язати
            if not tunnels: print("Спершу задайте дані (1)."); continue
            t0=time.perf_counter(); a,k,z=pe_solve(tunnels); t_pe=(time.perf_counter()-t0)*1e3
            P=GAParams(m=50,G=100,p=0.2,g=15,k_off=0.3,d_a=0.5,d_k=1.0)
            t0=time.perf_counter(); best=GeneticAlgorithm(tunnels,P).run(); t_ga=(time.perf_counter()-t0)*1e3
            solutions={"PE":{"a":a,"k":k,"Z":z,"T":t_pe},
                        "GA":{"a":best.a,"k":best.k,"Z":best.Z,"T":t_ga}}
            print(f"PE: Z={z}   GA: Z={best.Z}")

        elif ch=="3":            # експерименти
            sub=input("1.Налаштувати  2.Запустити : ").strip()
            if sub=="1":
                exp_cfg["n_range"]=range(int(input("n_min=")),int(input("n_max="))+1,int(input("Δn=")))
                exp_cfg["m_list"]=[int(x) for x in input("m_list = ").split(",")]
                exp_cfg["g_list"]=[int(x) for x in input("g_list = ").split(",")]
                print("Конфігурацію збережено."); continue
            from experiments.runner import run_dim_experiment
            csv_paths=run_dim_experiment(exp_cfg,repeats=3)
            print("CSV:",*csv_paths,sep="\n  ")

        elif ch=="4":
            print("\n".join(map(str,tunnels)) if tunnels else "Даних немає.")

        elif ch=="5":
            if not solutions: print("Спершу розв'яжіть задачу."); continue
            print("Алгоритм |      a |       k |  Z |  T, ms")
            print("---------+--------+---------+----+--------")
            for name,s in solutions.items():
                print(f"{name:>8} | {s['a']:7.3f} | {s['k']:8.3f} | {s['Z']:>2} | {s['T']:7.1f}")

        elif ch=="6":
            if not solutions: print("Спершу розв'яжіть задачу."); continue
            print("Файл →", _save_both_solutions(solutions))

if __name__=="__main__":
    cli()