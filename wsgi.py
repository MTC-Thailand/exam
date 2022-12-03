import random

from flask import redirect, url_for, abort
from flask_admin.contrib.sqla import ModelView
from app import create_app, admin, login
from app.adminview.views import UserAdminView, UploadUserView
from app.apis.views import SpecificationResource
from app.main import mainbp as main_blueprint
from app.exambank import exambank as exambank_blueprint
from app.webadmin import webadmin as webadmin_blueprint
from app.apis import api_bp as api_blueprint
from app.apis.models import *
from app.exambank.models import *
from app.main.models import User, Role
from pytz import timezone
from flask_restful import Api

app = create_app()
app.register_blueprint(main_blueprint, url_prefix='/main')
app.register_blueprint(exambank_blueprint, url_prefix='/bank')
app.register_blueprint(webadmin_blueprint, url_prefix='/webadmin')
app.register_blueprint(api_blueprint)

from app.apis import api_blueprint

api = Api(api_blueprint)
api.add_resource(SpecificationResource, '/specification')

app.register_blueprint(api_blueprint)


class BankView(ModelView):
    form_excluded_columns = ['bank_categories', 'items']


class SubjectView(ModelView):
    form_excluded_columns = ['item_groups']


class CategoryView(ModelView):
    form_excluded_columns = ['items']


admin.add_views(SubjectView(Subject, db.session, category='ExamBank'))
admin.add_views(BankView(Bank, db.session, category='ExamBank'))
admin.add_views(CategoryView(Category, db.session, category='ExamBank'))
admin.add_views(ModelView(SubCategory, db.session, category='ExamBank'))
admin.add_views(ModelView(SubSubCategory, db.session, category='ExamBank'))
admin.add_views(ModelView(Item, db.session, category='ExamBank'))
admin.add_views(ModelView(Choice, db.session, category='ExamBank'))
admin.add_views(ModelView(NumChoice, db.session, category='ExamBank'))

admin.add_views(ModelView(Specification, db.session, category='ExamBank'))

admin.add_views(UserAdminView(User, db.session, category='Main'))
admin.add_views(ModelView(Role, db.session, category='Main'))
admin.add_views(UploadUserView(name='User upload', endpoint='user_upload', category='Main'))


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


@app.template_filter('shuffle')
def shuffle_items(items):
    """Returns a shuffled copy of the items.
    """
    random.shuffle(items)
    return [item for item in items]
