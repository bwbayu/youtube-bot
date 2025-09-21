import hashlib

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
