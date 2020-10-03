from . import webadmin
from app.exambank.models import *
from flask import redirect, url_for, render_template, flash


@webadmin.route('/banks')
def list_banks():
    banks = Bank.query.all()
    return render_template('webadmin/banks.html', banks=banks)


@webadmin.route('/banks/<int:bank_id>/questions')
def list_questions(bank_id):
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/questions.html', bank=bank)


@webadmin.route('/questions/<int:item_id>/preview')
def preview(item_id):
    item = Item.query.get(item_id)
    return render_template('webadmin/preview.html', item=item)


@webadmin.route('/<int:item_id>/submit')
def submit(item_id):
    item = Item.query.get(item_id)
    item.status = 'submit'
    db.session.add(item)
    db.session.commit()
    flash('บันทึกข้อสอบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('webadmin.list_questions', bank_id=item.bank.id))