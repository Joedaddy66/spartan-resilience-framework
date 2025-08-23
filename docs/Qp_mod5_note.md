# Mod-5 Law for Q_p = 4(M_p - 2)^2 + 1

Let M_p = 2^p - 1. Powers of 2 mod 5 cycle with period 4: 2,4,3,1.
Compute:
- M_p ≡ 1,3,2,0 (mod 5) for p ≡ 1,2,3,0 (mod 4).
- M_p - 2 ≡ 4,1,0,3 → squares to 1,1,0,4 → ×4 → 4,4,0,1 → +1 → 0,0,1,2.

Therefore:
- Q_p ≡ 0 (mod 5) when p ≡ 1 or 2 (mod 4);
- Q_p ≡ 1 (mod 5) when p ≡ 3 (mod 4);
- Q_p ≡ 2 (mod 5) when p ≡ 0 (mod 4).

For all p > 2 with p ≡ 1 or 2 (mod 4), Q_p is composite with factor 5. The only prime multiple of 5 here is Q_2 = 5.