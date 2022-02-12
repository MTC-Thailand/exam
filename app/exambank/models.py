from app import db
from app.main.models import User

assoc_group_items = db.Table('assoc_group_items',
                             db.Column('group_id', db.Integer, db.ForeignKey('item_groups.id')),
                             db.Column('item_id', db.Integer, db.ForeignKey('items.id'))
                             )


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False)

    def __str__(self):
        return self.name


class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    subject_id = db.Column('subject_id', db.ForeignKey('subjects.id'))
    name = db.Column('name', db.String(), nullable=False)
    subject = db.relationship('Subject', backref=db.backref('banks'))

    categories = db.relationship('Category', secondary='bank_categories')

    def __str__(self):
        return self.name

    @property
    def drafted_items(self):
        return [item for item in self.items
                if item.status == 'draft' and item.status != 'discarded'
                and item.parent_id is None]

    @property
    def submitted_items(self):
        return [item for item in self.items
                if (item.status == 'submit' and item.status != 'discarded')
                or item.parent_id is not None]

    @property
    def accepted_items(self):
        return self.items.filter_by(peer_decision='Accepted').all()

    @property
    def grouped_items(self):
        return self.items.filter(Item.groups.any()).all()

    @property
    def ungrouped_items(self):
        return self.items.filter(~Item.groups.any()).all()


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False)

    def __str__(self):
        return self.name


class SubCategory(db.Model):
    __tablename__ = 'sub_categories'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.Text(), nullable=False)
    category_id = db.Column('category_id', db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref=db.backref('subcategories'))
    ref_no = db.Column('ref_no', db.String(), nullable=False)

    def __str__(self):
        return self.name


class SubSubCategory(db.Model):
    __tablename__ = 'sub_sub_categories'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.Text(), nullable=False)
    subcategory_id = db.Column('category_id', db.ForeignKey('sub_categories.id'))
    subcategory = db.relationship('SubCategory', backref=db.backref('subsubcategories'))
    ref_no = db.Column('ref_no', db.String(), nullable=False)

    def __str__(self):
        return self.name


class BankCategory(db.Model):
    __tablename__ = 'bank_categories'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column('category_id', db.ForeignKey('categories.id'))
    bank_id = db.Column('bank_in', db.ForeignKey('banks.id'))
    category = db.relationship('Category', backref=db.backref('bank_categories',
                                                              cascade='all, delete-orphan'))
    bank = db.relationship('Bank', backref=db.backref('bank_categories',
                                                      cascade='all, delete-orphan'))


class Figure(db.Model):
    __tablename__ = 'figures'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    url = db.Column('url', db.String(), nullable=False)
    filename = db.Column('filename', db.String(), nullable=False)
    desc = db.Column('desc', db.Text())
    ref = db.Column('reference', db.Text())
    item_id = db.Column('item_id', db.ForeignKey('items.id'))
    item = db.relationship('Item', backref=db.backref('figure', uselist=False))


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    question = db.Column('question', db.Text(), nullable=False)
    desc = db.Column('desc', db.Text())
    ref = db.Column('ref', db.String())
    bank_id = db.Column('bank_id', db.ForeignKey('banks.id'))
    category_id = db.Column('category_id', db.ForeignKey('categories.id'))
    subcategory_id = db.Column('subcategory_id', db.ForeignKey('sub_categories.id'))
    subsubcategory_id = db.Column('subsubcategory_id', db.ForeignKey('sub_sub_categories.id'))
    bank = db.relationship('Bank', backref=db.backref('items', lazy='dynamic',
                                                      cascade='all, delete-orphan'))
    category = db.relationship('Category',
                               backref=db.backref('items', cascade='all, delete-orphan', lazy='dynamic'))
    subcategory = db.relationship('SubCategory',
                                  backref=db.backref('items', cascade='all, delete-orphan', lazy='dynamic'))
    subsubcategory = db.relationship('SubSubCategory',
                                     backref=db.backref('items', cascade='all, delete-orphan', lazy='dynamic'))
    created_at = db.Column('created_at', db.DateTime(timezone=True))
    updated_at = db.Column('updated_at', db.DateTime(timezone=True))
    submitted_at = db.Column('submitted_at', db.DateTime(timezone=True))
    status = db.Column('status', db.String(), default='draft')
    user_id = db.Column('user_id', db.ForeignKey('users.id'))
    user = db.relationship(User, backref=db.backref('questions'))
    parent_id = db.Column('parent_id', db.ForeignKey('items.id'))
    children = db.relationship('Item', backref=db.backref('parent',
                                                          remote_side=[id],
                                                          lazy='dynamic',
                                                          uselist=True))
    peer_evaluated_at = db.Column('approved_at', db.DateTime(timezone=True))
    peer_summary = db.Column('peer_summary', db.Text(), info={'label': 'Peer Summary'})
    peer_decision = db.Column('peer_decision', db.String(),
                              info={'label': 'Decision',
                                    'choices': [(c, c) for c in ['Accepted', 'Rejected']]})

    def __str__(self):
        return self.question[:40]

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'bankId': self.bank.id,
            'bank': self.bank.name,
            'subjectId': self.bank.subject.id,
            'subject': self.bank.subject.name,
            'decision': self.peer_decision
        }

    @property
    def answer(self):
        for choice in self.choices:
            if choice.answer:
                return choice


