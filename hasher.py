"""
Salted Password Hashing
Stored format:  pbkdf2$<iterations>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import os


ALGORITHM = "pbkdf2"
ITERATIONS = 600_000

def _derive(password, salt, iterations):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

#Password Hashing (new random salt every time)
def hash_password(password):
    salt = os.urandom(16)
    digest = _derive(password, salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"

#Check a password against a stored hash (new or legacy format)
def verify_password(password, stored):
    if stored.startswith(ALGORITHM + "$"):
        try:
            _, iterations, salt_hex, digest_hex = stored.split("$")
            actual = _derive(password, bytes.fromhex(salt_hex), int(iterations))
            expected = bytes.fromhex(digest_hex)
        except ValueError:
            return False
        return hmac.compare_digest(actual, expected)
    #Legacy unsalted SHA-256
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy.encode(), stored.encode())

#True if the stored hash is still in the old format
def needs_upgrade(stored):
    return not stored.startswith(ALGORITHM + "$")