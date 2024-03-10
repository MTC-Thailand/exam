import csv
import os
from io import StringIO
from pprint import pprint

import arrow
import requests
from flask_wtf.csrf import generate_csrf
from sqlalchemy import or_
from flask_login import current_user
from werkzeug.utils import secure_filename

from . import webadmin
from app.exambank.models import *
from app import superuser
from app.exambank.views import get_categories
from flask import (redirect, url_for, render_template, flash, request,
                   jsonify, session, make_response)
from .forms import (ApprovalForm, EvaluationForm, SpecificationForm,
                    GroupForm, RandomSetForm, SubjectForm, ApiClientForm)
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive

from ..apis.models import ApiClient
from ..exambank.forms import ItemGroupNoteForm, ItemTagForm

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


@webadmin.route('/bank-groups')
@superuser
def list_bank_groups():
    banks = Bank.query.all()
    return render_template('webadmin/bank-groups.html',
                           banks=banks, Item=Item)


@webadmin.route('/banks/<int:bank_id>/questions')
@webadmin.route('/banks/<int:bank_id>/questions/<status>')
@superuser
def list_questions(bank_id, status=None):
    bank = Bank.query.get(bank_id)
    title = request.args.get('title', 'Not specified')
    with_groups = request.args.get('with_groups')
    subcategories = set([item.subcategory for item in bank.items])
    return render_template('webadmin/questions.html',
                           title=title,
                           with_groups=with_groups,
                           bank=bank,
                           subcategories=subcategories,
                           status=status)


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
        new_item.groups = item.groups

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
        group_id = request.args.get('group_id')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('webadmin.preview_in_group', item_id=new_item.id, group_id=group_id))
    return render_template('webadmin/item_edit.html',
                           categories=get_categories(item.bank),
                           choices=[c.id for c in item.choices],
                           item=item)


