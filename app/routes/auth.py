import requests
from flask import Blueprint, request, url_for, session, flash
from werkzeug.utils import redirect

from app.db.db import store_user
from app.routes import mal_client
from app.routes.utils import handle_error

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/authorization', methods=["GET", "POST"])
def authorize_user():
    """
    Authorizes a user to access MyAnimeList's API
    :return: redirects to MyAnimeList's auth page
    """
    if 'user' in session:
        flash("You are already logged in.", "warning")
        return redirect(url_for('index'))
    return redirect(mal_client.get_auth())


@auth_blueprint.route('/callback')
def callback():
    """
    Callback URL from MyAnimeList
    :return: A webpage with the manifest URL and Magnet URL
    """
    # check if error occurred from MyAnimeList
    if request.args.get('error'):
        flash(request.args.get('error_description'), "danger")
        return redirect(url_for('index'))

    if 'user' in session:
        flash("You are already logged in.", "warning")
        return redirect(url_for('index'))

    try:
        # exchange auth code for access token
        if not (auth_code := request.args.get('code', None)):
            return redirect(url_for('index'))
        resp = mal_client.get_access_token(auth_code)

        # get user details and append the access and refresh token the info
        user_details = mal_client.get_user_details(token=resp['access_token'])
        user_details['id'] = str(user_details['id'])
        user_details['access_token'] = resp['access_token']
        user_details['refresh_token'] = resp['refresh_token']
        user_details['expires_in'] = resp['expires_in']

        store_user(user_details)
        session['user'] = user_details
        flash("You are now logged in.", "success")
        return redirect(url_for('index'))
    except requests.HTTPError as e:
        return handle_error(e)


@auth_blueprint.route('/refresh')
def refresh_token():
    """
    Refreshes the access token for MyAnimeList
    :return: redirects to the index page of the app
    """
    if not (user_details := session.get('user', None)):
        flash("Session expired! Please log in to MyAnimeList again.", "danger")
        return redirect(url_for('index'))

    try:
        resp = mal_client.refresh_token(refresh_token=user_details['refresh_token'])
        user_details['access_token'] = resp['access_token']
        user_details['refresh_token'] = resp['refresh_token']
        user_details['expires_in'] = resp['expires_in']

        store_user(user_details)
        session['user'] = user_details
        flash("MyAnimeList session refreshed.", "success")
        return redirect(url_for('index'))
    except requests.HTTPError as e:
        return handle_error(e)


@auth_blueprint.route('/logout')
def logout():
    """
    Logs the user out and clears the session
    :return: redirects to the index page of the app
    """
    session.pop('user')
    return redirect(url_for('index'))
