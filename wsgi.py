from flask import redirect, url_for
from app import create_app
from app.main import mainbp as main_blueprint

app = create_app()
app.register_blueprint(main_blueprint, url_prefix='/main')


@app.route('/')
def index():
    return redirect(url_for('main.index'))