@webadmin.route('/questions/<int:item_id>/edit-inplace', methods=['GET', 'POST'])
@superuser
def edit_question_inplace(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        form = request.form
        item.question = form['question']
        item.desc = form['desc']
        item.ref = form['ref']
        item.updated_at = arrow.now(tz='Asia/Bangkok').datetime

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
                if not item.figure:
                    fig = Figure(url=file_drive['id'],
                                 filename=filename,
                                 desc=form.get('figdesc'),
                                 ref=form.get('figref'),
                                 item=item)
                    db.session.add(fig)
                else:
                    item.figure.url = file_drive['id']
                    item.figure.filename = filename
                    item.desc = form.get('figdesc')
                    item.ref = form.get('figref')
        for key in form:
            if key.startswith('choice'):
                choice_id = int(key.replace('choice_', ''))
                choice = Choice.query.get(choice_id)
                choice.desc = form[key]
                choice.answer = choice.answer
                db.session.add(choice)
        db.session.add(item)
        db.session.commit()
        flash('บันทึกการแก้ไขข้อสอบแล้ว', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        else:
            return redirect(url_for('webadmin.preview', item_id=item_id))
    return render_template('webadmin/item_edit_inplace.html',
                           categories=get_categories(item.bank),
                           choices=[c.id for c in item.choices],
                           item=item,
                           next=request.args.get('next'))


@webadmin.route('/questions/<int:item_id>/expire', methods=['POST'])
@superuser
def expire_question(item_id):
    item = Item.query.get(item_id)
    if item:
        item.expire_at = arrow.now('Asia/Bangkok').datetime
        item.groups = []
        db.session.add(item)
        db.session.commit()
        resp = make_response()
        resp.headers['HX-Redirect'] = request.args.get('next')
        return resp


@webadmin.route('/questions/<int:item_id>/delete')
@superuser
def delete_child_question(item_id):
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
    category_id = request.args.get('category_id', item.category_id, type=int)
    subcategory_id = request.args.get('subcategory_id', item.subcategory_id, type=int)
    subsubcategory_id = request.args.get('subsubcategory_id', item.subsubcategory_id, type=int)

    query = Item.query.filter_by(bank_id=item.bank_id, status=item.status)

    if category_id:
        query = query.filter_by(category_id=category_id)
    if subcategory_id:
        query = query.filter_by(subcategory_id=subcategory_id)
    if subsubcategory_id:
        query = query.filter_by(subsubcategory_id=subsubcategory_id)

    if item.status == 'submit':
        query = query.filter(Item.parent_id is not None)
    else:
        query = query.filter_by(parent_id=None)

    prev_item = query.order_by(Item.id.desc()).filter(Item.id < item_id).first()
    next_item = query.order_by(Item.id.asc()).filter(Item.id > item_id).first()

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
    if item.parent_id:
        item = Item.query.get(item.parent_id)
    return render_template('webadmin/preview.html',
                           item=item,
                           form=form,
                           category_id=category_id,
                           subcategory_id=subcategory_id,
                           subsubcategory_id=subsubcategory_id,
                           prev_item_id=prev_item.id if prev_item else None,
                           next_item_id=next_item.id if next_item else None)


@webadmin.route('/groups/<int:group_id>/questions/<int:item_id>/preview', methods=['GET', 'POST'])
@superuser
def preview_in_group(group_id, item_id):
    item = Item.query.get(item_id)
    group = ItemGroup.query.get(group_id)

    prev_item = group.items.order_by(Item.id.desc()).filter(Item.id < item_id).first()
    next_item = group.items.order_by(Item.id.asc()).filter(Item.id > item_id).first()

    return render_template('webadmin/preview_in_group.html',
                           item=item,
                           group_id=group_id,
                           group=group,
                           next=request.args.get('next'),
                           prev_item_id=prev_item.id if prev_item else None,
                           next_item_id=next_item.id if next_item else None)


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


@webadmin.route('/banks/<int:bank_id>/subcategories/<int:subcategory_id>/questions/<status>')
@superuser
def show_subcategory(bank_id, subcategory_id, status):
    subcategory = SubCategory.query.get(subcategory_id)
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/subcategory.html',
                           status=status,
                           subcategory=subcategory, bank=bank)


@webadmin.route('/banks/<int:bank_id>/subsubcategories/<int:subsubcategory_id>/questions/<status>')
@superuser
def show_subsubcategory(bank_id, subsubcategory_id, status):
    subsubcategory = SubSubCategory.query.get(subsubcategory_id)
    bank = Bank.query.get(bank_id)
    return render_template('webadmin/subsubcategory.html',
                           status=status,
                           subsubcategory=subsubcategory, bank=bank)


@webadmin.route('/questions/<int:item_id>/peer_evaluate', methods=['GET', 'POST', 'PATCH'])
@superuser
def peer_evaluate(item_id):
    form = EvaluationForm()
    item = Item.query.get(item_id)
    parent_id = request.args.get('parent_id')
    if request.method == 'PATCH':
        item.peer_decision = request.form.get('peer_decision')
        item.peer_evaluated_at = arrow.now('Asia/Bangkok').datetime
        item.groups = []
        db.session.add(item)
        db.session.commit()
        if request.headers.get('HX-Request') == 'true':
            resp = make_response()
            resp.headers['HX-Redirect'] = request.args.get('next')
            return resp
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
            return redirect(url_for('webadmin.preview', item_id=parent_id or item_id))
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
    if 'subject_id' not in request.args:
        subject_id = int(session.get('subject_id', -1))
    else:
        subject_id = request.args.get('subject_id', type=int)
        session['subject_id'] = subject_id
    specification = Specification.query.get(spec_id)
    subjects = Subject.query.all()
    if subject_id != -1:
        groups = specification.groups.filter_by(subject_id=subject_id).order_by(ItemGroup.name)
    else:
        groups = specification.groups.order_by(ItemGroup.subject_id, ItemGroup.name)

    total_num_sample_items = 0
    total_num_groups = 0
    for group in groups:
        total_num_sample_items += group.num_sample_items if group.num_sample_items else 0
        total_num_groups += 1

    return render_template('webadmin/spec_groups.html',
                           total_num_groups=total_num_groups,
                           total_num_sample_items=total_num_sample_items,
                           groups=groups,
                           spec=specification,
                           ItemGroup=ItemGroup,
                           subject_id=subject_id,
                           subjects=subjects)


@webadmin.route('/specification/<int:spec_id>/groups/number')
@superuser
def list_all_groups(spec_id):
    if 'subject_id' not in request.args:
        subject_id = int(session.get('subject_id', -1))
    else:
        subject_id = request.args.get('subject_id', type=int)
        session['subject_id'] = subject_id
    specification = Specification.query.get(spec_id)
    subjects = Subject.query.all()
    return render_template('webadmin/spec_groups_list.html',
                           spec=specification,
                           ItemGroup=ItemGroup,
                           subject_id=subject_id,
                           subjects=subjects)


@webadmin.route('/items/<int:item_id>/groups')
@superuser
def add_group_to_item(item_id):
    child = request.args.get('child', 'false')
    item = Item.query.get(item_id)
    specs = Specification.to_dict()
    return render_template('webadmin/add_group_item.html',
                           specs=specs, item=item, child=child)


@webadmin.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@superuser
def edit_group(group_id):
    group = ItemGroup.query.get(group_id)
    subject_id = int(session.get('subject_id', -1))
    form = GroupForm(obj=group)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(group)
            db.session.add(group)
            db.session.commit()
            return redirect(url_for('webadmin.list_groups', spec_id=group.spec_id, subject_id=subject_id))
    return render_template('webadmin/group_form_edit.html',
                           form=form,
                           spec_id=group.spec_id,
                           group_id=group.id)


@webadmin.route('/groups/<int:group_id>/remove')
@superuser
def remove_group(group_id):
    group = ItemGroup.query.get(group_id)
    spec_id = group.spec_id
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('webadmin.list_groups', spec_id=spec_id))


@webadmin.route('/items/<int:item_id>/groups/<int:group_id>')
@superuser
def add_group(item_id, group_id):
    group = ItemGroup.query.get(group_id)
    item = Item.query.get(item_id)
    item.groups.append(group)
    db.session.add(item)
    db.session.commit()
    if item.parent_id:
        return redirect(url_for('webadmin.preview', item_id=item.parent_id))
    else:
        return redirect(url_for('webadmin.preview', item_id=item.id))


