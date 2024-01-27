from flask import Flask, render_template

from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.manifest import manifest_blueprint
from app.routes.meta import meta_bp

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(auth_blueprint)
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(meta_bp)


@app.route('/')
def index():
    """
    Render the index page
    """
    return render_template('index.html')


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=5000)
