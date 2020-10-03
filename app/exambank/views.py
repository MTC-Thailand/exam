from flask import render_template, jsonify, request
from . import exambank
from .models import *


@exambank.route('/')
def index():
    banks = Bank.query.all()
    return render_template('exambank/index.html', banks=banks)


@exambank.route('/<int:bank_id>/categories')
def list_categories(bank_id):
    bank = Bank.query.get(bank_id)
    num_choice = NumChoice.query.first()
    categories = []
    for cat in bank.categories:
        categories.append({
            'id': cat.id,
            'name': cat.name
        })
    return render_template('exambank/category.html',
                           bank=bank,
                           categories=categories,
                           choices=range(num_choice.num))


@exambank.route('/preview', methods=['POST'])
def preview():
    form = request.form
    category = Category.query.get(int(form['category_id']))
    subcategory = SubCategory.query.get(int(form['category_id']))
    subsubcategory = SubSubCategory.query.get(int(form['category_id']))
    return render_template('exambank/preview.html', form=form,
                           category=category,
                           subsubcategory=subsubcategory,
                           subcategory=subcategory)


@exambank.route('/api/categories/<int:category_id>/subcategories')
def get_subcategories(category_id):
    category = Category.query.get(category_id)
    subcategories = []
    for cat in category.subcategories:
        subcategories.append({
            'id': cat.id,
            'name': cat.name
        })

    return jsonify(subcategories)


@exambank.route('/api/subcategories/<int:subcategory_id>/subsubcategories')
def get_subsubcategories(subcategory_id):
    subcategory = SubCategory.query.get(subcategory_id)
    subsubcategories = []
    for cat in subcategory.subsubcategories:
        subsubcategories.append({
            'id': cat.id,
            'name': cat.name
        })

    return jsonify(subsubcategories)