@webadmin.route('/items/<int:item_id>/groups/<int:group_id>/remove', methods=['GET', 'DELETE'])
@superuser
def remove_group_from_item(item_id, group_id):
    group = ItemGroup.query.get(group_id)
    item = Item.query.get(item_id)
    if group in item.groups:
        item.groups.remove(group)
        db.session.add(item)
        db.session.commit()
        flash('นำข้อสอบออกจากกล่องเรียบร้อยแล้ว', 'success')
    else:
        flash('ไม่พบกล่อง กรุณาตรวจสอบ', 'danger')
    if request.headers.get('HX-Request', 'false') == 'true':
        resp = make_response()
        resp.headers['HX-Redirect'] = url_for('webadmin.preview', item_id=item.parent_id or item.id)
        return resp
    return redirect(url_for('webadmin.preview', item_id=item.parent_id or item.id))


@webadmin.route('/groups/<int:group_id>/questions/<int:item_id>/remove')
@superuser
def remove_item_from_group(item_id, group_id):
    group = ItemGroup.query.get(group_id)
    item = Item.query.get(item_id)
    if group in item.groups:
        item.groups.remove(group)
        db.session.add(item)
        db.session.commit()
        flash('นำข้อสอบออกจากกล่องเรียบร้อยแล้ว', 'success')
    else:
        flash('ไม่พบกล่อง กรุณาตรวจสอบ', 'danger')
    return redirect(url_for('webadmin.list_items_in_group', group_id=group_id))


@webadmin.route('/api/specs/<int:spec_id>/items/<int:item_id>')
@superuser
def get_groups(spec_id, item_id):
    groups = []
    item = Item.query.get(item_id)
    for gr in ItemGroup.query.filter_by(spec_id=spec_id,
                                        subject_id=item.bank.subject_id):
        if gr not in item.groups:
            groups.append({
                'id': gr.id,
                'name': gr.name
            })
    return jsonify(groups)


@webadmin.route('/groups/<int:group_id>/items')
@superuser
def list_items_in_group(group_id):
    group = ItemGroup.query.get(group_id)
    return render_template('webadmin/group_questions.html',
                           group=group,
                           next=request.args.get('next'))


@webadmin.route('/subjects/<int:subject_id>/groups', methods=['GET', 'PATCH'])
@superuser
def get_groups_from_spec(subject_id):
    spec_id = request.args.get('spec_id')
    item_id = request.args.get('item_id')
    item = Item.query.get(int(item_id))
    template = ''
    for group in ItemGroup.query.filter_by(spec_id=int(spec_id), subject_id=subject_id):
        template += f'''
        <div class="control">
        <label class="checkbox label">
            <input type="checkbox" name="groups" {'checked' if group in item.groups else ''} value={group.id}>
            {group.name} ({group.items.count()} ข้อ) 
        </label>
        <br/>
        </div>
        '''
    return template


@webadmin.route('/items/<int:item_id>/assign-group', methods=['GET', 'PATCH'])
@superuser
def assign_group_no_spec(item_id):
    item = Item.query.get(item_id)
    specs = Specification.query.all()
    if request.method == 'PATCH':
        group_ids = request.form.getlist('groups')
        print(group_ids)
        item.groups = []
        for _id in group_ids:
            g = ItemGroup.query.get(int(_id))
            item.groups.append(g)
        db.session.add(item)
        db.session.commit()
        flash('อัพเดตกล่องเรียบร้อย', 'success')
        resp = make_response()
        resp.headers['HX-Redirect'] = request.args.get('next')
        return resp
    return render_template('webadmin/modals/assign_group_no_spec.html',
                           specs=specs, item=item, next=request.args.get('next'))


@webadmin.route('/specs/<int:spec_id>/items/<int:item_id>/assign-group', methods=['GET', 'PATCH'])
@superuser
def assign_group(item_id, spec_id):
    item = Item.query.get(item_id)
    spec = Specification.query.get(spec_id)
    if request.method == 'PATCH':
        group_ids = request.form.getlist('group')
        item.groups = []
        for _id in group_ids:
            g = ItemGroup.query.get(int(_id))
            item.groups.append(g)
        db.session.add(item)
        db.session.commit()
        flash('อัพเดตกล่องเรียบร้อย', 'success')
        resp = make_response()
        resp.headers['HX-Redirect'] = request.args.get('next')
        return resp
    return render_template('webadmin/modals/assign_group.html', item=item, spec=spec, next=request.args.get('next'))


@webadmin.route('/groups/<int:group_id>/edit-note', methods=['GET', 'POST'])
@webadmin.route('/groups/<int:group_id>/notes/<int:group_note_id>', methods=['GET', 'POST'])
@superuser
def edit_group_note(group_id, group_note_id=None):
    if group_note_id:
        group_note = ItemGroupNote.query.get(group_note_id)
        form = ItemGroupNoteForm(obj=group_note)
    else:
        form = ItemGroupNoteForm()

    if request.method == 'POST':
        if group_note_id:
            form.populate_obj(group_note)
        else:
            group_note = ItemGroupNote()
            form.populate_obj(group_note)
            group_note.group_id = group_id
        group_note.created_at = arrow.now('Asia/Bangkok').datetime
        db.session.add(group_note)
        db.session.commit()
        flash('เพิ่มบันทึกสำหรับกล่องเรียบร้อยแล้ว', 'success')
        resp = make_response()
        resp.headers['HX-Redirect'] = url_for('webadmin.list_items_in_group', group_id=group_id)
        return resp
    else:
        print(form.errors)
    return render_template('webadmin/modals/group_note.html', form=form, group_id=group_id)


