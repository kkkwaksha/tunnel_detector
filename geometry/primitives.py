from __future__ import annotations
from dataclasses import dataclass
from typing import List
import shapely.geometry as geom


@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float


@dataclass(slots=True)
class Rectangle:
    id: int
    corners: List[Point]

    def to_polygon(self) -> geom.Polygon:
        return geom.Polygon([(p.x, p.y) for p in self.corners])

    def __repr__(self) -> str:
        a, b, c, d, e, f, g, h = (f"{v:.2f}"
                                  for pt in self.corners
                                  for v in (pt.x, pt.y))
        indent = " " * 9
        return (f"id={self.id:>2} | "
                f"({a}, {b}) ({c}, {d})\n"
                f"{indent}({e}, {f}) ({g}, {h})")

    __str__ = __repr__

def line_intersects(rect: Rectangle, a: float, k: float) -> bool:
    M = 1e4
    line = geom.LineString([(-M, a * -M + k), (M, a * M + k)])
    return rect.to_polygon().intersects(line)