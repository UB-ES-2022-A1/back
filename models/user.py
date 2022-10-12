from database import db
from models.service import Service


class User(db.Model):
    __tablename__ = "users"

    # Campos obligatory
    email = db.Column(db.Text, primary_key=True)
    pwd = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)

    # Campos opcionales
    phone = db.Column(db.Integer, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)

    services = db.relationship(Service, backref="user", cascade="all, delete-orphan")

    # Todo falta foto, gender (enum)
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, instance_id):
        return cls.query.get(instance_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()

