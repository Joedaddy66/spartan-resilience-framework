import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from qpprime.qp import (
    Q_p, forced_composite_by_5, is_probable_prime, Qp_mod, 
    killer_residues, killed_by_m, pollards_rho, factor_semismooth
)

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

def test_is_probable_prime_with_secure_random():
    """Test Miller-Rabin primality testing with secure random (fixed Bandit B311)"""
    # Test known primes
    assert is_probable_prime(2)
    assert is_probable_prime(3)
    assert is_probable_prime(5)
    assert is_probable_prime(7)
    assert is_probable_prime(11)
    assert is_probable_prime(97)
    assert is_probable_prime(1009)
    
    # Test known composites
    assert not is_probable_prime(4)
    assert not is_probable_prime(9)
    assert not is_probable_prime(15)
    assert not is_probable_prime(100)
    assert not is_probable_prime(1000)
    
    # Test edge cases
    assert not is_probable_prime(0)
    assert not is_probable_prime(1)

def test_pollards_rho_with_secure_random():
    """Test Pollard's Rho factorization with secure random (fixed Bandit B311)"""
    # Test simple composites
    assert pollards_rho(15) in [3, 5]
    assert pollards_rho(21) in [3, 7]
    assert pollards_rho(35) in [5, 7]
    
    # Test even numbers (quick return)
    assert pollards_rho(10) == 2
    assert pollards_rho(100) == 2
    
    # Test divisible by 3 (quick return)
    assert pollards_rho(9) == 3
    assert pollards_rho(27) == 3

def test_factor_semismooth_with_secure_random():
    """Test factorization using secure random for Pollard's Rho (fixed Bandit B311)"""
    # Test small numbers
    factors = factor_semismooth(12)
    assert factors[2] == 2
    assert factors[3] == 1
    
    factors = factor_semismooth(100)
    assert factors[2] == 2
    assert factors[5] == 2
    
    # Test prime number
    factors = factor_semismooth(17)
    assert factors[17] == 1
    assert len(factors) == 1
    
    # Test composite with larger factors
    factors = factor_semismooth(143)  # 11 * 13
    assert 11 in factors
    assert 13 in factors