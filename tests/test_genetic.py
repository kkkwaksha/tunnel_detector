from algorithms.genetic import GAParams, GeneticAlgorithm
from data_io.generator import random_instance

def test_ga_smoke():
    tunnels = random_instance(6, 0, 0, 10, 10, (1, 2), (1, 2), seed=2)
    P = GAParams(m=30, G=50, p=0.2, g=10,
                 k_off=0.3, d_a=0.5, d_k=1.0, seed=123)
    ga = GeneticAlgorithm(tunnels, P)
    best = ga.run()
    assert 1 <= best.Z <= 6