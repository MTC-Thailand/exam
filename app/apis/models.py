from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app import db
import secrets
import string


class ApiClient(db.Model):
    __tablename__ = 'api_clients'
    client_id = db.Column('client_id', db.String(16), primary_key=True)
    active = db.Column('active', db.Boolean(), default=True)
    created_at = db.Column('created_at', db.DateTime(timezone=True), server_default=func.now())
    name = db.Column('name', db.String(), nullable=False)
    organization = db.Column('organization', db.String())
    _secret_hash = db.Column('secret_hash', db.String(255))

    def set_client_id(self):
        alphabets = string.digits
        self.client_id = ''.join([secrets.choice(alphabets) for i in range(10)])

    @property
    def client_secret(self):
        raise ValueError('Client secret is not accessible.')

    def set_secret(self):
        alphabets = string.ascii_letters + string.digits
        secret = ''.join([secrets.choice(alphabets) for i in range(32)])
        self._secret_hash = generate_password_hash(secret)
        print(f'The client secret is {secret}. Please keep it safe.')
