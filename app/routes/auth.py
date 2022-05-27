from flask import Blueprint, request, render_template
from werkzeug.utils import redirect

from app.routes import mal_client
from config import Config

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/authorization', methods=["GET", "POST"])
def authorize_user():
    return redirect(mal_client.get_auth())


@auth_blueprint.route('/callback')
def redirect_url():
    code = request.args.get('code')
    mal_client.get_token(code)

    # TODO: Return as https on live server
    manifest_url = f"http://{Config.HOST}:{Config.PORT}/{mal_client.access_tkn}/manifest.json"
    manifest_magnet = f'stremio://{Config.HOST}:{Config.PORT}/{mal_client.access_tkn}/manifest.json'
    return render_template('index.html', manifest_url=manifest_url, manifest_magnet=manifest_magnet)
