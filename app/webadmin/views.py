import os

import arrow
import requests
import random
from sqlalchemy import or_
from flask_login import current_user
from werkzeug.utils import secure_filename

from . import webadmin
from app.exambank.models import *
from app import superuser
from app.exambank.views import get_categories
from flask import redirect, url_for, render_template, flash, request, jsonify, session
from .forms import ApprovalForm, EvaluationForm, SpecificationForm, GroupForm, RandomSetForm, SubjectForm
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
    if 'subject_id' not in request.args:
        subject_id = int(session.get('subject_id', -1))
    else:
        subject_id = request.args.get('subject_id', type=int)
        session['subject_id'] = subject_id
    specification = Specification.query.get(spec_id)
    subjects = Subject.query.all()
    return render_template('webadmin/spec_groups.html',
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


@webadmin.route('/items/<int:item_id>/groups/<int:group_id>/remove')
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
    if item.parent_id:
        return redirect(url_for('webadmin.preview', item_id=item.parent_id))
    else:
        return redirect(url_for('webadmin.preview', item_id=item.id))


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
def list_items_in_group(group_id):
    group = ItemGroup.query.get(group_id)
    return render_template('webadmin/group_questions.html', group=group)


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
        d['question'] = f"<a href={url_for('webadmin.preview_in_group', item_id=item.id, group_id=group_id)}>{item.question}</a>"
        if item.parent_id:
            d['question'] += '<span class="icon"><i class="fas fa-code-branch"></i></span>'
        data.append(d)

    # response
    return jsonify({'data': data,
                    'draw': request.args.get('draw', type=int),
                    'recordsTotal': group.items.count(),
                    'recordsFiltered': total_filtered
                    })


@webadmin.route('/api/banks/<int:bank_id>/questions/<status>')
def get_questions(bank_id, status):
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    with_groups = request.args.get('with_groups', None)
    subcategory_id = request.args.get('subcategory', type=int)
    included_rejected = request.args.get('rejected', -1, type=int)
    if status == 'submit':
        query = Item.query.filter_by(bank_id=bank_id) \
            .filter(or_(Item.status == 'submit', Item.parent_id is not None)).order_by(Item.id)
    elif status == 'draft':
        query = Item.query.filter_by(bank_id=bank_id, parent_id=None, status='draft').order_by(Item.id)
    elif status == 'accepted':
        query = Item.query.filter_by(bank_id=bank_id, peer_decision='Accepted').order_by(Item.id)
    if subcategory_id:
        query = query.filter_by(subcategory_id=subcategory_id)
    if with_groups == 'yes':
        query = query.filter(Item.groups.any())
    elif with_groups == 'no':
        query = query.filter(~Item.groups.any())

    if included_rejected == 0:
        query = query.filter(Item.peer_decision != 'Rejected')

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
        boxes = []
        for group in item.groups:
            box = f'<a href={url_for("webadmin.list_items_in_group", group_id=group.id)}><span class ="icon"><i class ="fas fa-box-open has-text-info"></i></span><span><small>{group.name[:10]}</small></span></a>'
            boxes.append(box)

        data.append({
            'id': item.id,
            'question': question,
            'bankId': item.bank.id,
            'bank': item.bank.name,
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


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/randomize', methods=['GET', 'POST'])
@superuser
def randomize(spec_id, set_id):
    spec = Specification.query.get(spec_id)
    for group in spec.groups.all():
        if group.num_sample_items and group.items.all():
            for item in random.choices(group.items.all(), k=group.num_sample_items):
                s = RandomItemSet(set_id=set_id, group_id=group.id, item_id=item.id)
                db.session.add(s)
        db.session.commit()
    return redirect(url_for('webadmin.random_index', spec_id=spec_id))


@webadmin.route('/specs/<int:spec_id>/random_set/<int:set_id>/groups/<int:group_id>/randomize', methods=['GET', 'POST'])
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
            db.session.add(s)
    else:
        removed_item = group.sample_items.filter_by(item_id=item_id).filter_by(set_id=set_id).first()
        db.session.delete(removed_item)
        db.session.commit()
        random_ids = set([item_set.item.id for item_set in group.sample_items.filter_by(set_id=set_id)])
        while len(random_ids) < group.num_sample_items:
            for item in random.choices(group.items.all(), k=1):
                random_ids.add(item.id)
            print('Duplication alert! Re-randomizing..')
        s = RandomItemSet(set_id=set_id, group_id=group.id, item_id=item.id)
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
                else:
                    item.figure.url = file_drive['id']
                    item.figure.filename = filename
                    item.desc = form.get('figdesc')
                    item.ref = form.get('figref')
                db.session.add(fig)
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
