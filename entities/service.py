from sqlalchemy.orm import relationship
from database import db
from entities.user import User


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.Text, db.ForeignKey(User.__tablename__ + '.email'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)

    user = db.relationship(User, foreign_keys=[user_email], backref="services")

    # TODO Añadir campos como foto, fecha, ubicación.

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
