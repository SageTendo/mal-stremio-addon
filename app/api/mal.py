import os
import secrets

import requests
from dotenv import load_dotenv

from app.api import N_BYTES
from app.api.utils import generate_verifier_challenger_pair, kwargs_to_dict, to_query_string

AUTH_URL = "https://myanimelist.net/v1"
BASE_URL = "https://api.myanimelist.net/v1"


class MyAnimeListAPI:

    def __init__(self):
        flask_host = os.environ.get('FLASK_RUN_HOST')
        flask_host = 'localhost' if flask_host == '127.0.0.1' else flask_host
        flask_port = os.environ.get('FLASK_RUN_PORT')
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
        state = secrets.token_urlsafe(N_BYTES)[:16]
        query_params = 'response_type=code' \
                       f'&client_id={self.client_id}' \
                       f'&state={state}' \
                       f'&code_challenge={self.code_challenge}' \
                       f'&code_challenge_method={self.code_challenge_method}' \
            # f'&redirect_uri={self.redirect_url}'
        return f'{AUTH_URL}/oauth2/authorize?{query_params}'

    def get_token(self, authorization_code: str):
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

    def refresh_token(self):
        if self.refresh_tkn is None:
            raise Exception('No refresh token')

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_tkn
        }
        resp = requests.post(f'{AUTH_URL}/oauth2/token', data=data)
        # self.access_tkn =
        #  TODO

    @staticmethod
    def get_anime_list(token: str, query: str, **kwargs):
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
    def get_user_anime_list(token, **kwargs):
        if token is None:
            raise Exception("Auth Token Must Be Provided")

        headers = kwargs_to_dict(Authorization=f'Bearer {token}')
        query_params = to_query_string(kwargs)

        if query_params:
            resp = requests.get(f'{BASE_URL}/users/@me/animelist?{query_params}', headers=headers)
        else:
            resp = requests.get(f'{BASE_URL}/users/@me/animelist', headers=headers)

        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_anime_details(token, anime_id, **kwargs):
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


if __name__ == '__main__':
    load_dotenv()
    mal = MyAnimeListAPI()
    auth_token = os.environ.get("MAL_AUTH_TOKEN")
    print(mal.get_anime_details(auth_token, 36793, fields='genres'))
