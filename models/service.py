from database import db
from models.search import term_frequency


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
    search_coincidences = db.relationship(term_frequency, backref="service", cascade="all, delete-orphan")
    #
    begin = db.Column(db.Time, nullable=True) # time at wich service can begin
    end = db.Column(db.Time, nullable=True) # time at wich service will stop being available for the day
    cooldown = db.Column(db.Time, nullable=True) # minimum time after service is given to rest
    requiresPlace = db.Column(db.Boolean, default=False)

    # TODO Añadir campos como foto, fecha, ubicación.
    def save_to_db(self):
        """
        This method saves the instance to the database
        """
        db.session.add(self)
        db.session.commit()
        term_frequency.put_service(self)

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
