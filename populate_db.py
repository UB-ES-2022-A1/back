from app import app
from database import db
from models.user import User
from models.service import Service
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"

with app.app_context():
    db.create_all()
    User.query.delete()
    Service.query.delete()

    for i in range(1,11):
        user = User(email="email"+str(i), pwd="password", name="name")
        user.save_to_db()
        for j in range (2,i//2):
            serviceT = Service(title="title_"+str(i)+"_"+str(j), user=user, description="description", price=i+j)
            serviceT.save_to_db()
    db.session.commit()
