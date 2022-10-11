from database import db


class User(db.Model):
    __tablename__ = "users"

    # Campos obligatory
    email = db.Column(db.Text, primary_key=True)
    pwd = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)

    # Campos opcionales
    phone = db.Column(db.Integer, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Todo falta foto, gender (enum)



