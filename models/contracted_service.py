from sqlalchemy.orm import relationship
from database import db
from models.chat_room import ChatRoom


class ContractedService(db.Model):
    __tablename__ = "contracted_services"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    state = db.Column(db.Integer, nullable=False, default=0) # 0 creates, 1 accepted, 2 completed, 3 canceled.
    validate_c = db.Column(db.Integer, nullable=False, default=False)
    validate_s = db.Column(db.Integer, nullable=False, default=False)

    chat_room = db.relationship(ChatRoom, backref="contracted_service")

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
        self.state = 3
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
