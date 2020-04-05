import factory
from factory.faker import Faker
from api.models.event import User, Country, db
from api.app import create_app
from api.utils import hash_password

app = create_app()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session   # the SQLAlchemy session object

    name = Faker('name')
    email = factory.LazyAttribute(lambda obj: obj.name.split(" ")[0].lower() + "@gmail.com")
    password = hash_password('123')
    country = Country(name='Ghana', code='GH', calling_code='123')


with app.app_context():
    users = UserFactory.build_batch(5)
    db.session.add_all(users)
    db.session.commit()