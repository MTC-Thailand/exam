from flask_wtf import FlaskForm
from wtforms import FormField, FieldList
from wtforms_alchemy import model_form_factory
from app.exambank.models import Item, Figure, Choice

from app import db

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

class FigureForm(ModelForm):
    class Meta:
        model = Figure


class ChoiceForm(ModelForm):
    class Meta:
        model = Choice


class ItemForm(ModelForm):
    class Meta:
        model = Item

    figure = FormField('Figure', FigureForm, default=Figure)
    choices = FieldList(FormField(ChoiceForm, default=Choice), min_entries=4)