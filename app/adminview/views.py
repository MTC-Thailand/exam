from flask import flash, redirect, url_for, render_template, request
from flask_admin import BaseView, expose
from flask_admin.form import rules
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash
from wtforms import PasswordField
import pandas as pd

from app import db
from app.main.models import User, Role


class UserAdminView(ModelView):
    column_searchable_list = ('username',)
    column_sortable_list = ('username',)
    column_exclude_list = ('password_hash',)
    form_excluded_columns = ('password_hash', 'questions')
    form_edit_rules = ('username',
                       'role', 'name', 'email',
                       rules.Header('Reset Password'),
                       'new_password', 'confirm'
                       )
    form_create_rules = ('username', 'role', 'password', 'confirm', 'name', 'email')

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField('Password')
        form_class.new_password = PasswordField('New Password')
        form_class.confirm = PasswordField('Confirm New Password')
        return form_class

    def create_model(self, form):
        model = self.model(username=form.username.data,
                           password=form.password.data,
                           role=form.role.data,
                           name=form.name.data,
                           email=form.email.data)
        if form.password.data:
            if form.password.data == form.confirm.data:
                model.password_hash = generate_password_hash(form.password.data)
            else:
                flash('Password must match!')
                return redirect(url_for('user.create_view', url=url_for('user.index_view')))
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
        return redirect(url_for('user.index_view'))

    def update_model(self, form, model):
        form.populate_obj(model)
        if form.new_password.data:
            if form.new_password.data != form.confirm.data:
                flash('Password must match!')
            model.password_hash = generate_password_hash(form.new_password.data)
        self.session.add(model)
        self._on_model_change(form, model, False)
        self.session.commit()
        return redirect(url_for("user.index_view"))


class UploadUserView(BaseView):
    @expose('/')
    def index(self):
        return self.render('adminview/upload_user.html')

    @expose('/upload', methods=['POST'])
    def upload(self):
        if request.method == 'POST':
            if 'file' in request.files:
                file = request.files['file']
                if file.filename == '':
                    flash('No file selected.')
                    return redirect(url_for('user_upload.index'))
                df = pd.read_excel(request.files['file'])
                for idx, row in df.iterrows():
                    user = User.query.filter_by(username=row['username']).first()
                    role = Role.query.filter_by(role=row['role']).first()
                    if not user:
                        user = User(username=row['username'],
                                    password=row['password'],
                                    role=role,
                                    name=row['university'])
                        db.session.add(user)
                db.session.commit()

                return redirect(url_for('user_upload.index'))
            flash('File not uploaded.')
        return redirect(url_for('user_upload.index'))