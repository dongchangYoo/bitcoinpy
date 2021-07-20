import hashlib


def hash160(s: bytes) -> bytes:
    if not isinstance(s, bytes):
        raise Exception("input must be bytes type")
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()


def hash256(s: bytes) -> bytes:
    if not isinstance(s, bytes):
        raise Exception("input must be bytes type")
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def sha256(s: bytes) -> bytes:
    if not isinstance(s, bytes):
        raise Exception("input must be bytes type")
    return hashlib.sha256(s).digest()
