from database import db
from models.service import Service
from models.user import User


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        db.UniqueConstraint('reviewer_email', 'service_id', name='unq_cons2'),
    )

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    reviewer_email = db.Column(db.Text, db.ForeignKey('users.email'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    title = db.Column(db.Text, nullable=False, default='Untitled')
    text = db.Column(db.Text, nullable=False, default='Empty review text')
    stars = db.Column(db.Integer, nullable=False)

    reviewer = db.relationship(User, backref='reviews', cascade="all, delete")
    service = db.relationship("Service", backref='reviews', cascade="all, delete", foreign_keys=[service_id])


    # TODO Añadir campos como foto, fecha, ubicación.
    def save_to_db(self):
        """
        This method saves the instance to the database
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        This method deletes the instance from the database
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, instance_id):
        """
        Returns a service with the specified id
        :param instance_id: the service id
        :return: service with the corresponding id.
        """
        return cls.query.get(instance_id)

    @classmethod
    def get_all(cls):
        """
        Returns a list with all services
        :return: list with all services
        """
        return cls.query.all()

    @classmethod
    def get_count(cls):
        return cls.query.count()