class Choice(db.Model):
    __tablename__ = 'choices'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    desc = db.Column('desc', db.Text(), nullable=False)
    item_id = db.Column('item_id', db.ForeignKey('items.id'))
    item = db.relationship('Item',
                           backref=db.backref('choices', cascade='all, delete-orphan'),
                           foreign_keys=[item_id])
    answer = db.Column('answer', db.Boolean(), default=False)
    parent_id = db.Column('parent_id', db.ForeignKey('choices.id'))
    children = db.relationship('Choice', backref=db.backref('parent',
                                                            lazy='dynamic',
                                                            remote_side=[id],
                                                            uselist=True))

    def __str__(self):
        return self.desc[:40]


class NumChoice(db.Model):
    __tablename__ = 'number_choice'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    num = db.Column('num', db.Integer, default=5)


class ItemApproval(db.Model):
    __tablename__ = 'item_approvals'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column('item_id', db.ForeignKey('items.id'))
    item = db.relationship(Item, backref=db.backref('approvals'))
    user_id = db.Column('user_id', db.ForeignKey('users.id'))
    user = db.relationship(User, backref=db.backref('approved_items'))
    comment = db.Column('comment', db.Text())
    approved_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(), info={'label': 'สถานะการรับรอง',
                                          'choices': [(c, c) for c in
                                                      ('ไม่เหมาะสม',
                                                       'รอพิจารณาเพิ่มเติม',
                                                       'เหมาะสม',
                                                       'เหมาะสมแต่ควรย้ายหมวด')]})


class Specification(db.Model):
    __tablename__ = 'specifications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column('user_id', db.ForeignKey('users.id'))
    user = db.relationship(User, backref=db.backref('specifications'))

    @staticmethod
    def to_dict():
        return [{'name': s.name, 'id': s.id} for s in Specification.query.all()]


class ItemGroup(db.Model):
    __tablename__ = 'item_groups'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False, info={'label': 'ชื่อกล่องข้อสอบ'})
    num_sample_items = db.Column('num_sample_items', db.Integer(), info={'label': 'จำนวนข้อในการสุ่ม'})
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column('user_id', db.ForeignKey('users.id'))
    user = db.relationship(User, backref=db.backref('item_groups'))
    subject_id = db.Column('subject_id', db.ForeignKey('subjects.id'))
    subject = db.relationship(Subject, backref=db.backref('item_groups'))
    is_active = db.Column('is_active', db.Boolean(), default=True)
    spec_id = db.Column('spec_id', db.ForeignKey('specifications.id'))
    spec = db.relationship(Specification,
                           backref=db.backref('groups', lazy='dynamic'))
    items = db.relationship(Item,
                            secondary=assoc_group_items,
                            lazy='dynamic',
                            backref=db.backref('groups', lazy='dynamic'))
    desc = db.Column('desc', db.Text(), info={'label': 'Description'})
