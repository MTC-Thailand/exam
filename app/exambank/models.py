from app import db
from app.main.models import User


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
    bank = db.relationship('Bank', backref=db.backref('items', cascade='all, delete-orphan'))
    category = db.relationship('Category', backref=db.backref('items',
                                                              cascade='all, delete-orphan'))
    subcategory = db.relationship('SubCategory', backref=db.backref('items',
                                                                    cascade='all, delete-orphan'))
    subsubcategory = db.relationship('SubSubCategory', backref=db.backref('items',
                                                                          cascade='all, delete-orphan'))
    created_at = db.Column('created_at', db.DateTime(timezone=True))
    updated_at = db.Column('updated_at', db.DateTime(timezone=True))
    submitted_at = db.Column('submitted_at', db.DateTime(timezone=True))
    status = db.Column('status', db.String(), default='draft')
    user_id = db.Column('user_id', db.ForeignKey('users.id'))
    user = db.relationship(User, backref=db.backref('questions'))


    def __str__(self):
        return self.question[:40]

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

    def __str__(self):
        return self.desc[:40]


class NumChoice(db.Model):
    __tablename__ = 'number_choice'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    num = db.Column('num', db.Integer, default=5)
