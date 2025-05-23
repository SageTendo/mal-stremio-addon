import datetime
import logging

from flask import jsonify, flash, make_response, url_for, redirect, Response


def handle_error(err) -> Response:
    """
    Handles errors from MyAnimeList's API
    """
    if 400 >= err.response.status_code < 500:
        flash(err, "danger")
        return make_response(redirect(url_for('index')))
    elif err.response.status_code >= 500:
        log_error(err)
        flash(err, "danger")
        return make_response(redirect(url_for('index')))


def log_error(err):
    """
    Logs errors from MyAnimeList's API
    """
    response = err.response.json()
    error_label = response.get('error', 'No error label in response').capitalize()
    message = response.get('message', 'No message field in response')
    hint = response.get('hint', 'No hint field in response')
    logging.error(f"{error_label} [{err.response.status_code}] -> {message}\n HINT: {hint}\n")


def respond_with(data, ttl: int = 0) -> Response:
    """
    Respond with CORS headers to the client
    """
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'

    if ttl > 0:
        resp.content_type = 'application/json; charset=utf-8'
        resp.vary = 'Accept-Encoding'
        resp.add_etag(True)

        # Set Expires header with correct format
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl)
        resp.expires = expires
        resp.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')

        resp.cache_control.public = True
        resp.cache_control.max_age = ttl
        resp.cache_control.s_maxage = ttl
    return resp
