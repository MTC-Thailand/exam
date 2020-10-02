from flask import redirect, url_for
from flask_admin.contrib.sqla import ModelView
from app import create_app, admin
from app.main import mainbp as main_blueprint
from app.exambank import exambank as exambank_blueprint
from app.exambank.models import *

app = create_app()
app.register_blueprint(main_blueprint, url_prefix='/main')
app.register_blueprint(exambank_blueprint, url_prefix='/bank')

admin.add_views(ModelView(Subject, db.session, category='ExamBank'))
admin.add_views(ModelView(Bank, db.session, category='ExamBank'))
admin.add_views(ModelView(Category, db.session, category='ExamBank'))
admin.add_views(ModelView(SubCategory, db.session, category='ExamBank'))
admin.add_views(ModelView(Item, db.session, category='ExamBank'))
admin.add_views(ModelView(Choice, db.session, category='ExamBank'))


@app.route('/')
def index():
    return redirect(url_for('main.index'))