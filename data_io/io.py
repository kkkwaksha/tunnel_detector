from __future__ import annotations
import csv, json
from pathlib import Path
from typing import List
from geometry.primitives import Point, Rectangle

__all__ = ["load_instance", "save_instance", "save_solution"]

# читання
def load_instance(path: str | Path) -> List[Rectangle]:
    """
    Читає задачу з CSV або JSON.
    CSV: id;x1;y1;…;y4  (роздільник ;)
    JSON: {"tunnels":[{"id":1,"corners":[[x,y],…]},…]}
    """
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rects = []
        for obj in data["tunnels"]:
            pts = [Point(*xy) for xy in obj["corners"]]
            rects.append(Rectangle(obj["id"], pts))
        return rects

    # CSV
    rects: List[Rectangle] = []
    with path.open(newline="", encoding="utf-8") as f:
        rdr = csv.reader(f, delimiter=";")
        for row in rdr:
            rid, *coords = map(float, row)
            pts = [Point(coords[i], coords[i + 1]) for i in range(0, 8, 2)]
            rects.append(Rectangle(int(rid), pts))
    return rects

# запис задачі
def save_instance(rects: List[Rectangle], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        for r in rects:
            row = [r.id] + [coord for p in r.corners for coord in (p.x, p.y)]
            w.writerow(row)

# запис рішення
def save_solution(a: float, k: float, Z: int,
                  runtime_ms: float, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(
            [["a", "k", "Z", "runtime_ms"],
             [a, k, Z, f"{runtime_ms:.1f}"]])