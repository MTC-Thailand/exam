import arrow
from flask_login import current_user

from . import webadmin
from app.exambank.models import *
from app import superuser
from flask import redirect, url_for, render_template, flash, request
from .forms import ApprovalForm


@webadmin.route('/banks')
@superuser
def list_banks():
    banks = Bank.query.all()
    return render_template('webadmin/banks.html', banks=banks)


@webadmin.route('/banks/<int:bank_id>/questions')
@superuser
def list_questions(bank_id):
    bank = Bank.query.get(bank_id)
    subcategories = set([item.subcategory for item in bank.items])
    return render_template('webadmin/questions.html', bank=bank, subcategories=subcategories)


@webadmin.route('/questions/<int:item_id>/preview', methods=['GET', 'POST'])
@superuser
def preview(item_id):
    form = ApprovalForm()
    item = Item.query.get(item_id)
    if request.method == 'POST':
        if form.validate_on_submit():
            new_approval = ItemApproval()
            form.populate_obj(new_approval)
            new_approval.user = current_user
            new_approval.item = item
            new_approval.approved_at = arrow.now(tz='Asia/Bangkok').datetime,
            db.session.add(new_approval)
            db.session.commit()
            flash('Your approval has been submitted.', 'success')
            if request.args.get('next'):
                return redirect(request.args.get('next'))
    return render_template('webadmin/preview.html', item=item, form=form)

@webadmin.route('/approvals/<int:approval_id>/delete')
@superuser
def delete_comment(approval_id):
    approval = ItemApproval.query.get(approval_id)
    if approval:
        item_id = approval.item.id
        db.session.delete(approval)
        db.session.commit()
        flash('You comment has been deleted.', 'success')
        return redirect(url_for('webadmin.preview', item_id=item_id))
    else:
        flash('The comment is not found.', 'warning')
        return redirect(request.referrer)


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
