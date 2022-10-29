from database import db
from models.search import SearchCoincidende


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
    search_coincidences = db.relationship(SearchCoincidende, backref="service", cascade="all, delete-orphan")



    # TODO Añadir campos como foto, fecha, ubicación.
    def save_to_db(self):
        """
        This method saves the instance to the database
        """
        db.session.add(self)
        db.session.commit()
        SearchCoincidende.put_service(self)

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
