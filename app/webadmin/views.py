import os

import arrow
import requests
from flask_login import current_user
from werkzeug.utils import secure_filename

from . import webadmin
from app.exambank.models import *
from app import superuser
from app.exambank.views import get_categories
from flask import redirect, url_for, render_template, flash, request
from .forms import ApprovalForm, EvaluationForm, SpecificationForm, GroupForm
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
keyfile_dict = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()
scopes = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scopes)
drive = GoogleDrive(gauth)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}



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


@webadmin.route('/questions/<int:item_id>/edit', methods=['GET', 'POST'])
@superuser
def edit_question(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        new_item = Item(parent_id=item_id,
                        user=current_user,
                        category_id=item.category_id,
                        subcategory_id=item.subcategory_id,
                        subsubcategory_id=item.subsubcategory_id,
                        bank_id=item.bank_id)
        form = request.form
        new_item.question = form['question']
        new_item.desc = form['desc']
        new_item.ref = form['ref']
        new_item.updated_at = arrow.now(tz='Asia/Bangkok').datetime

        if 'figure' in request.files:
            upfile = request.files.get('figure')
            filename = secure_filename(upfile.filename)
            if filename:
                upfile.save(filename)
                file_drive = drive.CreateFile({'title': filename})
                file_drive.SetContentFile(filename)
                file_drive.Upload()
                permission = file_drive.InsertPermission({'type': 'anyone',
                                                          'value': 'anyone',
                                                          'role': 'reader'})
                fig = Figure(url=file_drive['id'],
                             filename=filename,
                             desc=form.get('figdesc'),
                             ref=form.get('figref'),
                             item=new_item)
                db.session.add(fig)
        for key in form:
            if key.startswith('choice'):
                choice_id = int(key.replace('choice_', ''))
                choice = Choice.query.get(choice_id)
                new_choice = Choice(parent_id=choice_id)
                new_choice.desc = form[key]
                new_choice.answer = choice.answer
                new_choice.item = new_item
                db.session.add(new_choice)
        new_item.created_at = arrow.now(tz='Asia/Bangkok').datetime
        db.session.add(new_item)
        db.session.commit()
        flash('บันทึกข้อสอบใหม่แล้ว', 'success')
        return redirect(url_for('webadmin.preview', item_id=item_id))
    return render_template('webadmin/item_edit.html',
                           categories=get_categories(item.bank),
                           choices=[c.id for c in item.choices],
                           item=item)


@webadmin.route('/questions/<int:item_id>/delete')
@superuser
def delete_question(item_id):
    item = Item.query.get(item_id)
    parent_id = item.parent_id
    db.session.delete(item)
    db.session.commit()
    flash('ลบคำถามเรียบร้อยแล้ว', 'success')
    return redirect(url_for('webadmin.preview', item_id=parent_id))


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


@webadmin.route('/questions/<int:item_id>/peer_evaluate', methods=['GET', 'POST'])
@superuser
def peer_evaluate(item_id):
    form = EvaluationForm()
    item = Item.query.get(item_id)
    parent_id = request.args.get('parent_id')
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(item)
            item.peer_evaluated_at = arrow.now(tz='Asia/Bangkok').datetime
            if not item.submitted_at:
                item.status = 'submit'
                item.submitted_at = arrow.now(tz='Asia/Bangkok').datetime
            db.session.add(item)
            db.session.commit()
            flash('Peer evaluation added.', 'success')
            if parent_id:
                return redirect(url_for('webadmin.preview', item_id=int(parent_id)))
            else:
                return redirect(url_for('webadmin.preview', item_id=item_id))
    return render_template('webadmin/peer_evaluation_form.html', form=form, item=item)


@webadmin.route('/banks/<int:bank_id>/questions/accepted')
@superuser
def list_accepted_questions(bank_id):
    bank = Bank.query.get(bank_id)
    subcategories = set([item.subcategory for item in bank.items])
    return render_template('webadmin/accepted_questions.html', bank=bank, subcategories=subcategories)


@webadmin.route('/specification')
@superuser
def specification():
    specifications = Specification.query.all()
    return render_template('webadmin/specification.html',
                           specifications=specifications)


@webadmin.route('/specification/new', methods=['GET', 'POST'])
@superuser
def add_specification():
    form = SpecificationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            spec = Specification()
            form.populate_obj(spec)
            spec.created_at = arrow.now(tz='Asia/Bangkok').datetime
            spec.user = current_user
            db.session.add(spec)
            db.session.commit()
            flash('New specification added.', 'success')
            return redirect(url_for('webadmin.specification'))
    return render_template('webadmin/specification_form.html', form=form)


@webadmin.route('/specification/<int:spec_id>/group/new', methods=['GET', 'POST'])
@superuser
def add_item_group(spec_id):
    form = GroupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            group = ItemGroup()
            form.populate_obj(group)
            group.created_at = arrow.now(tz='Asia/Bangkok').datetime
            group.user = current_user
            group.spec_id = spec_id
            db.session.add(group)
            db.session.commit()
            flash('New group has been added.', 'success')
            return redirect(url_for('webadmin.specification'))
        else:
            flash('Error', 'danger')
    return render_template('webadmin/group_form.html', form=form, spec_id=spec_id)


@webadmin.route('/specification/<int:spec_id>/groups')
@superuser
def list_groups(spec_id):
    specification = Specification.query.get(spec_id)
    return render_template('webadmin/spec_groups.html', spec=specification)
