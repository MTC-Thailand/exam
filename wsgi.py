from flask import redirect, url_for, abort
from flask_admin.contrib.sqla import ModelView
from app import create_app, admin, login
from app.adminview.views import UserAdminView
from app.main import mainbp as main_blueprint
from app.exambank import exambank as exambank_blueprint
from app.webadmin import webadmin as webadmin_blueprint
from app.exambank.models import *
from app.main.models import User
from pytz import timezone

app = create_app()
app.register_blueprint(main_blueprint, url_prefix='/main')
app.register_blueprint(exambank_blueprint, url_prefix='/bank')
app.register_blueprint(webadmin_blueprint, url_prefix='/webadmin')

admin.add_views(ModelView(Subject, db.session, category='ExamBank'))
admin.add_views(ModelView(Bank, db.session, category='ExamBank'))
admin.add_views(ModelView(Category, db.session, category='ExamBank'))
admin.add_views(ModelView(SubCategory, db.session, category='ExamBank'))
admin.add_views(ModelView(SubSubCategory, db.session, category='ExamBank'))
admin.add_views(ModelView(Item, db.session, category='ExamBank'))
admin.add_views(ModelView(Choice, db.session, category='ExamBank'))
admin.add_views(ModelView(NumChoice, db.session, category='ExamBank'))

admin.add_views(UserAdminView(User, db.session, category='Main'))



@login.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if not user:
        abort(500)
    else:
        return user


@app.route('/')
def index():
    return redirect(url_for('main.index'))


@app.template_filter("localdatetime")
def local_datetime(dt):
    if dt is None:
        return ''
    bangkok = timezone('Asia/Bangkok')
    datetime_format = '%d/%m/%Y %H:%M'
    return dt.astimezone(bangkok).strftime(datetime_format)