@webadmin.route('/api/specs/groups/<int:group_id>/questions', methods=['GET'])
@superuser
def get_items_in_group(group_id):
    group = ItemGroup.query.get(group_id)
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    search = request.args.get('search[value]')

    query = group.items

    total_filtered = query.count()

    # search filter
    if search:
        query = query.filter(Item.question.like(f'%{search}%'))
        total_filtered = query.count()

    # pagination
    query = query.order_by(Item.id).offset(start).limit(length)

    data = []
    for item in query:
        d = item.to_dict()
        d['question'] = f"<a href={url_for('webadmin.preview_in_group', item_id=item.id, group_id=group_id, next=request.args.get('next'))}>{item.question}</a>"
        if item.parent_id:
            d['question'] += '<span class="icon"><i class="fas fa-code-branch"></i></span>'

        template = '<span class="tags">'
        for tag in item.tags:
            template += f'''<span class="tag is-warning">{tag}</span>'''

        d['question'] += template
        d['question'] += f'''
        <a class="tag is-light is-warning" hx-get={url_for('webadmin.preview_group_item', item_id=item.id, group_id=group_id, next=request.args.get('next'))} hx-target="#item-preview-container" hx-swap="innerHTML">
            <span class="icon"><i class="fas fa-eye"></i></span>
            <span>quick view</span>
        </a>
        </span>
        '''

        data.append(d)

    # response
    return jsonify({'data': data,
                    'draw': request.args.get('draw', type=int),
                    'recordsTotal': group.items.count(),
                    'recordsFiltered': total_filtered
                    })


@webadmin.route('/items/<int:item_id>/preview', methods=['GET'])
@webadmin.route('/groups/<int:group_id>/items/<int:item_id>/preview', methods=['GET'])
@superuser
def preview_group_item(item_id, group_id=None):
    next = request.args.get('next')
    item = Item.query.get(item_id)
    return render_template('webadmin/modals/item_preview.html',
                           item=item, group_id=group_id, next=next)


@webadmin.route('/api/banks/<int:bank_id>/questions/<status>')
@superuser
def get_questions(bank_id, status):
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    search = request.args.get('search[value]')

    with_groups = request.args.get('with_groups', None)
    subcategory_id = request.args.get('subcategory', type=int)
    included_rejected = request.args.get('rejected', 0, type=int)
    if status == 'submit':
        query = Item.query.filter_by(bank_id=bank_id) \
            .filter(Item.status == 'submit').order_by(Item.id)
    elif status == 'draft':
        query = Item.query.filter_by(bank_id=bank_id, status='draft').order_by(Item.id)
    elif status == 'accepted':
        query = Item.query.filter_by(bank_id=bank_id, peer_decision='Accepted').order_by(Item.id)

    if subcategory_id:
        query = query.filter_by(subcategory_id=subcategory_id)

    if with_groups == 'yes':
        query = query.filter(Item.groups.any())
    elif with_groups == 'no':
        query = query.filter(~Item.groups.any())

    if included_rejected == 0:
        query = query.filter(or_(Item.peer_decision == None, Item.peer_decision != 'Rejected'))

    if search:
        query = query.join(Item.subcategory)
        query = query.filter(db.or_(
            Item.question.like(f'%{search}%'),
            SubCategory.name.like(f'%{search}%'),
        ))

    total_count = query.count()
    query = query.offset(start).limit(length)

    data = []
    for item in query:
        if item.subcategory:
            subcategory = f"<a href={url_for('webadmin.show_subcategory', subcategory_id=item.subcategory.id, bank_id=bank_id, status=status)}>{item.subcategory.name}</a>"
        else:
            subcategory = None
        if item.subsubcategory:
            subsubcategory = f"<a href={url_for('webadmin.show_subsubcategory', subsubcategory_id=item.subcategory.id, bank_id=bank_id, status=status)}>{item.subcategory.name}</a>"
        else:
            subsubcategory = None
        question = f"<a href={url_for('webadmin.preview', item_id=item.id)}>{item.question} <span class='tag is-info is-light'>ID: {item.id}</span></a>"
        question += f' <span class="tag">comments: {len(item.approvals)}</span>'
        if item.parent_id:
            question += '<span class="icon"><i class="fas fa-code-branch"></i></span>'
        for comment in item.approvals:
            if comment.user == current_user:
                if comment.status == 'เหมาะสม':
                    status = 'is-success'
                elif comment.status == 'ไม่เหมาะสม':
                    status = 'is-danger'
                else:
                    status = 'is-warning'
                question += f'<span class="tag {status}">your thought: {comment.status}</span>'
        question += f'''
        <a class="tag is-warning is-light" hx-get={url_for('webadmin.preview_group_item', item_id=item.id)} hx-target="#item-preview-container" hx-swap="innerHTML">
            <span class="icon"><i class="fas fa-eye"></i></span>
            <span>quick view</span>
        </a>
        '''
        boxes = []
        for group in item.groups:
            box = f'<a href={url_for("webadmin.list_items_in_group", group_id=group.id)}><span class="icon"><i class="fas fa-box-open has-text-info"></i></span><span><small>{group.name}</small></span></a>'
            boxes.append(box)

        data.append({
            'id': item.id,
            'question': question,
            'bankId': item.bank.id,
            'bank': item.bank.name,
            'status': '<span class="tag is-rounded">{}</span>'.format(item.status),
            'subjectId': item.bank.subject.id,
            'subject': item.bank.subject.name,
            'decision': item.peer_decision,
            'category': item.category.name if item.category else None,
            'subcategory': subcategory,
            'subsubcategory': subsubcategory,
            'submittedAt': item.submitted_at.isoformat() if item.submitted_at else None,
            'user': item.user.name,
            'groups': ''.join(boxes)
        })

    return jsonify({
        'data': data,
        'records': total_count,
        'recordsFiltered': total_count,
        'draw': request.args.get('draw', type=int)
    })


