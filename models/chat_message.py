from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import db


class ChatMessage(db.Model):
    __tablename__ = "chat_message"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'), nullable=False)
    text = db.Column(db.Text, nullable=False, default='Failed to store text message')
    time = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    #https://stackoverflow.com/questions/28278328/how-to-use-values-like-default-and-onupdate-in-flask-sqlalchemy
    state = db.Column(db.Integer, nullable=False, default=0) # 0 = active, 1 = deactivated

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