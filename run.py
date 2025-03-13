import logging

from flask import Flask, render_template, session, url_for, redirect, request
from flask_compress import Compress

import config
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


@app.route('/configure')
@app.route('/<userID>/<parameters>/configure')
def configure(userID: str = None, parameters: str = None):
    """
    Render the configure page
    :param userID: The user's MyAnimeList ID (ignored, as this is sent by Stremio when redirecting to the configure
    page)
    :param parameters: A query string containing the user's addon configuration options (ignored, same as above)
    """
    if not (user := session.get('user', None)):
        return redirect(url_for('index'))

    user_id = user['uid']
    sort_watchlist = request.args.get('sort_watchlist', config.SORT_OPTIONS['Last Updated'])
    disable_streams = request.args.get('disable_streams', 'true')
    addon_options = f"sort={sort_watchlist}&disable_streams={disable_streams}"

    uri = f'{Config.REDIRECT_URL}/{user_id}/{addon_options}/manifest.json'
    manifest_url = f'{Config.PROTOCOL}://{uri}'
    manifest_magnet = f'stremio://{uri}'
    return render_template('configure.html', user=user,
                           sort_options=config.SORT_OPTIONS, manifest_url=manifest_url,
                           manifest_magnet=manifest_magnet)


@app.route('/favicon.ico')
def favicon():
    """
    Render the favicon for the app
    """
    return app.send_static_file('favicon.ico')


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=5000)
