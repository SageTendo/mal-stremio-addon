import secrets
from urllib.parse import urlencode

from app.api import N_BYTES


# Return a verifier and challenge as a tuple
def generate_verifier_challenger_pair(length: int, method: str = None):
    verifier = generate_verifier(length)
    return verifier, generate_challenge(verifier, method)


# Generate a random verifier string using the Secrets library
def generate_verifier(length: int = 128):
    if not 43 <= length <= 128:
        raise ValueError("Param: 'Length' must be a min of 43 or a max of 128")
    return secrets.token_urlsafe(N_BYTES)[:length]


# Return a challenge
# In the case where an encoded challenge is required, the implementation would be added to this function
def generate_challenge(verifier, method):
    if method == 'plain' or method is None:
        return verifier


# Convert Keyword arguments to a dictionary
def kwargs_to_dict(**kwargs):
    data = {}
    for key in kwargs:
        value = kwargs.get(key, None)
        if value is not None:
            data[key] = value
    return data if len(data) > 0 else None


# Convert Keyword arguments to query string parameters
def to_query_string(kwargs):
    data = kwargs_to_dict(**kwargs)
    return urlencode(data) if data else None
