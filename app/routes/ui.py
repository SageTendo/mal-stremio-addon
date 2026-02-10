from quart import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import config
from app.services.db import get_user, store_user
from config import Config

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
async def index():
    """
    Render the index page
    """
    if session.get("user", None):
        return redirect(url_for("ui.configure"))
    response = await make_response(await render_template("index.html"))
    response.headers["Cache-Control"] = (
        "private, max-age=3600, stale-while-revalidate=600"
    )
    return response


@ui_bp.route("/configure", methods=["GET", "POST"])
@ui_bp.route("/<user_id>/configure")
async def configure(user_id: str = ""):
    """
    Render the configure page
    :param user_id: The user's MyAnimeList ID (ignored, as this is sent by Stremio when redirecting to the configure
    page)
    """
    if not (user_session := session.get("user")):
        return redirect(url_for("ui.index"))

    if not (user := get_user(user_session["uid"])):
        await flash("User not found.", "danger")
        return redirect(url_for("ui.index"))

    user_id = user["uid"]
    uri = f"{Config.REDIRECT_URL}/{user_id}/manifest.json"
    manifest_url = f"{Config.PROTOCOL}://{uri}"
    manifest_magnet = f"stremio://{uri}"

    # Handle form submission
    if request.method == "POST":
        user |= __handle_addon_options(await request.form)
        if not store_user(user):
            await flash("Failed to update user configurations.", "danger")
            return redirect(url_for("ui.index"))

        await flash("Addon options configured.", "success")
        r = await make_response(
            await render_template(
                "configure.html",
                user=user,
                sort_options=config.SORT_OPTIONS,
                manifest_url=manifest_url,
                manifest_magnet=manifest_magnet,
            )
        )
        r.headers["Cache-Control"] = "private, max-age=3600, stale-while-revalidate=600"
        return r

    r = await make_response(
        await render_template(
            "configure.html",
            user=user,
            sort_options=config.SORT_OPTIONS,
            manifest_url=manifest_url,
            manifest_magnet=manifest_magnet,
        )
    )
    r.headers["Cache-Control"] = "private, max-age=3600, stale-while-revalidate=600"
    return r


def __handle_addon_options(addon_config_options):
    """
    Handle addon configuration parameters that are provided by the user through the configuration page
    """
    options = {}
    if addon_config_options.get("sort_watchlist") in config.SORT_OPTIONS.values():
        options["sort_watchlist"] = addon_config_options.get("sort_watchlist")
    else:
        options["sort_watchlist"] = config.DEFAULT_SORT_OPTION

    if addon_config_options.get("track_unlisted_anime", "") == "true":
        options["track_unlisted_anime"] = True
    else:
        options["track_unlisted_anime"] = False

    if addon_config_options.get("nsfw_enabled", "") == "true":
        options["nsfw_enabled"] = True
    else:
        options["nsfw_enabled"] = False

    options["catalogs"] = []
    if addon_config_options.get("include_plan_to_watch"):
        options["catalogs"].append("plan_to_watch")
    if addon_config_options.get("include_watching"):
        options["catalogs"].append("watching")
    if addon_config_options.get("include_completed"):
        options["catalogs"].append("completed")
    if addon_config_options.get("include_on_hold"):
        options["catalogs"].append("on_hold")
    if addon_config_options.get("include_dropped"):
        options["catalogs"].append("dropped")
    return options
