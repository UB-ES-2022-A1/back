from database import db
from models.user import User


class Transaction(db.Model):
    _tablename_ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(50), db.ForeignKey('users.email'))
    description = db.Column(db.String(90), nullable=False)
    number = db.Column(db.Integer, nullable=False, default=0)
    quantity = db.Column(db.Numeric(scale=2), nullable=False, default=0.0)
    wallet = db.Column(db.Numeric(scale=2), nullable=False, default=0.0)

    user = db.relationship(User, backref="transactions")

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