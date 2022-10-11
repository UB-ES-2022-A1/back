from sqlalchemy.orm import relationship
from database import db
from entities.user import User


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.Text, db.ForeignKey(User.__tablename__ + '.email'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)

    user = relationship(User, backref="services", cascade="all")

    #TODO Añadir campos como foto, fecha, ubicación.