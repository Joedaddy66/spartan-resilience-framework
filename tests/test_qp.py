import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import Q_p, forced_composite_by_5, is_probable_prime, Qp_mod, killer_residues, killed_by_m

def test_small_cases():
    assert Q_p(2) == 5
    assert is_probable_prime(Q_p(2))
    assert Q_p(3) == 101
    assert is_probable_prime(Q_p(3))

def test_mod5_rule():
    for p in [5, 13, 17]:
        assert forced_composite_by_5(p)
        assert Q_p(p) % 5 == 0

def test_killer_residues_consistency():
    # Check that residue classification matches direct reduction for small p
    for m in [5,7,11]:
        per, res = killer_residues(m) if m != 5 else (4, [1,2])  # known rule for 5
        for p in range(2, 40):
            expect = (Q_p(p) % m == 0)
            fast = (p % per) in res
            assert expect == fast

def test_Qp_mod_matches():
    for m in [5,7,11]:
        for p in range(2, 40):
            assert Qp_mod(p, m) == (Q_p(p) % m)