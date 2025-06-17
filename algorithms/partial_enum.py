from __future__ import annotations
import time
from itertools import combinations
from typing import List, Tuple, Optional
from geometry.primitives import Rectangle, line_intersects


class PartialEnum:
    def __init__(self, timeout_s: float = 5.0, max_pairs: Optional[int] = None):
        self.timeout_s = timeout_s
        self.max_pairs = max_pairs
        self.pairs_checked = 0
        self.runtime_ms = 0.0

    def solve(self, tunnels: List[Rectangle]) -> Tuple[float, float, int]:
        if len(tunnels) < 2:
            return 0.0, 0.0, 0
        best_a = best_k = 0.0
        best_Z = -1
        t_start = time.perf_counter()
        for r1, r2 in combinations(tunnels, 2):
            for v1 in r1.corners:
                for v2 in r2.corners:
                    self.pairs_checked += 1
                    if self.max_pairs and self.pairs_checked > self.max_pairs:
                        self.runtime_ms = (time.perf_counter() - t_start) * 1e3
                        return best_a, best_k, best_Z
                    if time.perf_counter() - t_start > self.timeout_s:
                        self.runtime_ms = (time.perf_counter() - t_start) * 1e3
                        return best_a, best_k, best_Z
                    if v1.x == v2.x:
                        continue
                    a = (v2.y - v1.y) / (v2.x - v1.x)
                    k = v1.y - a * v1.x
                    Z = sum(line_intersects(r, a, k) for r in tunnels)
                    if Z > best_Z:
                        best_a, best_k, best_Z = a, k, Z
        self.runtime_ms = (time.perf_counter() - t_start) * 1e3
        return best_a, best_k, best_Z


def solve(tunnels, timeout_s: float = 5.0, max_pairs: Optional[int] = None):
    return PartialEnum(timeout_s, max_pairs).solve(tunnels)