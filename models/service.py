from sqlalchemy.orm import backref

from database import db
from models.contracted_service import ContractedService
from models.search import term_frequency


class Service(db.Model):
    __tablename__ = "services"
    __table_args__ = (
        db.UniqueConstraint('user_email', 'title', 'description', 'price', name='unq_cons1'),
    )

    id = db.Column(db.Integer, primary_key=True)
    masterID = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric(scale=2), nullable=False, default=0)
    service_grade = db.Column(db.Float, default=0.0)
    number_of_reviews = db.Column(db.Integer, default = 0)

    contracts = db.relationship(ContractedService, backref="service", cascade="all, delete-orphan")
    created_at = db.Column(db.Date(), nullable=True)

    search_coincidences = db.relationship(term_frequency, backref="service", cascade="all, delete-orphan")
    begin = db.Column(db.Time, nullable=True)  # time at wich service can begin
    end = db.Column(db.Time, nullable=True)  # time at wich service will stop being available for the day
    cooldown = db.Column(db.Time, nullable=True)  # minimum time after service is given to rest
    requiresPlace = db.Column(db.Boolean, default=False)

    state = db.Column(db.Integer, nullable=False, default=0)  # 0 active, 1 paused, 2 not-active

    search_coincidences = db.relationship(term_frequency, backref="service", cascade="all, delete-orphan")
    child_services = db.relationship("Service", backref=backref("master_service", remote_side=[id]), post_update=True, cascade="all, delete-orphan")


    # TODO Añadir campos como foto, fecha, ubicación.
    def save_to_db(self):
        """
        This method saves the instance to the database
        """

        if self.created_at is None:
            self.created_at = db.func.current_date()

        db.session.add(self)
        db.session.commit()

        if self.masterID is None:
            self.masterID = self.id

        db.session.commit()
        term_frequency.put_service(self)

    def delete_from_db(self):
        """
        This method deletes the instance from the database
        """
        self.state = 2
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
        return cls.query.filter_by(state=0).count()
