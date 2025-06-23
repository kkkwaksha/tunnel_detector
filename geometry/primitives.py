from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float

@dataclass(slots=True)
class Rectangle:
    id: int
    corners: List[Point]

    def __repr__(self) -> str:
        a, b, c, d, e, f, g, h = (
            f"{v:.2f}" for p in self.corners for v in (p.x, p.y)
        )
        pad = " " * 9
        return (
            f"id={self.id:>2} | "
            f"({a}, {b}) ({c}, {d})\n"
            f"{pad}({e}, {f}) ({g}, {h})"
        )

    __str__ = __repr__

def line_intersects(rect: Rectangle, a: float, k: float) -> bool:
    s = [p.y - a * p.x - k for p in rect.corners]
    return min(s) <= 0 <= max(s)