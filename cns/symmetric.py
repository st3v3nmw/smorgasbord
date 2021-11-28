"""
CSC411
Symmetric Encryption Algorithm Assignment
P15/1198/2018
"""

from itertools import permutations
from math import factorial
from functools import reduce

BLOCK_SIZE = 4  # should be a single digit


def encrypt(plain_text: str, key: int) -> str:
    # mod key to keep output in range of Unicode characters
    key = key % 0x110000

    msg_size = len(plain_text)
    ascii_codes = list(map(ord, plain_text))

    blocks = [ascii_codes[i : i + BLOCK_SIZE] for i in range(0, msg_size, BLOCK_SIZE)]
    # pad last block if necessary
    pad_size = BLOCK_SIZE - msg_size % BLOCK_SIZE
    blocks[-1] += [0 for _ in range(pad_size)]

    # mix within blocks using a permutation
    len_permutations = factorial(BLOCK_SIZE)
    temp_blocks = []
    for i in range(len(blocks)):
        # find permutation to use
        p = (key ^ i) % len_permutations
        permuted = list(permutations(blocks[i]))
        temp_blocks.append(permuted[p])
    blocks = temp_blocks

    # XOR with key
    blocks = [[e ^ key for e in block] for block in blocks]

    # flatten list
    ascii_codes = reduce(lambda x, y: x + y, blocks)
    # convert to str
    cipher_text = "".join(map(chr, ascii_codes))
    # append amount of padding done
    cipher_text += str(pad_size)
    return cipher_text


def decrypt(cipher_text: str, key: int) -> str:
    # mod size of key to keep output in range of Unicode characters
    key = key % 0x110000

    pad_size = int(cipher_text[-1])
    ascii_codes = list(map(ord, cipher_text[:-1]))

    # recreate blocks
    blocks = [
        ascii_codes[i : i + BLOCK_SIZE]
        for i in range(0, len(cipher_text) - 1, BLOCK_SIZE)
    ]

    # reverse XOR operation
    blocks = [[e ^ key for e in block] for block in blocks]

    # reverse mix within blocks
    len_permutations = factorial(BLOCK_SIZE)
    temp_blocks = []
    for i in range(len(blocks)):
        # find permutation used
        p = (key ^ i) % len_permutations
        tuple_block = tuple(blocks[i])
        for permutation in permutations(blocks[i]):
            inner_permutation = list(permutations(permutation))
            if inner_permutation[p] == tuple_block:
                temp_blocks.append(inner_permutation[0])
                break
    blocks = temp_blocks

    # remove padding in last block
    blocks[-1] = blocks[-1][: BLOCK_SIZE - pad_size]

    # flatten list
    ascii_codes = reduce(lambda x, y: x + y, blocks)
    # convert to ascii & return string
    return "".join(map(chr, ascii_codes))


if __name__ == "__main__":
    plain_text = input("Enter text to encrypt: ")
    key = int(input("Enter key: "))
    cipher_text = encrypt(plain_text, key)
    print(f"Cipher Text => {repr(cipher_text)}, len = {len(cipher_text)}")
    decrypted = decrypt(cipher_text, key)
    print(f"Decrypted => {repr(decrypted)}, len = {len(decrypted)}")
    assert decrypted == plain_text

    # Example
    # Text to encrypt = 'this is a test'
    # Key = 375
    # Cipher Text = 'ĞğĄăĄĞŗŗăĖĒŗŷĄăŷ2'
