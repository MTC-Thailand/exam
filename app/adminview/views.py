from flask import flash
from flask_login import current_user
from flask_admin.form import rules
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash
from wtforms import PasswordField


class UserAdminView(ModelView):
    column_searchable_list = ('username',)
    column_sortable_list = ('username',)
    column_exclude_list = ('password_hash',)
    form_excluded_columns = ('password_hash', 'questions')
    form_edit_rules = ('username',
                       'role',
                       rules.Header('Reset Password'),
                       'new_password', 'confirm'
                       )
    form_create_rules = ('username', 'role', 'password')

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField('Password')
        form_class.new_password = PasswordField('New Password')
        form_class.confirm = PasswordField('Confirm New Password')
        return form_class

    def create_model(self, form):
        model = self.model()
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()

    def update_model(self, form, model):
        form.populate_obj(model)
        if form.new_password.data:
            if form.new_password.data != form.confirm.data:
                flash('Password must match!')
            model.password_hash = generate_password_hash(form.new_password.data)
            self.session.add(model)
            self._on_model_change(form, model, False)
            self.session.commit()

