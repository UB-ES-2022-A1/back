from models.user import User
from models.service import Service


def populate(db):
    db.create_all()

    for i in range(1, 10):

        user_email = "email" + str(i) + "@gmail.com"

        try:

            user = User(email=user_email, pwd=User.hash_password("password"), name="Name" + str(i), verified_email=True)
            user.save_to_db()

            for j in range(2, i // 2):
                serviceT = Service(title="title_" + str(i) + "_" + str(j), user=user, description="description",
                                   price=i + j)
                serviceT.save_to_db()

            if i == 7:
                serviceT = Service(title="I'm a programmer that makes programs",
                                   user=user, description="i can program your computer. I like #cheEse!!!",
                                   price=10)
                serviceT.save_to_db()

            if i == 8:
                serviceT = Service(title="I'm a programmer that makes programs",
                                   user=user, description="i can program your computer. I like computers.",
                                   price=100)
                serviceT.save_to_db()

            if i == 9:
                serviceT = Service(title="I'm a cheese maker that makes cheese",
                                   user=user, description="i can also eat your cheese. I like cheese.",
                                   price=50)
                serviceT.save_to_db()

        except:
            db.session.rollback()

    user_a = User(email="madmin@gmail.com", pwd=User.hash_password("password"), name="MaxAdm", access=9,
                  verified_email=True)

    try:
        user_a.save_to_db()
    except:
        db.session.rollback()
