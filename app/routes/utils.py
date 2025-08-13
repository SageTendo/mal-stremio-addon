import datetime
import logging

from flask import jsonify, flash, make_response, url_for, redirect, Response, request


def handle_error(err) -> Response:
    """
    Handles errors from MyAnimeList's API
    """
    if 400 >= err.response.status_code < 500:
        flash(err, "danger")
        return make_response(redirect(url_for("index")))
    elif err.response.status_code >= 500:
        log_error(err)
        flash(err, "danger")
        return make_response(redirect(url_for("index")))
    else:
        log_error(err)
        flash("Unkown error occurred when tyring to access MyAnimeList", "danger")
        return make_response(redirect(url_for("index")))


def log_error(err):
    """
    Logs errors from MyAnimeList's API
    """
    response = err.response.json()
    error_label = response.get("error", "No error label in response").capitalize()
    message = response.get("message", "No message field in response")
    hint = response.get("hint", "No hint field in response")
    logging.error(
        f"{error_label} [{err.response.status_code}] -> {message}\n HINT: {hint}\n"
    )


def respond_with(
    data,
    private: bool = False,
    cache_max_age: int = 0,
    stale_revalidate: int = 0,
    stale_error: int = 0,
) -> Response:
    """
    Respond with CORS headers to the client
    data: the data to respond with
    private: whether to make caching available only to the user
    cacheMaxAge: How long to cache the response (0 for no caching)
    stale_revalidate: How long to serve stale content while revalidating
    stale_error: How long to serve stale content when an error occurs
    """
    resp = jsonify(data)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "*"

    if cache_max_age > 0:
        resp.content_type = "application/json; charset=utf-8"
        resp.vary = "Accept-Encoding"
        resp.add_etag(True)
        resp.make_conditional(request)

        # Set Expires header with correct format
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_max_age)
        resp.expires = expires
        resp.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

        cache_control = [
            "private" if private else "public",
            f"max-age={cache_max_age}",
            f"s-maxage={cache_max_age}" if not private else "",
            f"stale-while-revalidate={stale_revalidate}" if stale_revalidate > 0 else "",
            f"stale-if-error={stale_error}" if stale_error > 0 else "",
        ]
        resp.headers["Cache-Control"] = ", ".join(filter(None, cache_control))
    return resp
