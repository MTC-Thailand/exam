from app import db


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


class BankCategory(db.Model):
    __tablename__ = 'bank_categories'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column('category_id', db.ForeignKey('categories.id'))
    bank_id = db.Column('bank_in', db.ForeignKey('banks.id'))
    category = db.relationship('Category', backref=db.backref('banks',
                                                              cascade='all, delete-orphan'))
    bank = db.relationship('Bank', backref=db.backref('categories',
                                                      cascade='all, delete-orphan'))


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    question = db.Column('question', db.Text(), nullable=False)
    desc = db.Column('desc', db.Text())
    ref = db.Column('ref', db.String())
    answer_id = db.Column('answer_id', db.ForeignKey('choices.id'))
    answer = db.relationship('Choice', uselist=False, foreign_keys=[answer_id])
    bank_id = db.Column('bank_id', db.ForeignKey('banks.id'))
    category_id = db.Column('category_id', db.ForeignKey('categories.id'))
    subcategory_id = db.Column('subcategory_id', db.ForeignKey('sub_categories.id'))
    bank = db.relationship('Bank', backref=db.backref('items'))
    category = db.relationship('Category', backref=db.backref('items'))
    subcategory = db.relationship('SubCategory', backref=db.backref('items'))
    created_at = db.Column('created_at', db.DateTime(timezone=True))

    def __str__(self):
        return self.question[:40]


class Choice(db.Model):
    __tablename__ = 'choices'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    desc = db.Column('desc', db.Text(), nullable=False)
    item_id = db.Column('item_id', db.ForeignKey('items.id'))
    item = db.relationship('Item', backref=db.backref('choices'), foreign_keys=[item_id])

    def __str__(self):
        return self.desc[:40]
