from __future__ import annotations
import random
from typing import List, Tuple
from geometry.primitives import Point, Rectangle

__all__ = ["random_instance"]

def random_instance(
    n: int,
    x0: float,
    y0: float,
    dx: float,
    dy: float,
    w_range: Tuple[float, float],
    h_range: Tuple[float, float],
    seed: int | None = None,
) -> List[Rectangle]:
    """
    Генерує n прямокутних тунелів рівномірно у прямокутнику
    [x0; x0+dx] × [y0; y0+dy] із випадковими шириною та висотою.
    """
    rnd = random.Random(seed)
    rects: List[Rectangle] = []

    for rid in range(1, n + 1):
        cx = rnd.uniform(x0, x0 + dx)
        cy = rnd.uniform(y0, y0 + dy)
        w = rnd.uniform(*w_range)
        h = rnd.uniform(*h_range)

        corners = [
            Point(cx - w / 2, cy - h / 2),
            Point(cx + w / 2, cy - h / 2),
            Point(cx + w / 2, cy + h / 2),
            Point(cx - w / 2, cy + h / 2),
        ]
        rects.append(Rectangle(rid, corners))

    return rects