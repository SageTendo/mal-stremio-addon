import datetime
import logging

from flask import Response, flash, jsonify, make_response, redirect, request, url_for
from requests import HTTPError


def handle_auth_error(err: HTTPError) -> Response:
    """
    Handles auth related errors from MyAnimeList and notify the user
    """
    if not err.response:
        flash("No response received from MyAnimeList.", "danger")
        return make_response(redirect(url_for("index")))

    code = err.response.status_code
    content_type = err.response.headers.get("Content-Type", "")
    body = err.response.text.strip()

    if "application/json" in content_type.lower():
        try:
            response = err.response.json()
        except ValueError:
            body = err.response.text.strip()
            flash("Invalid response received from MyAnimeList.", "danger")
            log_error(
                "INVALID_JSON", "Empty or invalid JSON response from MAL", body, code
            )
            return make_response(redirect(url_for("index")))

        error_label = response.get("error", "No error label in response").upper()
        message = response.get(
            "message", "Unknown error occurred when tyring to access MyAnimeList"
        )
        hint = response.get("hint", "No hint field in response")
        flash(message, "danger")
        log_error(error_label, message, hint, code)
        return make_response(redirect(url_for("index")))

    if code == 400:
        flash("Invalid request was made to MyAnimeList.", "danger")
    elif code == 401:
        flash("Request could not be made to MyAnimeList. Are you logged in?", "danger")
    elif code == 403:
        flash("Unauthorized request when trying to access MyAnimeList.", "danger")
    elif code == 404:
        flash("MyAnimeList returned a not found error.", "danger")
    elif code >= 500:
        flash(
            "MyAnimeList returned an internal server error. The server might be down, try again later.",
            "danger",
        )
    else:
        flash("Unknown error occurred when trying to access MyAnimeList.", "danger")
    log_error(
        "NON_JSON_RESPONSE",
        "Unknown error occurred when trying to access MyAnimeList",
        body,
        code,
    )
    return make_response(redirect(url_for("index")))


def handle_api_error(err: HTTPError):
    """
    Handles and log external API related errors
    """
    code = err.response.status_code
    response = err.response.json()
    error_label = response.get("error", "No error label in response").upper()
    message = response.get(
        "message", "Unknown error occurred when tyring to access MyAnimeList"
    )
    hint = response.get("hint", "No hint field in response")
    log_error(error_label, message, hint, code)


def log_error(error_label: str, message: str, hint: str, code: int = 0):
    logging.error(
        "%s [%s]\n  MESSAGE: %s\n  HINT:    %s",
        error_label,
        code,
        message,
        hint,
    )


def respond_with(
    data: dict,
    private: bool = False,
    cache_max_age: int = 0,
    stale_revalidate: int = 0,
    stale_error: int = 0,
    stremio_response: bool = False,
) -> Response:
    """
    Respond with CORS & cache headers to the client
    data: the data to respond with
    private: whether to make caching available only to the user
    cacheMaxAge: How long to cache the response (0 for no caching)
    stale_revalidate: How long to serve stale content while revalidating
    stale_error: How long to serve stale content when an error occurs
    stremio_response: Whether the response is intended for Stremio
    """
    if stremio_response:
        data = _add_stremio_headers(data, cache_max_age, stale_revalidate, stale_error)

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
            f"stale-while-revalidate={stale_revalidate}"
            if stale_revalidate > 0
            else "",
            f"stale-if-error={stale_error}" if stale_error > 0 else "",
        ]
        resp.headers["Cache-Control"] = ", ".join(filter(None, cache_control))
    return resp


def _add_stremio_headers(
    data: dict, cache_max_age: int, stale_revalidate: int, stale_error: int
) -> dict:
    if cache_max_age > 0:
        data["cacheMaxAge"] = cache_max_age
        data["staleRevalidate"] = stale_revalidate
        data["staleError"] = stale_error
    return data
