from dotenv import load_dotenv
from flask import Flask, render_template

from app.routes.auth import auth_blueprint
from app.routes.catalog import catalog_bp
from app.routes.manifest import manifest_blueprint

load_dotenv()

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(manifest_blueprint)
app.register_blueprint(catalog_bp)
app.register_blueprint(auth_blueprint)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=9292)
