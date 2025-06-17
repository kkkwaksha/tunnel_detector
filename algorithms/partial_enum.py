from __future__ import annotations

import time
from itertools import combinations
from typing import List, Tuple, Optional

from geometry.primitives import Rectangle, line_intersects


def solve(
    tunnels: List[Rectangle],
    timeout_s: float = 5.0,
    max_pairs: Optional[int] = None,
) -> Tuple[float, float, int]:
    """
    Частковий перебір (partial enumeration).

    Перебираємо усі пари прямокутників, далі всі пари їхніх вершин,
    будуємо пряму через ці вершини й рахуємо, скільки тунелів вона
    перетинає. Повертаємо найкращі a, k та максимальне Z.

    Захист від «зависання»:
    - time-out  (timeout_s, сек)
    - ліміт на кількість перевірених пар вершин (max_pairs)
    """
    if len(tunnels) < 2:
        return 0.0, 0.0, 0

    best_a = best_k = 0.0
    best_Z = -1

    t_start = time.perf_counter()
    checked_pairs = 0

    for r1, r2 in combinations(tunnels, 2):
        for v1 in r1.corners:
            for v2 in r2.corners:
                # стопери
                checked_pairs += 1
                if max_pairs is not None and checked_pairs > max_pairs:
                    return best_a, best_k, best_Z
                if time.perf_counter() - t_start > timeout_s:
                    return best_a, best_k, best_Z

                if v1.x == v2.x: # вертикальна пряма - пропускаємо
                    continue

                a = (v2.y - v1.y) / (v2.x - v1.x)
                k = v1.y - a * v1.x
                Z = sum(line_intersects(r, a, k) for r in tunnels)

                if Z > best_Z:
                    best_a, best_k, best_Z = a, k, Z

    return best_a, best_k, best_Z