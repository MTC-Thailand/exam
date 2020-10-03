from flask import render_template
from . import mainbp as main


@main.route('/')
def index():
    return render_template('main/index.html')