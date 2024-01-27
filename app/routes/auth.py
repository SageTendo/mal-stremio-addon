import requests

from hashlib import sha256
from flask import Blueprint, request, url_for, make_response, session, flash
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
    # check if user is logged in
    if (session_id := request.cookies.get('session_id', None)) and session_id in session:
        flash("You are already logged in", "warning")
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
        flash(request.args.get('error_description'), "warning")
        return redirect(url_for('index'))

    # check if user is logged in
    if (session_id := request.cookies.get('session_id', None)) and session_id in session:
        flash("You are already logged in", "warning")
        return redirect(url_for('index'))

    # exchange auth code for access token
    auth_code = request.args.get('code')
    try:
        auth_data = mal_client.get_token(auth_code)
    except requests.HTTPError:
        flash("Invalid auth code", "danger")
        return redirect(url_for('index'))
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
    # get user info and append the access and refresh token the info
    user_info = mal_client.get_current_user_info(access_token)

    #  encrypt username and store it as a cookie in the browser and store the user's info server-side
    salted_username = user_info['name'] + Config.SECRET_KEY
    session_id = sha256(salted_username.encode('utf-8')).hexdigest()

    # check if user's info is already in the session
    if session_id in session:
        # TODO: implement server-side session management for this to work
        flash(f"Welcome back, {user_info['name']}", "success")
    else:
        session[session_id] = user_info
        user_info['access_token'] = access_token
        user_info['refresh_token'] = auth_data['refresh_token']
        flash("You are now logged in", "success")

    # redirect to the index page with the session_id cookie
    response = make_response(redirect(url_for('index')))
    response.set_cookie('session_id', session_id)
    return response


@auth_blueprint.route('/refresh')
def refresh_token():
    """
    Refreshes the access token for MyAnimeList
    :return: redirects to the index page of the app
    """
    session_id = request.cookies.get('session_id', None)
    if session_id is None:
        flash("You must log in first", "warning")
        return redirect(url_for('index'))

    user_info = session.get(session_id, None)
    if user_info is None:
        flash("Invalid session, please log in again", "warning")
        return redirect(url_for('index'))

    try:
        auth_data = mal_client.refresh_token(user_info['refresh_token'])
    except requests.HTTPError:
        # Logout the user if refresh token is invalid
        flash("Session expired, please log in again", "warning")
        return redirect(url_for('logout'))

    # update access and refresh token
    user_info['access_token'] = auth_data['access_token']
    user_info['refresh_token'] = auth_data['refresh_token']

    # store new access token and refresh token server-side
    session[session_id] = user_info
    return redirect(url_for('index'))


@auth_blueprint.route('/logout')
def logout():
    """
    Logs the user out and clears the session
    :return: redirects to the index page of the app
    """
    if session_id := request.cookies.get('session_id', None):
        session.pop(session_id, None)
    return redirect(url_for('index'))
