from sqlalchemy.orm import relationship

from database import db
from entities.user import User


class Service(db.Model):
    __tablename__ = "service"

    id = db.column(db.Integer, primary_key=True)
    user = relationship(User.__tablename__, backref="services", cascade="all", nullable=False)
    title = db.column(db.Text, nullable=False)
    description = db.column(db.Text, nullable=False)
