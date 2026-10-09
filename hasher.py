import hashlib

#Password Hashing
def hash_password(password):
    # Encode the string into bytes, then hash it, then return the hex string
    return hashlib.sha256(password.encode()).hexdigest()