"""
Digital Signatures Assignment: Signatures Implementation
P15/1198/2018
Python 3.9
"""

from hashlib import md5
from typing import Tuple
from asymmetric import pick_primes, find_e, find_d, encrypt, decrypt, phi


class Crypt:
    def __init__(self):
        prime1, prime2 = pick_primes()
        self.n = prime1 * prime2
        self.__private_key = find_e(prime1, prime2)
        self.public_key = find_d(self.__private_key, phi(prime1, prime2))
    
    def sign(self, message: str) -> Tuple[list[int], list[int]]:
        # Compute MD5 hash of the message
        message_hash = md5(message.encode("utf-8")).hexdigest()
        print(f"Message hash is {message_hash}")
        # Encrypt the message
        cipher = encrypt(message, self.__private_key, self.n)
        print(f"Cipher is {cipher}")
        # Encrypt the message hash to get the digital signature
        signature = encrypt(message_hash, self.__private_key, self.n)
        print(f"Digital signature is {signature}")
        return cipher, signature
    
    def send(self, other, cipher: list[int], signature: list[int]):
        # pass the cipher, signature, and public key to other party
        other.receive(cipher, signature, self.public_key, self.n)
    
    @staticmethod
    def receive(cipher: list[int], signature: list[int], other_public_key: int, n: int):
        # Decrypt message
        decrypted_msg = decrypt(cipher, other_public_key, n)
        print(f"Decrypted message is {repr(decrypted_msg)}")
        # Compute message hash
        message_hash = md5(decrypted_msg.encode("utf-8")).hexdigest()
        print(f"Message hash is {message_hash}")
        # Decrypt hash
        decrypted_hash = decrypt(signature, other_public_key, n)
        print(f"Decrypted hash is {decrypted_hash}")
        # Verify that message was signed by Alice
        assert decrypted_hash == message_hash


if __name__ == "__main__":
    alice = Crypt()
    bob = Crypt()

    plaintext = input("Enter a message for Alice to send to Bob: ")
    print(f"\n--- Alice ---")
    cipher, signature = alice.sign(plaintext)

    print(f"\n--- Bob ---")
    alice.send(bob, cipher, signature)
