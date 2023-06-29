import secrets
from urllib.parse import urlencode

from app.api import N_BYTES


def generate_verifier_challenger_pair(length: int, method: str = None):
    """
    Generate a verifier and challenge as a tuple
    :param length: The length of the verifier string
    :param method: The method to use to generate the challenge
    :return: verifier, challenge
    """
    verifier = generate_verifier(length)
    return verifier, generate_challenge(verifier, method)


def generate_verifier(length: int = 128):
    """
    Generate a random verifier string using the Secrets library
    :param length: The length of the verifier string
    :return: verifier
    """
    if not 43 <= length <= 128:
        raise ValueError("Param: 'Length' must be a min of 43 or a max of 128")
    return secrets.token_urlsafe(N_BYTES)[:length]


def generate_challenge(verifier, method):
    """
    Generate a challenge string using the Secrets library
    :param verifier: The verifier string
    :param method: The method to use to generate the challenge
    :return: the generated challenge
    """
    if method == 'plain' or method is None:
        return verifier


def kwargs_to_dict(**kwargs):
    """
    Convert Keyword arguments to a dictionary
    :param kwargs: The keyword arguments
    :return: data dictionary
    """
    data = {}
    for key in kwargs:
        value = kwargs.get(key, None)
        if value is not None:
            data[key] = value
    return data if len(data) > 0 else None


def to_query_string(kwargs):
    """
    Convert Keyword arguments to a query string
    :param kwargs: The keyword arguments
    :return: query string
    """
    data = kwargs_to_dict(**kwargs)
    return urlencode(data) if data else None
