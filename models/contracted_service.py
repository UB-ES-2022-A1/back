from sqlalchemy.orm import relationship
from database import db


class ContractedService(db.Model):
    __tablename__ = "contracted_services"
    __table_args__ = (
        db.UniqueConstraint('user_email', 'service_id', 'state', 'price', name='unq_cons2'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    state = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric(scale=2), nullable=False, default=0)

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
