import datetime

import requests
from flask import Blueprint, request, url_for, session, flash, abort, jsonify, make_response
from werkzeug.utils import redirect

from app.db.db import store_user, get_user
from app.routes import mal_client
from app.routes.utils import handle_error

auth_blueprint = Blueprint('auth', __name__)


def _store_user_session(user_details: dict):
    """
    Stores the user's details in the form of a web session
    :param user_details: The user details
    """
    session['user'] = user_details
    session.permanent = True


def get_valid_user(user_id: str):
    """
    Verify the access token for the user 'user_id' from the database
    :param user_id: The user's MyAnimeList ID
    :return: The user's details
    """
    if not (user := get_user(user_id)):
        return abort(make_response(jsonify({'error': 'User not found'}), 404))

    if not user.get('last_updated'):
        return abort(
            make_response(jsonify({'error': 'Invalid MAL session. Please refresh or login again.'}), 409)
        )

    expiration_date = user['last_updated'] + datetime.timedelta(seconds=user['expires_in'])
    if datetime.datetime.utcnow() > expiration_date:
        return abort(make_response(jsonify({'error': 'Access token expired'}), 401))
    return user


@auth_blueprint.route('/authorization', methods=["GET", "POST"])
def authorize_user():
    """
    Authorizes a user to access MyAnimeList's API
    :return: redirect response to MyAnimeList's auth page
    """
    if 'user' in session:
        flash("You are already logged in.", "warning")
        return redirect(url_for('index'))

    auth_url, code_verifier = mal_client.get_auth()
    session['code_verifier'] = code_verifier
    return redirect(auth_url)


@auth_blueprint.route('/callback')
def callback():
    """
    Callback URL from MyAnimeList
    :return: A webpage response with the manifest URL and Magnet URL
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

        if 'code_verifier' not in session:
            flash("Invalid callback request. First log in.", "warning")
            return redirect(url_for('index'))

        code_verifier = session['code_verifier']
        user_auth_data = mal_client.get_access_token(auth_code, code_verifier)

        user_details = mal_client.get_user_details(token=user_auth_data['access_token'])
        user_details['id'] = str(user_details['id'])
        user_details['access_token'] = user_auth_data['access_token']
        user_details['refresh_token'] = user_auth_data['refresh_token']
        user_details['expires_in'] = user_auth_data['expires_in']
        user_details['last_updated'] = datetime.datetime.utcnow()

        if not store_user(user_details):
            flash("Failed to store user details.", "danger")
            return redirect(url_for('index'))

        _store_user_session({
            'uid': user_details['uid'],
            'refresh_token': user_details['refresh_token']
        })
        flash("You are now logged in.", "success")
        return redirect(url_for('index'))
    except requests.HTTPError as e:
        return handle_error(e)


@auth_blueprint.route('/refresh')
def refresh_token():
    """
    Refreshes the access token for MyAnimeList
    :return: redirect response to the index page of the app
    """
    if not (user_session := session.get('user', None)):
        flash("Session expired! Please log in to MyAnimeList again.", "danger")
        return redirect(url_for('index'))

    try:
        user_auth_data = mal_client.refresh_token(refresh_token=user_session['refresh_token'])
        if not store_user({
            'id': user_session['uid'],
            'access_token': user_auth_data['access_token'],
            'refresh_token': user_auth_data['refresh_token'],
            'expires_in': user_auth_data['expires_in'],
            'last_updated': datetime.datetime.utcnow()
        }):
            flash("Failed to update user details.", "danger")
            return redirect(url_for('index'))

        _store_user_session({
            'uid': user_session['uid'],
            'refresh_token': user_auth_data['refresh_token']
        })
        flash("MyAnimeList session refreshed.", "success")
        return redirect(url_for('index'))
    except requests.HTTPError as e:
        return handle_error(e)


@auth_blueprint.route('/logout')
def logout():
    """
    Logs the user out and clears the session
    :return: redirect response to the index page of the app
    """
    if 'user' not in session:
        flash("You are not logged in.", "warning")
        return redirect(url_for('index'))

    session.pop('user')
    return redirect(url_for('index'))
