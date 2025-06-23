"""
 Генетичний алгоритм пошуку прямої y = a·x + k,
 що перетинає максимальну кількість тунелів.
 Працює із класами Rectangle та Point з geometry.primitives.
"""
from __future__ import annotations
from dataclasses import dataclass
from random import Random
from typing import List, Tuple
import time

from geometry.primitives import Rectangle, line_intersects


@dataclass(slots=True)
class GAParams:
    m: int
    G: int
    p: float
    g: int
    k_off: float
    d_a: float
    d_k: float
    seed: int | None = None


@dataclass(slots=True)
class Best:
    a: float
    k: float
    Z: int


class GeneticAlgorithm:
    def __init__(self, tunnels: List[Rectangle], params: GAParams):
        self.tunnels = tunnels
        self.P = params
        self.rnd = Random(self.P.seed)

    def _fitness(self, a: float, k: float) -> int:
        return sum(line_intersects(r, a, k) for r in self.tunnels)

    def _random_line(self) -> Tuple[float, float]:
        """Початкове випадкове рішення у розумних межах."""
        return self.rnd.uniform(-5, 5), self.rnd.uniform(-100, 100)

    def _tournament(self, pop: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Ділимо випадково навпіл, повертаємо найкращого з кожної половини."""
        self.rnd.shuffle(pop)
        half = len(pop) // 2
        left, right = pop[:half], pop[half:]
        best_L = max(left, key=lambda ind: self._fitness(*ind))
        best_R = max(right, key=lambda ind: self._fitness(*ind))
        return best_L, best_R

    def _crossover(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
        a1, k1 = p1
        a2, k2 = p2
        a_min = a2 - (a2 - a1) * self.P.k_off
        a_max = a2 + (a2 - a1) * self.P.k_off
        k_min = k2 - (k2 - k1) * self.P.k_off
        k_max = k2 + (k2 - k1) * self.P.k_off
        a = self.rnd.uniform(a_min, a_max)
        k = self.rnd.uniform(k_min, k_max)
        return a, k

    def _mutate(self, ind: Tuple[float, float]) -> Tuple[float, float]:
        a, k = ind
        if self.rnd.random() < self.P.p:
            a += self.rnd.uniform(-self.P.d_a, self.P.d_a)
        if self.rnd.random() < self.P.p:
            k += self.rnd.uniform(-self.P.d_k, self.P.d_k)
        return a, k

    # основний цикл
    def run(self) -> Best:
        population = [self._random_line() for _ in range(self.P.m)]
        best = Best(*max(population, key=lambda ind: self._fitness(*ind)),
                    Z=0)
        best.Z = self._fitness(best.a, best.k)

        gen, stagnation = 0, 0
        while gen < self.P.G and stagnation < self.P.g:
            new_pop: List[Tuple[float, float]] = []
            while len(new_pop) < self.P.m:
                p1, p2 = self._tournament(population)
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                new_pop.append(child)

            population = new_pop
            current_best = max(population, key=lambda ind: self._fitness(*ind))
            current_Z = self._fitness(*current_best)
            if current_Z > best.Z:
                best = Best(*current_best, Z=current_Z)
                stagnation = 0
            else:
                stagnation += 1
            gen += 1

        return best