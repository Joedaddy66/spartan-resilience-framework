import random, math
from typing import Dict, List

def mersenne(p: int) -> int:
    return (1 << p) - 1

def Q_p(p: int) -> int:
    M = mersenne(p)
    return 4 * (M - 2) * (M - 2) + 1

def p_mod4_class(p: int) -> int:
    return p % 4

def forced_composite_by_5(p: int) -> bool:
    # For p > 2, Q_p divisible by 5 when p ≡ 1 or 2 (mod 4); exception p=2 → Q_2 = 5 (prime)
    return p > 2 and (p % 4 in (1, 2))

_SMALL_PRIMES = [2,3,5,7,11,13,17,19,23,29,31,37]

def is_probable_prime(n: int, k: int = 16) -> bool:
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return n == p
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True

def small_trial_factor(n: int, limit: int = 200000):
    if n % 2 == 0:
        return 2
    f = 3
    while f * f <= n and f <= limit:
        if n % f == 0:
            return f
        f += 2
    return None

def pollards_rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
    for _ in range(6):
        x = random.randrange(2, n-1)
        y = x
        c = random.randrange(1, n-1)
        d = 1
        while d == 1:
            x = (x*x + c) % n
            y = (y*y + c) % n
            y = (y*y + c) % n
            d = math.gcd(abs(x - y), n)
            if d == n:
                break
        if 1 < d < n:
            return d
    return 1

def factor_semismooth(n: int, max_steps: int = 6) -> Dict[int,int]:
    factors: Dict[int,int] = {}
    if n == 1:
        return factors
    if is_probable_prime(n):
        factors[n] = factors.get(n, 0) + 1
        return factors
    m = n
    if m % 2 == 0:
        cnt = 0
        while m % 2 == 0:
            m //= 2
            cnt += 1
        factors[2] = factors.get(2, 0) + cnt
    sp = 3
    while sp * sp <= m and sp <= 100000:
        if m % sp == 0:
            cnt = 0
            while m % sp == 0:
                m //= sp
                cnt += 1
            factors[sp] = factors.get(sp, 0) + cnt
        sp += 2
    if m == 1:
        return factors
    stack = [m]
    steps = 0
    while stack and steps < max_steps:
        cur = stack.pop()
        if is_probable_prime(cur):
            factors[cur] = factors.get(cur, 0) + 1
            continue
        d = pollards_rho(cur)
        steps += 1
        if d in (1, cur):
            factors[cur] = factors.get(cur, 0) + 1
        else:
            a, b = d, cur // d
            stack.append(a)
            stack.append(b)
    return factors

def summarize_p_list(p_list: List[int]):
    rows = []
    for p in p_list:
        Q = Q_p(p)
        rows.append({
            "p": p,
            "p_mod_4": p_mod4_class(p),
            "forced_by_5": forced_composite_by_5(p),
            "Qp_mod_5": Q % 5,
            "Qp_digits": len(str(Q)),
            "Qp_probably_prime": is_probable_prime(Q, k=16),
        })
    return rows