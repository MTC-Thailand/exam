from wtforms_alchemy import model_form_factory, QuerySelectField
from flask_wtf import FlaskForm
from app import db
from app.exambank.models import ItemApproval, Item

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class ApprovalForm(ModelForm):
    class Meta:
        model = ItemApproval


class EvaluationForm(ModelForm):
    class Meta:
        model = Item
        only = ['peer_summary', 'peer_decision']