"""
Salted Password Hashing
Stored format:  pbkdf2$<iterations>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import os

class PasswordHasher:
    ALGORITHM = "pbkdf2"
    ITERATIONS = 600_000
    SALT_BYTES = 16  

    def __init__(self, iterations=ITERATIONS):
        self.iterations = iterations

    @staticmethod
    def _derive(password, salt, iterations):
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    #Password Hashing (new random salt every time)
    def hash(self, password):
        salt = os.urandom(self.SALT_BYTES)
        digest = self._derive(password, salt, self.iterations)
        return f"{self.ALGORITHM}${self.iterations}${salt.hex()}${digest.hex()}"

    #Check a plain-text password against a stored hash
    def verify(self, password, stored):
        try:
            algorithm, iterations, salt_hex, digest_hex = stored.split("$")
            if algorithm != self.ALGORITHM:
                return False
            actual = self._derive(password, bytes.fromhex(salt_hex), int(iterations))
            expected = bytes.fromhex(digest_hex)
        except (ValueError, OverflowError):
            return False
        return hmac.compare_digest(actual, expected)