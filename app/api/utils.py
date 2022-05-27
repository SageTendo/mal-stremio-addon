import secrets
from urllib.parse import urlencode

from app.api import N_BYTES


def generate_verifier_challenger_pair(length: int, method: str = None):
    verifier = generate_verifier(length)
    return verifier, generate_challenge(verifier, method)


def generate_verifier(length: int = 128):
    if not 43 <= length <= 128:
        raise ValueError("Param: 'Length' must be a min of 43 or a max of 128")
    return secrets.token_urlsafe(N_BYTES)[:length]


def generate_challenge(verifier, method):
    if method == 'plain' or method is None:
        return verifier


def kwargs_to_dict(**kwargs):
    data = {}
    for key in kwargs:
        value = kwargs.get(key, None)
        if value is not None:
            data[key] = value
    return data if len(data) > 0 else None


def to_query_string(kwargs):
    data = kwargs_to_dict(**kwargs)
    return urlencode(data) if data else None
