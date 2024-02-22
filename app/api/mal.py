import os
import secrets

import requests

from app.api import N_BYTES, QUERY_LIMIT
from app.api.utils import generate_verifier_challenger_pair, kwargs_to_dict, to_query_string
from config import Config

AUTH_URL = "https://myanimelist.net/v1"
BASE_URL = "https://api.myanimelist.net/v1"


class MyAnimeListAPI:

    def __init__(self):
        """
        Initialize the MyAnimeList API wrapper
        """

        self.redirect_uri = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/callback'
        self.client_id = os.environ.get('MAL_ID')
        self.client_secret = os.environ.get('MAL_SECRET')

        self.code_challenge_method = 'plain'
        self.code_verifier, self.code_challenge = \
            generate_verifier_challenger_pair(128, method=self.code_challenge_method)

    def get_auth(self):
        """
        Get the authorization URL for MyAnimeList API
        :return: Authorization URL
        """
        state = secrets.token_urlsafe(N_BYTES)[:16]
        query_params = 'response_type=code' \
                       f'&client_id={self.client_id}' \
                       f'&state={state}' \
                       f'&code_challenge={self.code_challenge}' \
                       f'&code_challenge_method={self.code_challenge_method}' \
                       f'&redirect_uri={self.redirect_uri}'
        return f'{AUTH_URL}/oauth2/authorize?{query_params}'

    def get_access_token(self, authorization_code: str):
        """
        Get the access token for MyAnimeList
        :param authorization_code: Authorization Code from MyAnimeList
        :return: Access Token
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'code_verifier': self.code_verifier,
            'redirect_uri': self.redirect_uri
        }
        resp = requests.post(f'{AUTH_URL}/oauth2/token', data=data)
        resp.raise_for_status()

        resp_json = resp.json()
        resp.close()

        return {
            'token_type': resp_json['token_type'],
            'expires_in': resp_json['expires_in'],
            'access_token': resp_json['access_token'],
            'refresh_token': resp_json['refresh_token']
        }

    def refresh_token(self, refresh_token: str):
        """
        Refresh the access token for MyAnimeList
        :param refresh_token: Refresh Token
        :return: Access Token
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        resp = requests.post(f'{AUTH_URL}/oauth2/token', data=data)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_user_details(token: str):
        """
        Get the user's details from MyAnimeList
        :param token: The user's access token
        :return: JSON response
        """
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        resp = requests.get(f'{BASE_URL}/users/@me', headers=headers)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_anime_list(token: str, query: str, **kwargs):
        """
        Get a list of anime from MyAnimeList
        :param token: The user's access token
        :param query: The search query
        :param kwargs: Additional query parameters
        :return: JSON response
        """
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        if query is None:
            raise Exception("A Valid Query Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        query_params = to_query_string(kwargs)

        if query_params:
            resp = requests.get(f'{BASE_URL}/anime?q={query}&{query_params}', headers=headers)
        else:
            resp = requests.get(f'{BASE_URL}/anime?q={query}', headers=headers)

        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_user_anime_list(token: str, limit: int = QUERY_LIMIT, **kwargs):
        """
        Get a user's list of anime from MyAnimeList
        :param token: The user's access token
        :param limit: The number of results to return
        :param kwargs: Additional query parameters
        :return: JSON response
        """
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        query_params = to_query_string(kwargs)

        if query_params:
            resp = requests.get(f'{BASE_URL}/users/@me/animelist?limit={limit}&{query_params}', headers=headers)
        else:
            resp = requests.get(f'{BASE_URL}/users/@me/animelist?limit={limit}', headers=headers)

        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_anime_details(token: str, anime_id: str, **kwargs):
        """
        Get anime details from MyAnimeList
        :param token: The user's access token
        :param anime_id: The ID of the anime to get details for
        :param kwargs: Additional query parameters
        :return: JSON response
        """
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        if anime_id is None:
            raise Exception("A Valid Anime ID Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        query_params = to_query_string(kwargs)

        if query_params:
            resp = requests.get(f'{BASE_URL}/anime/{anime_id}?{query_params}', headers=headers)
        else:
            resp = requests.get(f'{BASE_URL}/anime/{anime_id}', headers=headers)

        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update_watched_status(token: str, anime_id: str, episode: int, status: str = 'watching'):
        """
        Update the watched status of an anime in a user's watchlist
        :param token: The user's access token
        :param anime_id: The ID of the anime
        :param episode: The episode that is being watched
        :param status: The status to update the anime to
        :return: The details of the anime in the watchlist
        """
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        if anime_id is None:
            raise Exception("A Valid Anime ID Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        body = {'status': status, 'num_watched_episodes': episode}
        resp = requests.put(f'{BASE_URL}/anime/{anime_id}/my_list_status', headers=headers, data=body)

        resp.raise_for_status()
        return resp.json()
