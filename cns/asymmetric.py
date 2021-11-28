"""
Digital Signatures Assignment: Public-Private Key Encryption Library
P15/1198/2018
Python 3.9
"""

from random import randint, choice
from math import gcd
from typing import Tuple

N = 1000
phi = lambda p, q: (p - 1) * (q - 1)

def pick_primes() -> Tuple[int, int]:
    multiples = set()
    primes = []
    for i in range(2, N):
        if i not in multiples:
            primes.append(i)
            multiples.update(range(i * i, N + 1, i))

    return choice(primes), choice(primes)

def find_e(p: int, q: int) -> int:
    phi_of_n = phi(p, q)
    while True:
        e = randint(2, (p * q) // 2)
        if gcd(p, e) == 1 and gcd(q, e) == 1 and gcd(phi_of_n, e) == 1:
            return e

def find_d(e: int, phi_of_n: int) -> int:
    d = 2
    while (d * e) % phi_of_n != 1 or d == e:
        d += 1
    return d

def encrypt(plaintext: str, e: int, n: int) -> list[int]:
    return list(map(lambda x: pow(ord(x), e, n), plaintext))

def decrypt(cipher: list[int], d: int, n: int) -> str:
    return ''.join(map(lambda y: chr(pow(y, d, n)), cipher))
