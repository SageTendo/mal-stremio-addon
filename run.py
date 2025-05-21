import logging

from flask import Flask, render_template, session, url_for, redirect, request, flash
from flask_compress import Compress
from waitress import serve

import config
from app.db.db import store_user
from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.content_sync import content_sync_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta_bp
from app.routes.stream import stream_bp
from config import Config

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(auth_blueprint)
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(meta_bp)
app.register_blueprint(content_sync_bp)
app.register_blueprint(stream_bp)

Compress(app)

logging.basicConfig(format='%(asctime)s %(message)s')


@app.route('/')
def index():
    """
    Render the index page
    """
    if session.get('user', None):
        return redirect(url_for('configure'))
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """
    Render the favicon for the app
    """
    return app.send_static_file('favicon.ico')


@app.route('/configure', methods=['GET', 'POST'])
@app.route('/<userID>/configure')
def configure(userID: str = None):
    """
    Render the configure page
    :param userID: The user's MyAnimeList ID (ignored, as this is sent by Stremio when redirecting to the configure
    page)
    """
    if not (user := session.get('user', None)):
        return redirect(url_for('index'))

    if request.method == 'POST':
        user |= __handle_addon_options(request.form)
        store_user(user)

        user_id = user['uid']
        uri = f'{Config.REDIRECT_URL}/{user_id}/manifest.json'
        manifest_url = f'{Config.PROTOCOL}://{uri}'
        manifest_magnet = f'stremio://{uri}'

        flash("Addon options configured.", "success")
        return render_template('configure.html', user=user,
                               sort_options=config.SORT_OPTIONS, manifest_url=manifest_url,
                               manifest_magnet=manifest_magnet)
    else:
        return render_template('configure.html', user=user,
                               sort_options=config.SORT_OPTIONS)


def __handle_addon_options(addon_config_options):
    options = {}
    if addon_config_options.get('sort_watchlist') in config.SORT_OPTIONS.values():
        options['sort_watchlist'] = addon_config_options.get('sort_watchlist')
    else:
        options['sort_watchlist'] = config.DEFAULT_SORT_OPTION

    if addon_config_options.get('fetch_streams', '') == 'true':
        options['fetch_streams'] = True
    else:
        options['fetch_streams'] = False
    return options


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
