import logging

from flask import jsonify, flash, make_response, url_for, redirect


def handle_error(err):
    if 400 >= err.response.status_code < 500:
        flash(err, "danger")
        return make_response(redirect(url_for('index')))
    elif err.response.status_code >= 500:
        log_error(err)
        flash(err, "danger")
        return make_response(redirect(url_for('index')))


def log_error(err):
    response = err.response.json()
    error_label = response.get('error', 'No error label in response').capitalize()
    message = response.get('message', 'No message field in response')
    hint = response.get('hint', 'No hint field in response')
    logging.error(f"{error_label} [{err.response.status_code}] -> {message}\n HINT: {hint}\n")


# Enable CORS
def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp
