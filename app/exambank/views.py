from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
import arrow
from . import exambank
from .models import *


def get_categories(bank):
    categories = []
    for cat in bank.categories:
        categories.append({
            'id': cat.id,
            'name': cat.name
        })
    return categories


@exambank.route('/')
@login_required
def index():
    banks = Bank.query.all()
    return render_template('exambank/index.html', banks=banks)


@exambank.route('/<int:bank_id>/questions')
@login_required
def list_questions(bank_id):
    bank = Bank.query.get(bank_id)
    return render_template('exambank/questions.html', bank=bank)


@exambank.route('/<int:bank_id>/categories')
@login_required
def list_categories(bank_id):
    bank = Bank.query.get(bank_id)
    num_choice = NumChoice.query.first()
    return render_template('exambank/category.html',
                           bank=bank,
                           categories=get_categories(bank),
                           choices=list(range(num_choice.num)))


@exambank.route('/<int:bank_id>/save', methods=['POST'])
@login_required
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
                user=current_user
                )
    for key in form:
        if key.startswith('choice'):
            choice = Choice(desc=form[key], item=item)
            db.session.add(choice)
            db.session.commit()
            if key == 'choice_1':
                choice.answer = True
    db.session.add(item)
    db.session.commit()

    if preview:
        return redirect(url_for('exambank.preview', item_id=item.id))


@exambank.route('/<int:item_id>/preview', methods=['GET'])
@login_required
def preview(item_id):
    item = Item.query.get(item_id)
    return render_template('exambank/preview.html', item=item)


@exambank.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        form = request.form
        preview = request.args.get('preview', False)
        item.question = form['question']
        item.desc = form['desc']
        item.ref = form['ref']
        item.updated_at = arrow.now(tz='Asia/Bangkok').datetime
        for key in form:
            if key.startswith('choice'):
                choice_id = int(key.replace('choice_', ''))
                choice = Choice.query.get(choice_id)
                choice.desc = form[key]
                db.session.add(choice)
        db.session.add(item)
        db.session.commit()

        if preview:
            return redirect(url_for('exambank.preview', item_id=item.id))
        else:
            return redirect(url_for('exambank.list_questions', bank_id=item.bank.id))

    return render_template('exambank/edit_question.html',
                           categories=get_categories(item.bank),
                           choices=[c.id for c in item.choices],
                           item=item)


@exambank.route('/<int:item_id>/submit')
@login_required
def submit(item_id):
    item = Item.query.get(item_id)
    item.status = 'submit'
    db.session.add(item)
    db.session.commit()
    flash('บันทึกข้อสอบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('exambank.list_questions', bank_id=item.bank.id))


@exambank.route('/api/categories/<int:category_id>/subcategories')
@login_required
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
@login_required
def get_subsubcategories(subcategory_id):
    subcategory = SubCategory.query.get(subcategory_id)
    subsubcategories = []
    for cat in subcategory.subsubcategories:
        subsubcategories.append({
            'id': cat.id,
            'name': cat.name
        })

    return jsonify(subsubcategories)
