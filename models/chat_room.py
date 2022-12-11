from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import db
from models.chat_message import ChatMessage

class ChatRoom(db.Model):
    __tablename__ = "chat_room"

    id = db.Column(db.Integer, db.ForeignKey('contracted_services.id'), nullable=False, primary_key=True)
    seller_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    client_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    update = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    #https://stackoverflow.com/questions/28278328/how-to-use-values-like-default-and-onupdate-in-flask-sqlalchemy
    state = db.Column(db.Integer, nullable=False, default=0) # 0 = active, 1 = deactivated

    messages = db.relationship(ChatMessage, backref='chat_room')

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
        self.state = 1
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