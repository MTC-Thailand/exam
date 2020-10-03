from flask import render_template, jsonify, request, redirect, url_for, flash
from app import db
import arrow
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


@exambank.route('/<int:bank_id>/save', methods=['POST'])
def save(bank_id):
    bank = Bank.query.get(bank_id)
    form = request.form
    preview = request.args.get('preview', False)
    category = Category.query.get(int(form['category_id']))
    subcategory = SubCategory.query.get(int(form['subcategory_id']))
    if form.get('subsubcategory_id'):
        subsubcategory = SubSubCategory.query.get(int(form['subsubcategory_id']))
    else:
        subsubcategory = None
    item = Item(bank=bank,
                question=form['question'],
                desc=form['desc'],
                ref=form['ref'],
                category=category,
                subcategory=subcategory,
                subsubcategory=subsubcategory,
                created_at=arrow.now(tz='Asia/Bangkok').datetime,
                )
    for key in form:
        if key.startswith('choice'):
            choice = Choice(desc=form[key], item=item)
            db.session.add(choice)
            db.session.commit()
            if 'choice_{}'.format(form['answer_id']) == key:
                choice.answer = True
    db.session.add(item)
    db.session.commit()

    if preview:
        return redirect(url_for('exambank.preview', item_id=item.id))


@exambank.route('/<int:item_id>/preview', methods=['GET'])
def preview(item_id):
    item = Item.query.get(item_id)
    return render_template('exambank/preview.html', item=item)


@exambank.route('/<int:item_id>/submit')
def submit(item_id):
    item = Item.query.get(item_id)
    item.status = 'submit'
    db.session.add(item)
    db.session.commit()
    flash('บันทึกข้อสอบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('exambank.list_categories', bank_id=item.bank.id))


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
