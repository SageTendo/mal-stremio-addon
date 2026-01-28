from app.app import App
from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.content_sync import content_sync_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta_bp
from app.routes.ui import ui_bp
from app.services.mal_service import MalService


def create_app() -> App:
    app_ = App(__name__, template_folder="../templates", static_folder="./static")
    app_.config.from_object("config.Config")
    app_.register_blueprint(auth_blueprint)
    app_.register_blueprint(manifest_blueprint)
    app_.register_blueprint(catalog_bp)
    app_.register_blueprint(meta_bp)
    app_.register_blueprint(content_sync_bp)
    app_.register_blueprint(ui_bp)

    app_.mal = MalService()
    return app_
