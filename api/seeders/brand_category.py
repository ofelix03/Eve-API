from api.app import app
from api.models.event import db, BrandCategory

categories = ['Energy', 'Mining', 'Industrial', 'Health', 'NGO', 'Agriculture', 'Governmental', 'Technology', 'Social Media']

category_objs = []
for categ in categories:
    category_objs.append(BrandCategory(name=categ))

with app.app_context():
    db.session.add_all(category_objs)
    db.session.commit()