@webadmin.route('/specs/<int:spec_id>/random')
@superuser
def random_index(spec_id):
    random_sets = RandomSet.query.filter_by(spec_id=spec_id).all()
    return render_template('webadmin/random_index.html', spec_id=spec_id, random_sets=random_sets)


@webadmin.route('/specs/<int:spec_id>/random/create', methods=['GET', 'POST'])
@superuser
def random_create(spec_id):
    form = RandomSetForm()
    form.created_at.data = arrow.now(tz='Asia/Bangkok')
    if request.method == 'POST':
        if form.validate_on_submit():
            random_set = RandomSet()
            form.populate_obj(random_set)
            random_set.spec_id = spec_id
            random_set.creator = current_user
            random_set.created_at = random_set.created_at.datetime
            db.session.add(random_set)
            db.session.commit()
            flash('เพิ่มรอบการสุ่มแล้ว', 'success')
            return redirect(url_for('webadmin.random_index', spec_id=spec_id))
        flash('กรุณาตรวจสอบข้อมูล', 'danger')
    return render_template('webadmin/random_create_form.html', form=form)


@webadmin.route('/specs/<int:spec_id>/random/<int:random_set_id>/delete')
@superuser
def delete_random_set(spec_id, random_set_id):
    random_set = RandomSet.query.get(random_set_id)
    db.session.delete(random_set)
    db.session.commit()
    return redirect(url_for('webadmin.random_index', spec_id=spec_id))


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/randomize')
@superuser
def randomize(spec_id, set_id):
    spec = Specification.query.get(spec_id)
    for group in spec.groups.all():
        if group.num_sample_items and group.items.all():
            for item in random.choices(group.items.all(), k=group.num_sample_items):
                s = RandomItemSet(set_id=set_id, group_id=group.id, item_id=item.id)
                # randomize_choices method does not work here because item is not linked yet
                choices_order = [str(c.id) for c in item.choices]
                random.shuffle(choices_order)
                s.choices_order = ','.join(choices_order)
                db.session.add(s)
        db.session.commit()
    return redirect(url_for('webadmin.random_index', spec_id=spec_id))


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/randomize-choices')
@superuser
def randomize_choices(spec_id, set_id):
    random_set = RandomSet.query.get(set_id)
    for item_set in random_set.item_sets:
        item_set.randomize_choices()
        db.session.add(item_set)
    db.session.commit()
    return redirect(url_for('webadmin.export_to_html', spec_id=spec_id, random_set_id=set_id))


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/groups/<int:group_id>/randomize')
@superuser
def randomize_group(spec_id, set_id, group_id):
    subject_id = int(session.get('subject_id', -1))
    item_id = request.args.get('item_id', type=int)
    group = ItemGroup.query.get(group_id)
    if item_id is None:
        for item in group.sample_items.filter_by(set_id=set_id):
            db.session.delete(item)
        db.session.commit()
        for item in random.choices(group.items.all(), k=group.num_sample_items):
            s = RandomItemSet(set_id=set_id,
                              group_id=group.id,
                              item_id=item.id)
            choices_order = [str(c.id) for c in item.choices]
            random.shuffle(choices_order)
            s.choices_order = ','.join(choices_order)
            db.session.add(s)
    else:
        removed_item = group.sample_items.filter_by(item_id=item_id).filter_by(set_id=set_id).first()
        if removed_item is None:
            flash(f'Item with ID={item_id} has been moved.', 'warning')
            return redirect(url_for('webadmin.preview_random_items',
                                    subject_id=subject_id,
                                    spec_id=spec_id,
                                    group_id=group_id,
                                    random_set_id=set_id))

        db.session.delete(removed_item)
        db.session.commit()
        random_ids = set([item_set.item.id for item_set in group.sample_items.filter_by(set_id=set_id)])
        while len(random_ids) < group.num_sample_items:
            for item in random.choices(group.items.all(), k=1):
                random_ids.add(item.id)
            print('Duplication alert! Re-randomizing..')
        s = RandomItemSet(set_id=set_id, group_id=group.id, item_id=item.id)
        # randomize_choices method does not work here
        choices_order = [str(c.id) for c in item.choices]
        random.shuffle(choices_order)
        s.choices_order = ','.join(choices_order)
        db.session.add(s)
    db.session.commit()
    return redirect(url_for('webadmin.preview_random_items',
                            subject_id=subject_id,
                            spec_id=spec_id,
                            group_id=group_id,
                            random_set_id=set_id))


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/remove')
@superuser
def remove_random_set(spec_id, set_id):
    random_set = RandomSet.query.get(set_id)
    db.session.delete(random_set)
    db.session.commit()
    flash('ลบชุดสุ่มคำถามแล้ว', 'success')
    return redirect(url_for('webadmin.random_index', spec_id=spec_id))


