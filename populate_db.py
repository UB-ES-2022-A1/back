from models.user import User
from models.service import Service


def populate(db):
    db.create_all()

    user_emails = [u.email for u in User.get_all()]

    for i in range(1, 5):
        user = User(email="email" + str(i) + "@gmail.com", pwd=User.hash_password("password"), name="Name"+str(i))
        if not user.email in user_emails:
            user.save_to_db()
            for j in range(2, i // 2):
                serviceT = Service(title="title_" + str(i) + "_" + str(j), user=user, description="description",
                                   price=i + j)
                serviceT.save_to_db()

    db.session.commit()
    try:
        user_a = User(email="madmin@gmail.com", pwd=User.hash_password("password"), name="MaxAdm", access=9)
        user_a.save_to_db()
    except Exception as e:
        print(e)
        return


