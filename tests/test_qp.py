import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import Q_p, forced_composite_by_5, is_probable_prime

def test_small_cases():
    assert Q_p(2) == 5
    assert is_probable_prime(Q_p(2))
    assert Q_p(3) == 101
    assert is_probable_prime(Q_p(3))

def test_mod5_rule():
    for p in [5, 13, 17]:
        assert forced_composite_by_5(p)
        assert Q_p(p) % 5 == 0

def test_known_composite():
    assert not is_probable_prime(Q_p(5))
    assert not is_probable_prime(Q_p(13))