from sqlalchemy.orm import relationship
from database import db


class Service(db.Model):
    __tablename__ = "services"
    __table_args__ = (
        db.UniqueConstraint('user_email', 'title', 'description', 'price', name='unq_cons1'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)


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
