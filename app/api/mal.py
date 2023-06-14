import os
import secrets

import requests
from dotenv import load_dotenv

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
        flask_host = 'localhost' if Config.FLASK_HOST == "127.0.0.1" else Config.FLASK_HOST
        flask_port = Config.FLASK_PORT

        self.redirect_url = f'http://{flask_host}:{flask_port}/callback'
        self.client_id = os.environ.get('MAL_ID')
        self.client_secret = os.environ.get('MAL_SECRET')

        self.code_challenge_method = 'plain'
        self.code_verifier, self.code_challenge = generate_verifier_challenger_pair(128,
                                                                                    method=self.code_challenge_method)
        self.token_type = None
        self.token_expr = None
        self.access_tkn = None
        self.refresh_tkn = None

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
            # f'&redirect_uri={self.redirect_url}'
        return f'{AUTH_URL}/oauth2/authorize?{query_params}'

    def get_token(self, authorization_code: str):
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
            # 'redirect_url': self.redirect_url
        }
        resp = requests.post(f'{AUTH_URL}/oauth2/token', data=data)
        resp.raise_for_status()

        resp_json = resp.json()
        self.token_type = resp_json['token_type']
        self.token_expr = resp_json['expires_in']
        self.access_tkn = resp_json['access_token']
        self.refresh_tkn = resp_json['refresh_token']

        print('Token Generated')
        resp.close()

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
    def get_user_anime_list(token, limit: int = QUERY_LIMIT, **kwargs):
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
    def get_anime_details(token, anime_id, **kwargs):
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
            raise Exception("A Valid Query Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        query_params = to_query_string(kwargs)

        if query_params:
            resp = requests.get(f'{BASE_URL}/anime/{anime_id}?{query_params}', headers=headers)
        else:
            resp = requests.get(f'{BASE_URL}/anime/{anime_id}', headers=headers)

        resp.raise_for_status()
        return resp.json()