@webadmin.route('/specification/<int:spec_id>/groups/random_set/<int:set_id>')
@superuser
def list_group_random_items(spec_id, set_id):
    if 'subject_id' not in request.args:
        subject_id = session.get('subject_id', -1)
    else:
        subject_id = request.args.get('subject_id', type=int)
        session['subject_id'] = subject_id
    specification = Specification.query.get(spec_id)
    subjects = Subject.query.all()
    random_set = RandomSet.query.get(set_id)
    return render_template('webadmin/group_random_items.html',
                           spec=specification,
                           random_set=random_set,
                           ItemGroup=ItemGroup,
                           subject_id=subject_id,
                           subjects=subjects)


@webadmin.route('/specification/<int:spec_id>/groups/<int:group_id>/random_set/<int:random_set_id>')
@superuser
def preview_random_items(spec_id, random_set_id, group_id):
    group = ItemGroup.query.get(group_id)
    return render_template('webadmin/random_items_preview.html',
                           group=group,
                           random_set_id=random_set_id,
                           spec_id=spec_id)


@webadmin.route('/specification/<int:spec_id>/random_set/<int:random_set_id>')
@superuser
def preview_random_item_set(spec_id, random_set_id):
    random_set = RandomSet.query.get(random_set_id)
    subject_id = int(session.get('subject_id', -1))
    subject = Subject.query.get(subject_id)
    return render_template('webadmin/random_item_set_preview.html',
                           RandomItemSet=RandomItemSet,
                           Item=Item,
                           Bank=Bank,
                           subject=subject,
                           subject_id=subject_id,
                           random_set=random_set,
                           spec_id=spec_id)


@webadmin.route('/specification/<int:spec_id>/random_set/<int:random_set_id>/export/csv')
@superuser
def export_choices_csv(spec_id, random_set_id):
    data = [['No.', 'ItemSetID', 'ItemID', '1', '2', '3', '4', '5', 'AnswerID']]
    random_set = RandomSet.query.get(random_set_id)
    for n, item_set in enumerate(random_set.item_sets, start=1):
        choices = item_set.choices_order.split(',')
        data.append([n, item_set.id, item_set.item.id] + choices + [choices[item_set.correct_answer_position]])
    si = StringIO()
    cw = csv.writer(si)
    cw.writerows(data)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@webadmin.route('/specification/<int:spec_id>/random_set/<int:random_set_id>/export/html')
@superuser
def export_to_html(spec_id, random_set_id):
    random_set = RandomSet.query.get(random_set_id)
    subject_id = request.args.get('subject_id', -1, type=int)
    subject = Subject.query.get(subject_id)
    return render_template('webadmin/random_item_set_plain_html.html',
                           RandomItemSet=RandomItemSet,
                           Item=Item,
                           Bank=Bank,
                           subject=subject,
                           subject_id=subject_id,
                           random_set=random_set,
                           spec_id=spec_id)


@webadmin.route('/questions/<int:item_id>/preview-before-moving')
@superuser
def preview_before_moving(item_id):
    item = Item.query.get(item_id)
    form = SubjectForm()
    # category_id = request.args.get('category_id', item.category_id, type=int)
    # subcategory_id = request.args.get('subcategory_id', item.subcategory_id, type=int)
    # subsubcategory_id = request.args.get('subsubcategory_id', item.subsubcategory_id, type=int)

    return render_template('webadmin/preview_before_moving.html',
                           item=item,
                           form=form,
                           # category_id=category_id,
                           # subcategory_id=subcategory_id,
                           # subsubcategory_id=subsubcategory_id,
                           )


