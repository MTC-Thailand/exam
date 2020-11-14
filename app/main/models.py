from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column('username', db.String(), nullable=False, unique=True)
    password_hash = db.Column('password_hash', db.String(), nullable=True)

    @property
    def has_password(self):
        return self.password_hash != None

    @property
    def password(self):
        raise AttributeError('Password attribute is not accessible.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __str__(self):
        return self.username