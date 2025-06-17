from algorithms.partial_enum import solve
from data_io.generator import random_instance


def test_partial_enum_small():
    """Алгоритм має повертати коректний Z на невеликій ІЗ."""
    tunnels = random_instance(
        n=5, x0=0, y0=0, dx=10, dy=10,
        w_range=(1, 2), h_range=(1, 2),
        seed=42
    )
    a, k, Z = solve(tunnels)
    # має покривати хоча б один тунель, але не більше 5
    assert 1 <= Z <= 5