@webadmin.route('/questions/<int:item_id>/groups/<int:group_id>/randoms/<int:set_id>/edit', methods=['GET', 'POST'])
@superuser
def edit_random_question(item_id, set_id, group_id):
    subject_id = int(session.get('subject_id', -1))
    item = Item.query.get(item_id)
    random_set = RandomSet.query.get(set_id)
    if request.method == 'POST':
        form = request.form
        item.question = form['question']
        item.desc = form['desc']
        item.ref = form['ref']
        item.updated_at = arrow.now(tz='Asia/Bangkok').datetime

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
                if not item.figure:
                    fig = Figure(url=file_drive['id'],
                                 filename=filename,
                                 desc=form.get('figdesc'),
                                 ref=form.get('figref'),
                                 item=item)
                    db.session.add(fig)
                else:
                    item.figure.url = file_drive['id']
                    item.figure.filename = filename
                    item.desc = form.get('figdesc')
                    item.ref = form.get('figref')
        for key in form:
            if key.startswith('choice'):
                choice_id = int(key.replace('choice_', ''))
                choice = Choice.query.get(choice_id)
                choice.desc = form[key]
                choice.answer = choice.answer
                db.session.add(choice)
        db.session.add(item)
        db.session.commit()
        flash('บันทึกการแก้ไขข้อสอบแล้ว', 'success')
        return redirect(request.args.get('next') or url_for('webadmin.preview_random_items',
                                                            random_set_id=random_set.id,
                                                            spec_id=random_set.spec_id,
                                                            group_id=group_id,
                                                            subject_id=subject_id,
                                                            ))
    return render_template('webadmin/random_item_edit.html',
                           random_set_id=random_set.id,
                           spec_id=random_set.spec_id,
                           group_id=group_id,
                           subject_id=subject_id,
                           categories=get_categories(item.bank),
                           choices=[c.id for c in item.choices],
                           item=item)


@webadmin.route('/groups/<int:group_id>/clone', methods=['GET', 'POST'])
@superuser
def clone_group(group_id):
    group = ItemGroup.query.get(group_id)
    subject_id = int(session.get('subject_id', -1))
    new_group = ItemGroup()
    new_group.name = group.name + ' (copy)'
    new_group.num_sample_items = group.num_sample_items
    new_group.subject = group.subject
    new_group.is_active = group.is_active
    new_group.desc = group.desc
    form = GroupForm(obj=new_group)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(new_group)
            new_group.user = current_user
            new_group.items = group.items
            new_group.created_at = arrow.now(tz='Asia/Bangkok').datetime
            db.session.add(new_group)
            db.session.commit()
            flash('คัดลอกกล่องใหม่เรียบร้อยแล้ว', 'success')
            return redirect(url_for('webadmin.list_groups', spec_id=new_group.spec_id, subject_id=subject_id))
    return render_template('webadmin/group_form_edit.html',
                           form=form,
                           spec_id=group.spec_id,
                           group_id=group.id)


@webadmin.route('/web-services')
def client_index():
    return render_template('webadmin/apis/index.html')


@webadmin.route('/web-services/client/new', methods=['GET', 'POST'])
def add_client():
    form = ApiClientForm()
    if form.validate_on_submit():
        new_client = ApiClient()
        form.populate_obj(new_client)
        new_client.set_client_id()
        client_secret = new_client.set_secret()
        db.session.add(new_client)
        db.session.commit()
        flash('New client has been created.', 'success')
        return render_template('webadmin/apis/new_client_info.html',
                               client=new_client, client_secret=client_secret)
    return render_template('webadmin/apis/clien_form.html', form=form)


@webadmin.route('/specs/<int:spec_id>/testdrive', methods=['GET', 'POST'])
@superuser
def new_testdrive(spec_id):
    spec = Specification.query.get(spec_id)
    random_set = RandomSetTestDrive()
    random_set.spec_id = spec_id
    random_set.creator = current_user
    random_set.created_at = arrow.now(tz='Asia/Bangkok').datetime
    item_orders = []
    for group in spec.groups.all():
        if group.num_sample_items and group.items.all():
            for item in random.choices(group.items.all(), k=group.num_sample_items):
                s = RandomItemSetTestDrive(set=random_set, group_id=group.id, item_id=item.id)
                # randomize_choices method does not work here because item is not linked yet
                choices_order = [str(c.id) for c in item.choices]
                random.shuffle(choices_order)
                s.choices_order = ','.join(choices_order)
                db.session.add(s)
                item_orders.append(s)
    random.shuffle(item_orders)
    db.session.add(random_set)
    db.session.commit()
    random_set.item_orders = ','.join([str(i.id) for i in item_orders])
    db.session.add(random_set)
    db.session.commit()
    return render_template('webadmin/testdrive.html', random_set=random_set, item_set=item_orders[0])


