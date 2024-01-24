from flask import Blueprint, request, render_template
from werkzeug.utils import redirect

from app.db.db import UID_map_collection
from app.routes import mal_client
from config import Config

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/authorization', methods=["GET", "POST"])
def authorize_user():
    """
    Authorizes a user to access MyAnimeList's API
    :return: redirects to MyAnimeList's auth page
    """
    return redirect(mal_client.get_auth())


@auth_blueprint.route('/callback')
def redirect_url():
    """
    Callback URL from MyAnimeList
    :return: A webpage with the manifest URL and Magnet URL
    """
    code = request.args.get('code')
    auth_data = mal_client.get_token(code)
    access_token = auth_data['access_token']

    # Get the user's username
    user_details = mal_client.get_user_details(access_token)
    user_id = str(user_details['id'])

    # Add the user to the database
    user = UID_map_collection.find_one({'uid': user_id})
    if user:
        UID_map_collection.update_one(user, {'$set': {'access_token': access_token}})
    else:
        UID_map_collection.insert_one({'uid': user_id, 'access_token': access_token})

    manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/{user_id}/manifest.json'
    manifest_magnet = f'stremio://{Config.REDIRECT_URL}/{user_id}/manifest.json'
    return render_template('index.html', manifest_url=manifest_url, manifest_magnet=manifest_magnet)
