from wtforms_alchemy import model_form_factory, QuerySelectField
from flask_wtf import FlaskForm
from app import db
from app.exambank.models import ItemApproval

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class ApprovalForm(ModelForm):
    class Meta:
        model = ItemApproval