@webadmin.route('/htmx/testdrive/random_set/<int:random_set_id>/item/<int:item_set_id>', methods=['GET', 'POST'])
@superuser
def new_testdrive_item(random_set_id, item_set_id):
    item_set = RandomItemSetTestDrive.query.get(item_set_id)
    random_set = RandomSetTestDrive.query.get(random_set_id)
    curr_pos, prev_item, next_item = random_set.get_item_set_positions(item_set)
    if next_item:
        next_item_url = url_for('webadmin.new_testdrive_item', random_set_id=random_set_id, item_set_id=next_item.id)
    else:
        next_item_url = url_for('webadmin.new_testdrive_item', random_set_id=random_set_id, item_set_id=item_set.id)
    if prev_item:
        prev_item_url = url_for('webadmin.new_testdrive_item', random_set_id=random_set_id, item_set_id=prev_item.id)
    else:
        prev_item_url = url_for('webadmin.new_testdrive_item', random_set_id=random_set_id, item_set_id=item_set.id)
    choices = '<table class="table is-hoverable">'
    if request.method == 'POST':
        answer_id = request.args.get('answer_id', int)
        if item_set.answer:
            item_set.answer.answer_id = answer_id
            item_set.answer.updated_at = arrow.now(tz='Asia/Bangkok').datetime
            item_set.answer.creator = current_user
        else:
            answer = RandomItemSetTestDriveAnswer(answer_id=answer_id)
            item_set.answer = answer
            item_set.answer.updated_at = arrow.now(tz='Asia/Bangkok').datetime
            item_set.answer.creator = current_user
        db.session.add(item_set)
        db.session.commit()

    for n, ch in enumerate(item_set.ordered_choices, start=1):
        url = url_for('webadmin.new_testdrive_item',
                      random_set_id=random_set_id,
                      item_set_id=item_set_id,
                      answer_id=ch.id)
        if item_set.answer and ch == item_set.answer.answer:
            choices += f'<tr hx-indicator="#indicator" hx-target="#item" hx-swap="innerHTML" hx-trigger="click" hx-post="{url}" class="is-selected"><td>{n}</td><td>{ch.desc}</td></tr>'
        else:
            choices += f'<tr hx-indicator="#indicator" hx-target="#item" hx-swap="innerHTML" hx-trigger="click" hx-post="{url}"><td>{n}</td><td>{ch.desc}</td></tr>'
    choices += '</table>'

    submit_url = url_for('webadmin.submit_testdrive', random_set_id=random_set.id)

    image = ''
    if item_set.item.figure:
        image += '''
            <p class="label">ภาพประกอบ</p>
            <div class="notification is-white">
                <img src="https://drive.google.com/uc?id={{ item_set.item.figure.url }}" width="700">
                <p class="label">คำอธิบายภาพ</p>
                <p>{{ item_set.item.figure.desc }}</p>
                <p class="label">ที่มาของภาพ</p>
                <p>{{ item_set.item.figure.ref }}</p>
            </div>
        '''

    resp = f'''
    <div class="content">
        <h1 class="title is-size-5 has-text-centered">ข้อ {curr_pos + 1}</h1>
        <div class="notification">{item_set.item.question}</div>
        {image}
        <h4>ตัวเลือก</h4>
        {choices}
        <div class="buttons is-centered">
            <button class="button" hx-indicator="#indicator" {"disabled" if not prev_item else ""} hx-get="{prev_item_url}" hx-target="#item" hx-swap="innerHTML">
                <span class="icon">
                    <i class="fas fa-chevron-left"></i>
                </span>
            </button>
            <button class="button" hx-indicator="#indicator" {"disabled" if not next_item else ""} hx-get="{next_item_url}" hx-target="#item" hx-swap="innerHTML">
                <span class="icon">
                    <i class="fas fa-chevron-right"></i>
                </span>
            </button>
            <a class="button is-primary" href="{submit_url}">
                Submit
            </a>
        </div>
    </div>
    '''
    return resp


@webadmin.route('/testdrive/random_set/<int:random_set_id>/submit')
@superuser
def submit_testdrive(random_set_id):
    random_set = RandomSetTestDrive.query.get(random_set_id)
    random_set.submitted_at = arrow.now(tz='Asia/Bangkok').datetime
    db.session.add(random_set)
    db.session.commit()
    return redirect(url_for('webadmin.testdrive_index', spec_id=random_set.spec_id))


@webadmin.route('/testdrive/spec/<int:spec_id>')
@superuser
def testdrive_index(spec_id):
    random_sets = RandomSetTestDrive.query.filter_by(creator=current_user, spec_id=spec_id)
    return render_template('webadmin/testdrive_index.html', random_sets=random_sets, spec_id=spec_id)


@webadmin.route('/items/<int:item_id>/tags', methods=['GET', 'POST'])
@webadmin.route('/items/<int:item_id>/tags/<int:tag_id>', methods=['DELETE'])
@superuser
def edit_tag(item_id, tag_id=None):
    if item_id:
        item = Item.query.get(item_id)

    form = ItemTagForm()
    form.tag.choices = [(tag.tag, tag.tag) for tag in Tag.query.all()]

    if request.method == 'GET':
        return render_template('webadmin/modals/tag_form.html', form=form, item_id=item_id)

    if request.method == 'DELETE':
        tag = Tag.query.get(tag_id)
        item.tags.remove(tag)
        db.session.add(item)
        db.session.commit()

    if request.method == 'POST':
        for tag_name in form.tag.data:
            tag_ = Tag.query.filter_by(tag=tag_name).first()
            if tag_ is None:
                tag_ = Tag(tag=tag_name, creator=current_user)
            item.tags.append(tag_)
        db.session.add(item)
        db.session.commit()

    template = ''
    for tag in item.tags:
        template += f'''
        <div class="control">
            <span class="tags has-addons">
                <span class="tag is-warning">{tag}</span>
                <span class="tag is-delete is-dark"
                      hx-headers='{{"X-CSRF-Token": "{generate_csrf()}" }}'
                      hx-delete="{url_for('webadmin.edit_tag', tag_id=tag.id, item_id=item_id, _method='DELETE')}"
                      hx-confirm="ท่านต้องการลบแท็กนี้หรือไม่">
                </span>
            </span>
        </div>
        '''
    resp = make_response(template)
    resp.headers['HX-Trigger-After-Swap'] = 'closeModal'
    resp.headers['HX-Retarget'] = '#item-tags'
    return resp
