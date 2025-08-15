import logging

from flask import (
    Flask,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_compress import Compress  # type: ignore
from waitress import serve

import config
from app.db.db import get_user, store_user
from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.content_sync import content_sync_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta_bp
from app.routes.stream import stream_bp
from config import Config

app = Flask(__name__, template_folder="./templates", static_folder="./static")
app.config.from_object("config.Config")
app.register_blueprint(auth_blueprint)
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(meta_bp)
app.register_blueprint(content_sync_bp)
app.register_blueprint(stream_bp)

Compress(app)

logging.basicConfig(format="%(asctime)s %(message)s")


@app.route("/")
def index():
    """
    Render the index page
    """
    if session.get("user", None):
        return redirect(url_for("configure"))
    response = make_response(render_template("index.html"))
    response.headers["Cache-Control"] = (
        "private, max-age=3600, stale-while-revalidate=600"
    )
    return response


@app.route("/configure", methods=["GET", "POST"])
@app.route("/<user_id>/configure")
def configure(user_id: str = ""):
    """
    Render the configure page
    :param user_id: The user's MyAnimeList ID (ignored, as this is sent by Stremio when redirecting to the configure
    page)
    """
    if not (user_session := session.get("user")):
        return redirect(url_for("index"))

    if request.method == "GET":
        if not (user := get_user(user_session["uid"])):
            flash("User not found.", "danger")
            return redirect(url_for("index"))

        response = make_response(
            render_template(
                "configure.html", user=user, sort_options=config.SORT_OPTIONS
            )
        )
        response.headers["Cache-Control"] = (
            "private, max-age=3600, stale-while-revalidate=600"
        )
        return response

    if not (user := get_user(user_session["uid"])):
        flash("User not found.", "danger")
        return redirect(url_for("index"))

    user |= __handle_addon_options(request.form)
    if not store_user(user):
        flash("Failed to update user configurations.", "danger")
        return redirect(url_for("index"))

    user_id = user["uid"]
    uri = f"{Config.REDIRECT_URL}/{user_id}/manifest.json"
    manifest_url = f"{Config.PROTOCOL}://{uri}"
    manifest_magnet = f"stremio://{uri}"

    flash("Addon options configured.", "success")
    response = make_response(
        render_template(
            "configure.html",
            user=user,
            sort_options=config.SORT_OPTIONS,
            manifest_url=manifest_url,
            manifest_magnet=manifest_magnet,
        )
    )
    response.headers["Cache-Control"] = (
        "private, max-age=3600, stale-while-revalidate=600"
    )
    return response


def __handle_addon_options(addon_config_options):
    """
    Handle addon configuration parameters that are provided by the user through the configuration page
    """
    options = {}
    if addon_config_options.get("sort_watchlist") in config.SORT_OPTIONS.values():
        options["sort_watchlist"] = addon_config_options.get("sort_watchlist")
    else:
        options["sort_watchlist"] = config.DEFAULT_SORT_OPTION

    if addon_config_options.get("fetch_streams", "") == "true":
        options["fetch_streams"] = True
    else:
        options["fetch_streams"] = False

    if addon_config_options.get("track_unlisted_anime", "") == "true":
        options["track_unlisted_anime"] = True
    else:
        options["track_unlisted_anime"] = False
    return options


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
