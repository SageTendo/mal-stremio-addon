import logging

from flask import Flask, render_template, session
from flask_compress import Compress
from flask_session import Session

from app.db.db import db
from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta_bp
from config import Config

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(auth_blueprint)
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(meta_bp)

app.config['SESSION_MONGODB'] = db
Session(app)
Compress(app)

logging.basicConfig(format='%(asctime)s %(message)s')


@app.route('/')
def index():
    """
    Render the index page
    """
    if user := session.get('user', None):
        user_id = user['id']
        manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/{user_id}/manifest.json'
        manifest_magnet = f'stremio://{Config.REDIRECT_URL}/{user_id}/manifest.json'
        return render_template('index.html', logged_in=True, user=user,
                               manifest_url=manifest_url, manifest_magnet=manifest_magnet)
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=5000)
