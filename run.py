from flask import Flask, render_template, request, session

from waitress import serve
from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta
from app.routes.stream import stream_bp
from config import Config

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(auth_blueprint)
app.register_blueprint(meta)
app.register_blueprint(stream_bp)


@app.route('/')
def index():
    """
    Render the index page
    """
    if session_id := request.cookies.get('session_id', None):
        if user_info := session.get(session_id, None):
            access_token = user_info['access_token']
            manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/{access_token}/manifest.json'
            manifest_magnet = f'stremio://{Config.REDIRECT_URL}/{access_token}/manifest.json'
            return render_template('index.html', logged_in=True, user_info=user_info, manifest_url=manifest_url,
                                   manifest_magnet=manifest_magnet)
    return render_template('index.html', logged_in=False)


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
