from . import webadmin
from app.exambank.models import *
from app import superuser
from flask import redirect, url_for, render_template, flash


@webadmin.route('/banks')
@superuser
def list_banks():
    banks = Bank.query.all()
    return render_template('webadmin/banks.html', banks=banks)


@webadmin.route('/banks/<int:bank_id>/questions')
@superuser
def list_questions(bank_id):
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/questions.html', bank=bank)


@webadmin.route('/questions/<int:item_id>/preview')
@superuser
def preview(item_id):
    item = Item.query.get(item_id)
    return render_template('webadmin/preview.html', item=item)


@webadmin.route('/<int:item_id>/submit')
@superuser
def submit(item_id):
    item = Item.query.get(item_id)
    item.status = 'submit'
    db.session.add(item)
    db.session.commit()
    flash('บันทึกข้อสอบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('webadmin.list_questions', bank_id=item.bank.id))


@webadmin.route('/banks/<int:bank_id>/subcategories/<int:subcategory_id>/questions')
@superuser
def show_subcategory(bank_id, subcategory_id):
    subcategory = SubCategory.query.get(subcategory_id)
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/subcategory.html',
                           subcategory=subcategory, bank=bank)


@webadmin.route('/banks/<int:bank_id>/subsubcategories/<int:subsubcategory_id>/questions')
@superuser
def show_subsubcategory(bank_id, subsubcategory_id):
    subsubcategory = SubSubCategory.query.get(subsubcategory_id)
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/subsubcategory.html',
                           subsubcategory=subsubcategory, bank=bank)
